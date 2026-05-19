"""Cursor file parsers backed by Pillow."""

from __future__ import annotations

import struct
from collections import defaultdict
from io import BytesIO
from typing import Iterable

from PIL import Image

from ani2xcur.cursor_conversion.native_cursor.models import CursorFrame, CursorImage

CUR_MAGIC = b"\x00\x00\x02\x00"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
XCURSOR_MAGIC = b"Xcur"
XCURSOR_VERSION = 0x00010000
XCURSOR_IMAGE_TYPE = 0xFFFD0002

ICON_DIR = struct.Struct("<HHH")
ICON_DIR_ENTRY = struct.Struct("<BBBBHHII")
RIFF_HEADER = struct.Struct("<4sI4s")
CHUNK_HEADER = struct.Struct("<4sI")
ANIH_HEADER = struct.Struct("<IIIIIIIII")
UNSIGNED = struct.Struct("<I")
XCURSOR_FILE_HEADER = struct.Struct("<4sIII")
XCURSOR_TOC_CHUNK = struct.Struct("<III")
XCURSOR_IMAGE_HEADER = struct.Struct("<IIIIIIIII")

ANI_ICON_FLAG = 0x1


def parse_blob(blob: bytes) -> list[CursorFrame]:
    """Parse a Windows CUR/ANI or Linux Xcursor blob."""
    if blob.startswith(CUR_MAGIC):
        return parse_cur(blob)
    if _is_ani(blob):
        return parse_ani(blob)
    if blob.startswith(XCURSOR_MAGIC):
        return parse_xcursor(blob)
    raise ValueError("Unsupported cursor file format")


def parse_cur(blob: bytes) -> list[CursorFrame]:
    """Parse a Windows .cur file into one static cursor frame."""
    if len(blob) < ICON_DIR.size:
        raise ValueError("CUR file is too small")

    reserved, cursor_type, image_count = ICON_DIR.unpack_from(blob, 0)
    if reserved != 0 or cursor_type != 2:
        raise ValueError("Not a CUR file")
    if image_count <= 0:
        raise ValueError("CUR file does not contain images")

    entries_start = ICON_DIR.size
    entries_end = entries_start + image_count * ICON_DIR_ENTRY.size
    if len(blob) < entries_end:
        raise ValueError("CUR directory is truncated")

    images: list[CursorImage] = []
    offset = entries_start
    for _ in range(image_count):
        width_byte, height_byte, _, _, hotspot_x, hotspot_y, image_size, image_offset = ICON_DIR_ENTRY.unpack_from(blob, offset)
        offset += ICON_DIR_ENTRY.size

        if image_offset + image_size > len(blob):
            raise ValueError("CUR image payload is truncated")

        entry_width = 256 if width_byte == 0 else width_byte
        entry_height = 256 if height_byte == 0 else height_byte
        payload = blob[image_offset : image_offset + image_size]
        image = _decode_cur_payload(payload, entry_width, entry_height)
        images.append(
            CursorImage(
                image=image,
                hotspot=(hotspot_x, hotspot_y),
                nominal=image.width,
            )
        )

    return [CursorFrame(images=images)]


def parse_ani(blob: bytes) -> list[CursorFrame]:
    """Parse an icon-based Windows .ani file."""
    if not _is_ani(blob):
        raise ValueError("Not an ANI file")

    _, riff_size, _ = RIFF_HEADER.unpack_from(blob, 0)
    riff_end = min(len(blob), 8 + riff_size)
    offset = RIFF_HEADER.size

    frame_count = 0
    step_count = 0
    display_rate = 1
    flags = 0
    icon_frames: list[CursorFrame] = []
    order: list[int] | None = None
    delays: list[int] | None = None

    for name, size, payload_start, payload_end in _iter_chunks(blob, offset, riff_end):
        if name == b"anih":
            if size != ANIH_HEADER.size:
                raise ValueError(f"Unexpected anih header size {size}")
            header_size, frame_count, step_count, _, _, _, _, display_rate, flags = ANIH_HEADER.unpack_from(blob, payload_start)
            if header_size != ANIH_HEADER.size:
                raise ValueError(f"Unexpected size in anih header {header_size}")
            if not flags & ANI_ICON_FLAG:
                raise NotImplementedError("Raw BMP ANI frames are not supported")
        elif name == b"LIST" and blob[payload_start : payload_start + 4] == b"fram":
            for child_name, child_size, child_start, _ in _iter_chunks(blob, payload_start + 4, payload_end):
                if child_name != b"icon":
                    continue
                icon_frames.append(parse_cur(blob[child_start : child_start + child_size])[0])
        elif name == b"seq ":
            order = [value for (value,) in UNSIGNED.iter_unpack(blob[payload_start:payload_end])]
        elif name == b"rate":
            delays = [value for (value,) in UNSIGNED.iter_unpack(blob[payload_start:payload_end])]

    if not icon_frames:
        raise ValueError("ANI file does not contain icon frames")

    frame_count = frame_count or len(icon_frames)
    step_count = step_count or frame_count
    order = list(range(frame_count)) if order is None else order
    delays = [display_rate for _ in range(step_count)] if delays is None else delays

    if len(order) != step_count:
        raise ValueError(f"Wrong animation sequence size: {len(order)}, expected {step_count}")
    if len(delays) != step_count:
        raise ValueError(f"Wrong animation rate size: {len(delays)}, expected {step_count}")

    sequence: list[CursorFrame] = []
    for frame_index, delay in zip(order, delays):
        if frame_index >= len(icon_frames):
            raise ValueError(f"ANI sequence references missing frame {frame_index}")
        frame = icon_frames[frame_index].clone()
        frame.delay = delay / 60
        sequence.append(frame)

    return sequence


