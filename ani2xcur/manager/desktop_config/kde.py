"""KDE 桌面环境配置工具

参考资料:
- KDE 当前会话光标未即时刷新问题: https://bugs.kde.org/show_bug.cgi?id=470265
"""

import shutil
import os

from ani2xcur.cmd import run_cmd
from ani2xcur.config import (
    LOGGER_COLOR,
    LOGGER_LEVEL,
    LOGGER_NAME,
)
from ani2xcur.logger import get_logger
from ani2xcur.manager.desktop_config.base import is_wayland_session
from ani2xcur.utils import safe_convert_to_int
from ani2xcur.manager.desktop_config.x_cursor import apply_x_cursor_theme

logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)


def _which_first(*names: str) -> str | None:
    for name in names:
        executable = shutil.which(name)
        if executable:
            logger.debug("找到 KDE 可执行文件候选: %s -> %s", name, executable)
            return name
    logger.debug("未找到 KDE 可执行文件候选: %s", names)
    return None


def _readconfig_executable() -> str | None:
    return _which_first("kreadconfig6", "kreadconfig5", "kreadconfig")


def _writeconfig_executable() -> str | None:
    return _which_first("kwriteconfig6", "kwriteconfig5", "kwriteconfig")


def _apply_plasma_cursor_theme(cursor_name: str | None, cursor_size: int | None) -> None:
    if cursor_name is None:
        logger.debug("未提供 KDE 光标主题名称, 跳过 plasma-apply-cursortheme")
        return

    executable = _which_first("plasma-apply-cursortheme")
    if executable is None:
        logger.debug("未找到 plasma-apply-cursortheme, 跳过 KDE 光标主题即时应用")
        return

    command = [executable, cursor_name]
    logger.debug("执行 KDE 光标主题即时应用命令: %s", command)
    run_cmd(command, live=False, check=False)

    if cursor_size is None:
        return

    sized_command = [executable, cursor_name, "--size", str(cursor_size)]
    logger.debug("执行 KDE 光标大小即时应用命令: %s", sized_command)
    run_cmd(sized_command, live=False, check=False)


def _notify_kde_cursor_change() -> None:
    dbus_send = shutil.which("dbus-send")
    if not dbus_send:
        logger.debug("未找到 dbus-send, 跳过 KDE D-Bus 光标变更通知")
        return

    command = [
        "dbus-send",
        "--session",
        "--type=signal",
        "/KGlobalSettings",
        "org.kde.KGlobalSettings.notifyChange",
        "int32:5",
        "int32:0",
    ]
    logger.debug("执行 KDE D-Bus 光标变更通知命令: %s", command)
    run_cmd(
        command,
        live=False,
        check=False,
    )


def _refresh_root_cursor(cursor_name: str | None, cursor_size: int | None) -> None:
    if not shutil.which("xsetroot"):
        logger.debug("未找到 xsetroot, 跳过 X11 root 光标刷新")
        return

    custom_env = None
    if cursor_name is not None or cursor_size is not None:
        custom_env = os.environ.copy()
        if cursor_name is not None:
            custom_env["XCURSOR_THEME"] = cursor_name
        if cursor_size is not None:
            custom_env["XCURSOR_SIZE"] = str(cursor_size)

    command = ["xsetroot", "-cursor_name", "left_ptr"]
    logger.debug("执行 X11 root 光标刷新命令: %s, cursor_name=%r, cursor_size=%r", command, cursor_name, cursor_size)
    run_cmd(command, custom_env=custom_env, live=False, check=False)


def refresh_kde_cursor_session(cursor_name: str | None, cursor_size: int | None = None) -> None:
    """在光标配置文件写入后刷新 KDE 会话中的光标状态。

    Args:
        cursor_name (str | None): 要应用的光标主题名称。
        cursor_size (int | None): 要应用的光标大小。
    """
    logger.debug("刷新 KDE 光标会话: cursor_name=%r, cursor_size=%r", cursor_name, cursor_size)
    _apply_plasma_cursor_theme(cursor_name, cursor_size)
    _notify_kde_cursor_change()
    if is_wayland_session():
        logger.debug("当前为 Wayland 会话, 跳过 KDE X11-only 光标刷新")
        return

    apply_x_cursor_theme(cursor_name, cursor_size)
    _refresh_root_cursor(cursor_name, cursor_size)
    logger.debug("KDE 光标会话刷新完成")


def get_kde_cursor_theme() -> str | None:
    """获取 KDE 桌面当前使用的鼠标指针配置名称

    Returns:
        (str | None): 当前使用的鼠标指针名称
    """
    executable = _readconfig_executable()
    if executable is None:
        logger.debug("未找到 KDE readconfig 可执行文件, 无法读取当前光标主题")
        return None

    command = [
        executable,
        "--file",
        "kcminputrc",
        "--group",
        "Mouse",
        "--key",
        "cursorTheme",
    ]
    result = run_cmd(
        command,
        live=False,
        check=False,
    )

    if not isinstance(result, str):
        logger.debug("KDE 当前光标主题读取结果不是字符串: %r", result)
        return None

    result = result.strip()
    if result == "":
        logger.debug("KDE 当前光标主题读取结果为空")
        return None

    logger.debug("KDE 当前光标主题读取结果: %s", result)
    return result


def get_kde_cursor_size() -> int | None:
    """获取 KDE 桌面当前使用的鼠标指针大小

    Returns:
        (int | None): 当前使用的鼠标指针大小
    """
    executable = _readconfig_executable()
    if executable is None:
        logger.debug("未找到 KDE readconfig 可执行文件, 无法读取当前光标大小")
        return None

    command = [
        executable,
        "--file",
        "kcminputrc",
        "--group",
        "Mouse",
        "--key",
        "cursorSize",
    ]
    result = run_cmd(
        command,
        live=False,
        check=False,
    )

    if not isinstance(result, str):
        logger.debug("KDE 当前光标大小读取结果不是字符串: %r", result)
        return None

    result = result.strip()
    if result == "":
        logger.debug("KDE 当前光标大小读取结果为空")
        return None

    cursor_size = safe_convert_to_int(result)
    if isinstance(cursor_size, int):
        logger.debug("KDE 当前光标大小读取结果: %s", cursor_size)
        return cursor_size
    logger.debug("KDE 当前光标大小读取结果不是整数: %r", result)
    return None


def set_kde_cursor_theme(
    cursor_name: str,
) -> None:
    """设置 KDE 桌面当前使用的鼠标指针配置名称

    Args:
        cursor_name (str): 要设置的鼠标指针配置名称
    """
    executable = _writeconfig_executable()
    if executable is not None:
        command = [executable, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", cursor_name]
        logger.debug("执行 KDE 光标主题写入命令: %s", command)
        run_cmd(
            command,
            live=False,
            check=False,
        )
    else:
        logger.debug("未找到 KDE writeconfig 可执行文件, 跳过 kcminputrc 光标主题写入")


def set_kde_cursor_size(
    cursor_size: int,
) -> None:
    """设置 KDE 桌面当前使用的鼠标指针大小

    Args:
        cursor_size (int): 要设置的鼠标指针大小
    """
    executable = _writeconfig_executable()
    if executable is None:
        logger.debug("未找到 KDE writeconfig 可执行文件, 无法写入光标大小")
        return

    command = [executable, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorSize", str(cursor_size)]
    logger.debug("执行 KDE 光标大小写入命令: %s", command)
    run_cmd(
        command,
        live=False,
        check=False,
    )
