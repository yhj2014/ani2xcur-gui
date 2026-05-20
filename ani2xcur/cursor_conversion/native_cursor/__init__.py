"""基于 Pillow 的光标转换工具。"""

from ani2xcur.cursor_conversion.native_cursor.process import (
    Win2xcurArgs,
    X2wincurArgs,
    win2xcur_process,
    x2wincur_process,
)

__all__ = [
    "Win2xcurArgs",
    "X2wincurArgs",
    "win2xcur_process",
    "x2wincur_process",
]