def parse_xcursor(blob: bytes) -> list[CursorFrame]:
    """Parse an Xcursor file."""
    if len(blob) < XCURSOR_FILE_HEADER.size:
        raise ValueError("Xcursor file is too small")

    magic, _, version, toc_size = XCURSOR_FILE_HEADER.unpack_from(blob, 0)
    if magic != XCURSOR_MAGIC:
        raise ValueError("Not an Xcursor file")
    if version != XCURSOR_VERSION:
        raise ValueError(f"Unsupported Xcursor version 0x{version:08x}")

    toc_end = XCURSOR_FILE_HEADER.size + toc_size * XCURSOR_TOC_CHUNK.size
    if len(blob) < toc_end:
        raise ValueError("Xcursor table of contents is truncated")

    chunks: list[tuple[int, int, int]] = []
    offset = XCURSOR_FILE_HEADER.size
    for _ in range(toc_size):
        chunks.append(XCURSOR_TOC_CHUNK.unpack_from(blob, offset))
        offset += XCURSOR_TOC_CHUNK.size

    images_by_size: dict[int, list[tuple[CursorImage, float]]] = defaultdict(list)
    for chunk_type, chunk_subtype, position in chunks:
        if chunk_type != XCURSOR_IMAGE_TYPE:
            continue
        if position + XCURSOR_IMAGE_HEADER.size > len(blob):
            raise ValueError("Xcursor image header is truncated")

        header_size, actual_type, nominal, _, width, height, hotspot_x, hotspot_y, delay = XCURSOR_IMAGE_HEADER.unpack_from(blob, position)
        if header_size != XCURSOR_IMAGE_HEADER.size:
            raise ValueError(f"Unexpected Xcursor image header size {header_size}")
        if actual_type != chunk_type or nominal != chunk_subtype:
            raise ValueError("Xcursor image chunk does not match table of contents")
        if width > 0x7FFF or height > 0x7FFF:
            raise ValueError(f"Xcursor image is too large: {width}x{height}")
        if hotspot_x > width or hotspot_y > height:
            raise ValueError("Xcursor hotspot is outside the image")

        image_start = position + XCURSOR_IMAGE_HEADER.size
        image_size = width * height * 4
        image_end = image_start + image_size
        if image_end > len(blob):
            raise ValueError("Xcursor pixel data is truncated")

        rgba = _unpremultiply_bgra_to_rgba(blob[image_start:image_end])
        image = Image.frombytes("RGBA", (width, height), rgba)
        images_by_size[nominal].append((CursorImage(image=image, hotspot=(hotspot_x, hotspot_y), nominal=nominal), delay / 1000))

    if not images_by_size:
        raise ValueError("Xcursor file does not contain images")

    frame_counts = {len(images) for images in images_by_size.values()}
    if len(frame_counts) != 1:
        raise ValueError("Xcursor animations must have the same frame count for every size")

    frames: list[CursorFrame] = []
    size_sequences = list(images_by_size.values())
    for frame_items in zip(*size_sequences):
        images = [item[0] for item in frame_items]
        frame_delays = {item[1] for item in frame_items}
        if len(frame_delays) != 1:
            raise ValueError("Xcursor animations must use the same delay for every size in a frame")
        frames.append(CursorFrame(images=images, delay=frame_items[0][1]))

    return frames


