import pytest

from ani2xcur.manager.desktop_config.base import (
    convert_windows_cursor_base_size_to_size,
    convert_windows_cursor_size_to_base_size,
)


@pytest.mark.parametrize(
    ("cursor_size", "cursor_base_size"),
    [
        (1, 32),
        (2, 48),
        (15, 256),
    ],
)
def test_convert_windows_cursor_size_to_base_size(cursor_size, cursor_base_size):
    assert convert_windows_cursor_size_to_base_size(cursor_size) == cursor_base_size


@pytest.mark.parametrize(
    ("cursor_base_size", "cursor_size"),
    [
        (32, 1),
        (48, 2),
        (256, 15),
    ],
)
def test_convert_windows_cursor_base_size_to_size(cursor_base_size, cursor_size):
    assert convert_windows_cursor_base_size_to_size(cursor_base_size) == cursor_size


@pytest.mark.parametrize("cursor_size", [0, 16])
def test_convert_windows_cursor_size_to_base_size_rejects_invalid_size(cursor_size):
    with pytest.raises(ValueError):
        convert_windows_cursor_size_to_base_size(cursor_size)


@pytest.mark.parametrize("cursor_base_size", [31, 33, 257])
def test_convert_windows_cursor_base_size_to_size_returns_none_for_unmatched_base_size(cursor_base_size):
    assert convert_windows_cursor_base_size_to_size(cursor_base_size) is None
