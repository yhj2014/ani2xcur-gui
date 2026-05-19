"""Cursor file writers for Xcursor and Windows cursor formats."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from ani2xcur.cursor_conversion.native_cursor.models import CursorFrame
from ani2xcur.cursor_conversion.native_cursor.parsers import (
    ANIH_HEADER,
    CHUNK_HEADER,
    ICON_DIR,
    ICON_DIR_ENTRY,
    RIFF_HEADER,
    UNSIGNED,
    XCURSOR_FILE_HEADER,
    XCURSOR_IMAGE_HEADER,
    XCURSOR_IMAGE_TYPE,
    XCURSOR_MAGIC,
    XCURSOR_TOC_CHUNK,
    XCURSOR_VERSION,
)

ANI_ICON_FLAG = 0x1


def to_xcursor(frames: list[CursorFrame]) -> bytes:
    """Serialize frames to an Xcursor file."""
    chunks: list[tuple[int, int, bytes]] = []
    for frame in frames:
        for cursor in frame.images:
            image = cursor.image.convert("RGBA")
            width, height = image.size
            hotspot_x, hotspot_y = cursor.hotspot
            if width > 0x7FFF or height > 0x7FFF:
                raise ValueError(f"Xcursor image is too large: {width}x{height}")
            if not 0 <= hotspot_x <= width or not 0 <= hotspot_y <= height:
                raise ValueError(f"Cursor hotspot is outside the image: {cursor.hotspot}")

            header = XCURSOR_IMAGE_HEADER.pack(
                XCURSOR_IMAGE_HEADER.size,
                XCURSOR_IMAGE_TYPE,
                cursor.nominal,
                1,
                width,
                height,
                hotspot_x,
                hotspot_y,
                int(round(frame.delay * 1000)),
            )
            chunks.append((XCURSOR_IMAGE_TYPE, cursor.nominal, header + _premultiply_rgba_to_bgra(image.tobytes())))

    header = XCURSOR_FILE_HEADER.pack(
        XCURSOR_MAGIC,
        XCURSOR_FILE_HEADER.size,
        XCURSOR_VERSION,
        len(chunks),
    )

    offset = XCURSOR_FILE_HEADER.size + len(chunks) * XCURSOR_TOC_CHUNK.size
    toc: list[bytes] = []
    for chunk_type, chunk_subtype, chunk in chunks:
        toc.append(XCURSOR_TOC_CHUNK.pack(chunk_type, chunk_subtype, offset))
        offset += len(chunk)

    return b"".join([header, *toc, *(chunk for _, _, chunk in chunks)])


def to_cur(frame: CursorFrame) -> bytes:
    """Serialize a static frame to a Windows .cur file."""
    header = ICON_DIR.pack(0, 2, len(frame.images))
    directory: list[bytes] = []
    image_data: list[bytes] = []
    offset = ICON_DIR.size + len(frame.images) * ICON_DIR_ENTRY.size

    for cursor in frame.images:
        image = cursor.image.convert("RGBA")
        width, height = image.size
        if width > 256 or height > 256:
            raise ValueError(f"Image too big for CUR format: {width}x{height}")
        hotspot_x, hotspot_y = cursor.hotspot
        if not 0 <= hotspot_x <= width or not 0 <= hotspot_y <= height:
            raise ValueError(f"Cursor hotspot is outside the image: {cursor.hotspot}")

        png_blob = _image_to_png(image)
        image_data.append(png_blob)
        directory.append(
            ICON_DIR_ENTRY.pack(
                0 if width == 256 else width,
                0 if height == 256 else height,
                0,
                0,
                hotspot_x,
                hotspot_y,
                len(png_blob),
                offset,
            )
        )
        offset += len(png_blob)

    return b"".join([header, *directory, *image_data])


def to_ani(frames: list[CursorFrame]) -> bytes:
    """Serialize animated frames to a Windows .ani file."""
    rates = [_frame_delay_to_jiffies(frame.delay, animated=len(frames) > 1) for frame in frames]
    ani_header = ANIH_HEADER.pack(
        ANIH_HEADER.size,
        len(frames),
        len(frames),
        0,
        0,
        32,
        1,
        rates[0] if rates else 1,
        ANI_ICON_FLAG,
    )

    cursor_list = _ani_cursor_list(frames)
    rate_chunk = CHUNK_HEADER.pack(b"rate", UNSIGNED.size * len(rates)) + b"".join(UNSIGNED.pack(rate) for rate in rates)
    body = b"".join(
        [
            CHUNK_HEADER.pack(b"anih", len(ani_header)),
            ani_header,
            RIFF_HEADER.pack(b"LIST", len(cursor_list) + 4, b"fram"),
            cursor_list,
            rate_chunk,
        ]
    )
    return RIFF_HEADER.pack(b"RIFF", len(body) + 4, b"ACON") + body


def to_smart(frames: list[CursorFrame]) -> tuple[str, bytes]:
    """Choose .cur for static cursors and .ani for animated cursors."""
    if len(frames) == 1:
        return ".cur", to_cur(frames[0])
    return ".ani", to_ani(frames)


def _image_to_png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _ani_cursor_list(frames: list[CursorFrame]) -> bytes:
    chunks: list[bytes] = []
    for frame in frames:
        cur_file = to_cur(frame)
        chunk = CHUNK_HEADER.pack(b"icon", len(cur_file)) + cur_file
        if len(cur_file) & 1:
            chunk += b"\0"
        chunks.append(chunk)
    return b"".join(chunks)


def _frame_delay_to_jiffies(delay: float, animated: bool) -> int:
    jiffies = int(round(delay * 60))
    if animated and jiffies <= 0:
        return 1
    return jiffies


def _premultiply_rgba_to_bgra(source: bytes) -> bytes:
    result = bytearray(len(source))
    for index in range(0, len(source), 4):
        red = source[index]
        green = source[index + 1]
        blue = source[index + 2]
        alpha = source[index + 3]
        if alpha < 255:
            red = (red * alpha + 127) // 255
            green = (green * alpha + 127) // 255
            blue = (blue * alpha + 127) // 255
        result[index : index + 4] = bytes((blue, green, red, alpha))
    return bytes(result)