def _is_ani(blob: bytes) -> bool:
    if len(blob) < RIFF_HEADER.size:
        return False
    signature, _, subtype = RIFF_HEADER.unpack_from(blob, 0)
    return signature == b"RIFF" and subtype == b"ACON"


def _iter_chunks(blob: bytes, offset: int, end: int) -> Iterable[tuple[bytes, int, int, int]]:
    while offset + CHUNK_HEADER.size <= end:
        name, size = CHUNK_HEADER.unpack_from(blob, offset)
        payload_start = offset + CHUNK_HEADER.size
        payload_end = payload_start + size
        if payload_end > end:
            raise ValueError(f"Chunk {name!r} is truncated")
        yield name, size, payload_start, payload_end
        offset = payload_end + (payload_end & 1)


def _decode_cur_payload(payload: bytes, entry_width: int, entry_height: int) -> Image.Image:
    if payload.startswith(PNG_MAGIC):
        with Image.open(BytesIO(payload)) as image:
            return image.convert("RGBA").copy()
    return _decode_dib_payload(payload, entry_width, entry_height)


def _decode_dib_payload(payload: bytes, entry_width: int, entry_height: int) -> Image.Image:
    if len(payload) < 40:
        raise ValueError("DIB cursor payload is too small")

    header_size = struct.unpack_from("<I", payload, 0)[0]
    if header_size < 40 or len(payload) < header_size:
        raise ValueError(f"Unsupported DIB header size {header_size}")

    width, raw_height, planes, bit_count, compression, _, _, _, colors_used, _ = struct.unpack_from("<iiHHIIiiII", payload, 4)
    if planes != 1:
        raise ValueError(f"Unsupported DIB plane count {planes}")
    if compression != 0:
        raise ValueError(f"Unsupported compressed DIB cursor payload {compression}")
    if bit_count not in {24, 32}:
        raise ValueError(f"Unsupported DIB cursor bit depth {bit_count}")

    width = abs(width) or entry_width
    absolute_height = abs(raw_height)
    height = entry_height if absolute_height >= entry_height * 2 else absolute_height
    if width <= 0 or height <= 0:
        raise ValueError("Invalid DIB cursor dimensions")

    color_table_size = 0
    if bit_count <= 8:
        color_table_size = (colors_used or (1 << bit_count)) * 4
    pixel_offset = header_size + color_table_size
    row_stride = ((width * bit_count + 31) // 32) * 4
    xor_size = row_stride * height
    mask_offset = pixel_offset + xor_size
    mask_stride = ((width + 31) // 32) * 4
    if len(payload) < pixel_offset + xor_size:
        raise ValueError("DIB cursor pixel data is truncated")

    has_mask = len(payload) >= mask_offset + mask_stride * height
    bottom_up = raw_height > 0
    rgba = bytearray(width * height * 4)

    alpha_values: list[int] = []
    if bit_count == 32:
        for row in range(height):
            row_start = pixel_offset + row * row_stride
            alpha_values.extend(payload[row_start + 3 : row_start + width * 4 : 4])
    use_alpha_channel = any(alpha > 0 for alpha in alpha_values)

    for y in range(height):
        source_y = height - 1 - y if bottom_up else y
        source_row = pixel_offset + source_y * row_stride
        mask_row = mask_offset + source_y * mask_stride
        for x in range(width):
            dst = (y * width + x) * 4
            if bit_count == 32:
                src = source_row + x * 4
                b, g, r, a = payload[src : src + 4]
                alpha = a if use_alpha_channel else 255
            else:
                src = source_row + x * 3
                b, g, r = payload[src : src + 3]
                alpha = 255

            if has_mask:
                mask_byte = payload[mask_row + x // 8]
                if mask_byte & (0x80 >> (x % 8)):
                    alpha = 0

            rgba[dst : dst + 4] = bytes((r, g, b, alpha))

    return Image.frombytes("RGBA", (width, height), bytes(rgba))


def _unpremultiply_bgra_to_rgba(source: bytes) -> bytes:
    result = bytearray(len(source))
    for index in range(0, len(source), 4):
        blue = source[index]
        green = source[index + 1]
        red = source[index + 2]
        alpha = source[index + 3]
        if alpha == 0:
            red = green = blue = 0
        elif alpha < 255:
            red = min(255, (red * 255 + alpha // 2) // alpha)
            green = min(255, (green * 255 + alpha // 2) // alpha)
            blue = min(255, (blue * 255 + alpha // 2) // alpha)
        result[index : index + 4] = bytes((red, green, blue, alpha))
    return bytes(result)
