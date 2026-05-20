import struct

from PIL import Image

from ani2xcur.cursor_conversion.native_cursor.models import CursorFrame, CursorImage
from ani2xcur.cursor_conversion.native_cursor.parsers import parse_blob
from ani2xcur.cursor_conversion.native_cursor.process import win2xcur_process
from ani2xcur.cursor_conversion.native_cursor.transforms import (
    DEFAULT_XCURSOR_SIZES,
    add_shadow_to_frames,
    normalize_xcursor_sizes,
    scale_frames,
)
from ani2xcur.cursor_conversion.native_cursor.writers import to_ani, to_cur, to_xcursor


def test_parse_cur_preserves_all_sizes_and_hotspots(windows_cursor_dir):
    frames = parse_blob((windows_cursor_dir / "Arrow.cur").read_bytes())

    assert len(frames) == 1
    assert [(image.image.size, image.hotspot, image.nominal) for image in frames[0].images] == [
        ((24, 24), (7, 4), 24),
        ((32, 32), (10, 5), 32),
        ((48, 48), (14, 8), 48),
    ]


def test_parse_ani_preserves_frame_delay_and_multi_size_images(windows_cursor_dir):
    frames = parse_blob((windows_cursor_dir / "Wait.ani").read_bytes())

    assert len(frames) == 23
    assert frames[0].delay == 2 / 60
    assert [image.image.size for image in frames[0].images] == [(32, 32), (48, 48), (64, 64)]


def test_xcursor_writer_round_trips_multisize_cursor():
    frames = [
        CursorFrame(
            images=[
                CursorImage(Image.new("RGBA", (2, 2), (100, 20, 40, 128)), (1, 1), 2),
                CursorImage(Image.new("RGBA", (4, 4), (40, 80, 120, 255)), (2, 2), 4),
            ],
            delay=0.125,
        )
    ]

    parsed = parse_blob(to_xcursor(frames))

    assert len(parsed) == 1
    assert parsed[0].delay == 0.125
    assert [(image.image.size, image.hotspot, image.nominal) for image in parsed[0].images] == [
        ((2, 2), (1, 1), 2),
        ((4, 4), (2, 2), 4),
    ]
    assert parsed[0].images[0].image.getpixel((0, 0)) == (100, 20, 40, 128)


def test_windows_writers_round_trip_static_and_animated_cursors():
    frame_a = CursorFrame([CursorImage(Image.new("RGBA", (16, 16), (255, 0, 0, 255)), (3, 4), 16)], delay=0.1)
    frame_b = CursorFrame([CursorImage(Image.new("RGBA", (16, 16), (0, 0, 255, 255)), (5, 6), 16)], delay=0.2)

    parsed_cur = parse_blob(to_cur(frame_a))
    parsed_ani = parse_blob(to_ani([frame_a, frame_b]))

    assert [(image.image.size, image.hotspot) for image in parsed_cur[0].images] == [((16, 16), (3, 4))]
    assert len(parsed_ani) == 2
    assert [frame.delay for frame in parsed_ani] == [0.1, 0.2]
    assert [frame.images[0].hotspot for frame in parsed_ani] == [(3, 4), (5, 6)]


def test_parse_32bit_dib_cur_uses_alpha_channel():
    cur_blob = _make_cur_blob(_make_32bit_dib_payload())

    frames = parse_blob(cur_blob)

    image = frames[0].images[0].image
    assert image.size == (2, 2)
    assert image.getpixel((0, 0)) == (255, 0, 0, 128)
    assert image.getpixel((1, 1)) == (255, 255, 255, 0)


def test_parse_24bit_dib_cur_uses_and_mask():
    cur_blob = _make_cur_blob(_make_24bit_dib_payload())

    frames = parse_blob(cur_blob)

    image = frames[0].images[0].image
    assert image.size == (2, 2)
    assert image.getpixel((0, 0)) == (255, 0, 0, 255)
    assert image.getpixel((1, 0)) == (0, 255, 0, 0)


def test_scale_frames_scales_images_and_hotspots():
    frames = [CursorFrame([CursorImage(Image.new("RGBA", (10, 8), (0, 0, 0, 255)), (2, 3), 10)])]

    scale_frames(frames, scale=2)

    assert frames[0].images[0].image.size == (20, 16)
    assert frames[0].images[0].hotspot == (4, 6)


def test_normalize_xcursor_sizes_expands_single_size_cursor():
    frames = [CursorFrame([CursorImage(Image.new("RGBA", (10, 10), (0, 0, 0, 255)), (2, 3), 10)])]

    normalize_xcursor_sizes(frames, [10, 20, 30])

    assert [(image.image.size, image.hotspot, image.nominal) for image in frames[0].images] == [
        ((10, 10), (2, 3), 10),
        ((20, 20), (4, 6), 20),
        ((30, 30), (6, 9), 30),
    ]


