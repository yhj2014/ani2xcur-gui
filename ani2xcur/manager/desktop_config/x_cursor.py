"""Xcursor 当前会话刷新工具

参考资料:
- Xcursor API: https://manpages.ubuntu.com/manpages/resolute/man3/XcursorSetTheme.3.html
- XFixes 命名光标刷新: https://manpages.ubuntu.com/manpages/focal/man3/X11%3A%3AProtocol%3A%3AExt%3A%3AXFIXES.3pm.html
- X.Org 光标引用机制: https://xorg.freedesktop.org/wiki/Development/Documentation/CursorHandling/
"""

import os
import sys
import ctypes
from ctypes import c_int, c_char_p, c_ulong, c_void_p
from ctypes.util import find_library
from typing import Any

_CURSOR_NAMES = (
    "left_ptr",
    "default",
    "arrow",
    "top_left_arrow",
    "right_ptr",
    "hand1",
    "hand2",
    "pointer",
    "xterm",
    "text",
    "ibeam",
    "watch",
    "wait",
    "progress",
    "left_ptr_watch",
    "cross",
    "crosshair",
    "cross_reverse",
    "plus",
    "question_arrow",
    "help",
    "fleur",
    "move",
    "size_all",
    "sb_h_double_arrow",
    "ew-resize",
    "col-resize",
    "size_hor",
    "left_side",
    "right_side",
    "sb_v_double_arrow",
    "ns-resize",
    "row-resize",
    "size_ver",
    "top_side",
    "bottom_side",
    "top_left_corner",
    "nw-resize",
    "size_fdiag",
    "top_right_corner",
    "ne-resize",
    "size_bdiag",
    "bottom_left_corner",
    "sw-resize",
    "bottom_right_corner",
    "se-resize",
    "not-allowed",
    "no-drop",
    "dnd-no-drop",
    "forbidden",
    "copy",
    "dnd-copy",
    "link",
    "dnd-link",
    "openhand",
    "closedhand",
    "grab",
    "grabbing",
    "zoom-in",
    "zoom-out",
    "cell",
    "context-menu",
    "vertical-text",
    "alias",
    "all-scroll",
)


def _load_library(name: str) -> Any | None:
    library_path = find_library(name)
    if library_path is None:
        return None

    try:
        return ctypes.CDLL(library_path)
    except OSError:
        return None


def _configure_libraries(x11: Any, xcursor: Any, xfixes: Any) -> None:
    x11.XOpenDisplay.argtypes = [c_char_p]
    x11.XOpenDisplay.restype = c_void_p
    x11.XCloseDisplay.argtypes = [c_void_p]
    x11.XCloseDisplay.restype = c_int
    x11.XFlush.argtypes = [c_void_p]
    x11.XFlush.restype = c_int
    x11.XFreeCursor.argtypes = [c_void_p, c_ulong]
    x11.XFreeCursor.restype = c_int

    xcursor.XcursorSetTheme.argtypes = [c_void_p, c_char_p]
    xcursor.XcursorSetTheme.restype = None
    xcursor.XcursorSetDefaultSize.argtypes = [c_void_p, c_int]
    xcursor.XcursorSetDefaultSize.restype = None
    xcursor.XcursorLibraryLoadCursor.argtypes = [c_void_p, c_char_p]
    xcursor.XcursorLibraryLoadCursor.restype = c_ulong

    xfixes.XFixesChangeCursorByName.argtypes = [c_void_p, c_ulong, c_char_p]
    xfixes.XFixesChangeCursorByName.restype = None


def apply_x_cursor_theme(cursor_name: str | None, cursor_size: int | None = None) -> None:
    """刷新当前 X11 会话中已经加载过的常见鼠标指针

    Args:
        cursor_name (str | None): 要应用的鼠标指针主题名称
        cursor_size (int | None): 要应用的鼠标指针大小
    """
    if sys.platform == "win32" or not os.environ.get("DISPLAY"):
        return

    x11 = _load_library("X11")
    xcursor = _load_library("Xcursor")
    xfixes = _load_library("Xfixes")
    if x11 is None or xcursor is None or xfixes is None:
        return

    try:
        _configure_libraries(x11, xcursor, xfixes)
    except AttributeError:
        return

    display = x11.XOpenDisplay(os.environ["DISPLAY"].encode("utf-8"))
    if not display:
        return

    try:
        if cursor_name is not None:
            xcursor.XcursorSetTheme(display, cursor_name.encode("utf-8"))
        if cursor_size is not None:
            xcursor.XcursorSetDefaultSize(display, cursor_size)

        for cursor_shape in _CURSOR_NAMES:
            cursor = xcursor.XcursorLibraryLoadCursor(display, cursor_shape.encode("utf-8"))
            if cursor:
                xfixes.XFixesChangeCursorByName(display, cursor, cursor_shape.encode("utf-8"))
                x11.XFreeCursor(display, cursor)

        x11.XFlush(display)
    finally:
        x11.XCloseDisplay(display)
