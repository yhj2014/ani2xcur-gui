"""基于 Pillow 的光标转换工具。

- **Xcursor 手册：** https://www.x.org/archive/X11R7.5/doc/man/man3/Xcursor.3.html
- **xcursorgen 手册：** https://www.x.org/releases/X11R6.8.1/doc/xcursorgen.1.html
- **Freedesktop 图标主题规范：** https://specifications.freedesktop.org/icon-theme/latest/
- **wayland-cursor CursorTheme 文档：** https://docs.rs/wayland-cursor/latest/wayland_cursor/struct.CursorTheme.html
- **Pillow 图像格式文档：** https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
"""

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
