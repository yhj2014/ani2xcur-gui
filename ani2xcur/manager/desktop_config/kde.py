"""KDE 桌面环境配置工具

参考资料:
- KDE 当前会话光标未即时刷新问题: https://bugs.kde.org/show_bug.cgi?id=470265
"""

import shutil

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
            return name
    logger.debug("未找到 KDE 可执行文件候选: %s", names)
    return None


def _readconfig_executable() -> str | None:
    return _which_first("kreadconfig6", "kreadconfig5", "kreadconfig")


def _writeconfig_executable() -> str | None:
    return _which_first("kwriteconfig6", "kwriteconfig5", "kwriteconfig")


def _apply_plasma_cursor_theme(cursor_name: str) -> None:
    if is_wayland_session():
        logger.debug("当前为 Wayland 会话, 跳过 plasma-apply-cursortheme 即时应用")
        return

    executable = _which_first("plasma-apply-cursortheme")
    if executable is None:
        logger.debug("未找到 plasma-apply-cursortheme, 跳过 KDE 光标主题即时应用")
        return

    logger.debug("执行 KDE 光标主题即时应用命令: %s", [executable, cursor_name])
    run_cmd([executable, cursor_name], live=False, check=False)


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


def _refresh_current_session(cursor_name: str, cursor_size: int | None = None) -> None:
    if is_wayland_session():
        logger.debug("当前为 Wayland 会话, 跳过 KDE 当前会话即时刷新")
        return

    _notify_kde_cursor_change()
    apply_x_cursor_theme(cursor_name, cursor_size)


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
        return None

    result = result.strip()
    if result == "":
        return None

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
        return None

    result = result.strip()
    if result == "":
        return None

    cursor_size = safe_convert_to_int(result)
    if isinstance(cursor_size, int):
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
    _apply_plasma_cursor_theme(cursor_name)

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

    cursor_size = get_kde_cursor_size()
    _refresh_current_session(cursor_name, cursor_size)


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

    cursor_name = get_kde_cursor_theme()
    if cursor_name is not None:
        _apply_plasma_cursor_theme(cursor_name)
        _refresh_current_session(cursor_name, cursor_size)
    else:
        logger.debug("未读取到 KDE 当前光标主题, 跳过当前会话刷新")