def test_normalize_xcursor_sizes_preserves_existing_images():
    small = CursorImage(Image.new("RGBA", (16, 16), (255, 0, 0, 255)), (1, 2), 16)
    large = CursorImage(Image.new("RGBA", (32, 32), (0, 0, 255, 255)), (2, 4), 32)
    frames = [CursorFrame([small, large])]

    normalize_xcursor_sizes(frames, [16, 24, 32])

    assert frames[0].images[0] is small
    assert frames[0].images[2] is large
    assert [(image.image.size, image.hotspot, image.nominal) for image in frames[0].images] == [
        ((16, 16), (1, 2), 16),
        ((24, 24), (2, 3), 24),
        ((32, 32), (2, 4), 32),
    ]


def test_normalize_xcursor_sizes_keeps_animation_delay():
    frames = [
        CursorFrame([CursorImage(Image.new("RGBA", (16, 16), (255, 0, 0, 255)), (3, 4), 16)], delay=0.1),
        CursorFrame([CursorImage(Image.new("RGBA", (16, 16), (0, 0, 255, 255)), (5, 6), 16)], delay=0.2),
    ]

    normalize_xcursor_sizes(frames, [16, 32])

    assert [frame.delay for frame in frames] == [0.1, 0.2]
    assert [[image.nominal for image in frame.images] for frame in frames] == [[16, 32], [16, 32]]


def test_scale_then_normalize_preserves_scaled_visual_size():
    frames = [CursorFrame([CursorImage(Image.new("RGBA", (10, 10), (0, 0, 0, 255)), (2, 3), 10)])]

    scale_frames(frames, scale=2)
    normalize_xcursor_sizes(frames, [10, 20])

    assert [(image.image.size, image.hotspot, image.nominal) for image in frames[0].images] == [
        ((20, 20), (4, 6), 10),
        ((40, 40), (8, 12), 20),
    ]


def test_win2xcur_process_synthesizes_default_sizes_from_single_size_cur(tmp_path):
    input_file = tmp_path / "single.cur"
    input_file.write_bytes(to_cur(CursorFrame([CursorImage(Image.new("RGBA", (16, 16), (0, 0, 0, 255)), (4, 5), 16)])))

    output_file = win2xcur_process(input_file, tmp_path)

    frames = parse_blob(output_file.read_bytes())
    assert [image.nominal for image in frames[0].images] == list(DEFAULT_XCURSOR_SIZES)


def test_shadow_uses_requested_opacity():
    frames = [CursorFrame([CursorImage(Image.new("RGBA", (4, 4), (255, 255, 255, 255)), (1, 1), 4)])]

    add_shadow_to_frames(
        frames,
        color="#000000",
        opacity=64,
        radius=0,
        sigma=0,
        xoffset=1,
        yoffset=0,
    )

    alpha_histogram = frames[0].images[0].image.convert("RGBA").getchannel("A").histogram()
    assert alpha_histogram[64] > 0


def _make_cur_blob(payload: bytes) -> bytes:
    header = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack("<BBBBHHII", 2, 2, 0, 0, 1, 1, len(payload), len(header) + 16)
    return header + entry + payload


def _make_32bit_dib_payload() -> bytes:
    width = 2
    height = 2
    row_stride = width * 4
    mask_stride = 4
    pixels_bottom_up = bytes(
        [
            255,
            0,
            0,
            255,
            255,
            255,
            255,
            0,
            0,
            0,
            255,
            128,
            0,
            255,
            0,
            255,
        ]
    )
    mask = b"\x00" * (mask_stride * height)
    header = struct.pack("<IiiHHIIiiII", 40, width, height * 2, 1, 32, 0, row_stride * height + len(mask), 0, 0, 0, 0)
    return header + pixels_bottom_up + mask


def _make_24bit_dib_payload() -> bytes:
    width = 2
    height = 2
    row_stride = 8
    mask_stride = 4
    bottom_row = bytes([255, 0, 0, 255, 255, 255, 0, 0])
    top_row = bytes([0, 0, 255, 0, 255, 0, 0, 0])
    bottom_mask = b"\x00\x00\x00\x00"
    top_mask = b"\x40\x00\x00\x00"
    header = struct.pack("<IiiHHIIiiII", 40, width, height * 2, 1, 24, 0, row_stride * height + mask_stride * height, 0, 0, 0, 0)
    return header + bottom_row + top_row + bottom_mask + top_mask
