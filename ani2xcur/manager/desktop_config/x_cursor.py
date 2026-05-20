"""Xcursor 当前会话刷新工具

参考资料:
- Xcursor API: https://manpages.ubuntu.com/manpages/resolute/man3/XcursorSetTheme.3.html
- XFixes 命名光标刷新: https://manpages.ubuntu.com/manpages/focal/man3/X11%3A%3AProtocol%3A%3AExt%3A%3AXFIXES.3pm.html
- X.Org 光标引用机制: https://xorg.freedesktop.org/wiki/Development/Documentation/CursorHandling/
"""

import os
import sys
import ctypes
from pathlib import Path
from ctypes import c_int, c_char_p, c_ulong, c_void_p
from ctypes.util import find_library
from collections.abc import Iterator
from typing import Any

from ani2xcur.config import (
    LOGGER_COLOR,
    LOGGER_LEVEL,
    LOGGER_NAME,
)
from ani2xcur.logger import get_logger
from ani2xcur.manager.base import (
    LINUX_CURSOR_KEYS,
    LINUX_CURSOR_LINKS,
    LINUX_ICONS_PATH,
    LINUX_USER_ICONS_PATH,
)

logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)

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

_XCURSOR_THEME_PATHS = (
    LINUX_USER_ICONS_PATH,
    Path("~/.local/share/icons").expanduser(),
    LINUX_ICONS_PATH,
)


def _load_library(name: str) -> Any | None:
    library_path = find_library(name)
    if library_path is None:
        logger.debug("未找到 Xcursor 刷新依赖库: '%s'", name)
        return None

    try:
        return ctypes.CDLL(library_path)
    except OSError as e:
        logger.debug("加载 Xcursor 刷新依赖库失败: '%s' -> '%s', 错误: %s", name, library_path, e)
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


def _is_wayland_session() -> bool:
    session_type = os.environ.get("XDG_SESSION_TYPE", "").casefold()
    wayland_display = os.environ.get("WAYLAND_DISPLAY")
    display = os.environ.get("DISPLAY")
    if session_type == "wayland":
        logger.debug("当前会话明确为 Wayland, 跳过 X11 鼠标指针刷新")
        return True
    if session_type == "x11":
        return False

    is_wayland = bool(wayland_display) and bool(display)
    if is_wayland:
        logger.debug("会话类型未知但检测到 Wayland/XWayland 环境, 跳过 X11 鼠标指针刷新")
    return is_wayland


def _iter_theme_cursor_names(cursor_name: str | None) -> Iterator[str]:
    if cursor_name is None:
        return

    for theme_path in _XCURSOR_THEME_PATHS:
        cursors_dir = theme_path / cursor_name / "cursors"
        if not cursors_dir.is_dir():
            continue

        try:
            for cursor_file in cursors_dir.iterdir():
                if cursor_file.name.startswith("."):
                    continue
                if cursor_file.is_file() or cursor_file.is_symlink():
                    yield cursor_file.name
        except OSError as e:
            logger.debug("读取 Xcursor 主题光标文件列表失败: '%s', 错误: %s", cursors_dir, e)


def _iter_cursor_names(cursor_name: str | None) -> Iterator[str]:
    seen: set[str] = set()
    cursor_link_names = (name for pair in LINUX_CURSOR_LINKS for name in pair)
    for name in (*_CURSOR_NAMES, *LINUX_CURSOR_KEYS, *cursor_link_names, *_iter_theme_cursor_names(cursor_name)):
        if name in seen:
            continue
        seen.add(name)
        yield name


def apply_x_cursor_theme(cursor_name: str | None, cursor_size: int | None = None) -> None:
    """刷新当前 X11 会话中已经加载过的常见鼠标指针

    Args:
        cursor_name (str | None): 要应用的鼠标指针主题名称
        cursor_size (int | None): 要应用的鼠标指针大小
    """
    if sys.platform == "win32":
        logger.debug("当前平台为 Windows, 跳过 X11 鼠标指针刷新")
        return

    display_name = os.environ.get("DISPLAY")
    if not display_name:
        logger.debug("环境变量 DISPLAY 为空, 跳过 X11 鼠标指针刷新")
        return

    if _is_wayland_session():
        return

    x11 = _load_library("X11")
    xcursor = _load_library("Xcursor")
    xfixes = _load_library("Xfixes")
    if x11 is None or xcursor is None or xfixes is None:
        logger.debug(
            "X11 鼠标指针刷新依赖库不完整, 跳过刷新: X11=%s, Xcursor=%s, Xfixes=%s",
            x11 is not None,
            xcursor is not None,
            xfixes is not None,
        )
        return

    try:
        _configure_libraries(x11, xcursor, xfixes)
    except AttributeError as e:
        logger.debug("配置 X11 / Xcursor / Xfixes 函数签名失败, 跳过刷新: %s", e)
        return

    display = x11.XOpenDisplay(display_name.encode("utf-8"))
    if not display:
        logger.debug("打开 X11 display 失败, 跳过 X11 鼠标指针刷新: '%s'", display_name)
        return

    try:
        if cursor_name is not None:
            xcursor.XcursorSetTheme(display, cursor_name.encode("utf-8"))
        if cursor_size is not None:
            xcursor.XcursorSetDefaultSize(display, cursor_size)

        changed_count = 0
        missing_count = 0
        for cursor_shape in _iter_cursor_names(cursor_name):
            cursor = xcursor.XcursorLibraryLoadCursor(display, cursor_shape.encode("utf-8"))
            if cursor:
                xfixes.XFixesChangeCursorByName(display, cursor, cursor_shape.encode("utf-8"))
                x11.XFreeCursor(display, cursor)
                changed_count += 1
            else:
                missing_count += 1

        x11.XFlush(display)
        logger.debug("Xcursor 当前 X11 会话刷新完成: changed=%s, missing=%s", changed_count, missing_count)
    finally:
        x11.XCloseDisplay(display)
