"""KDE 桌面环境配置工具"""

import shutil

from ani2xcur.cmd import run_cmd
from ani2xcur.utils import safe_convert_to_int


def _which_first(*names: str) -> str | None:
    for name in names:
        if shutil.which(name):
            return name
    return None


def _readconfig_executable() -> str | None:
    return _which_first("kreadconfig6", "kreadconfig5", "kreadconfig")


def _writeconfig_executable() -> str | None:
    return _which_first("kwriteconfig6", "kwriteconfig5", "kwriteconfig")


def _apply_cursor_theme(cursor_name: str) -> None:
    executable = _which_first("plasma-apply-cursortheme")
    if executable is None:
        return

    run_cmd([executable, cursor_name], live=False, check=False)


def get_kde_cursor_theme() -> str | None:
    """获取 KDE 桌面当前使用的鼠标指针配置名称

    Returns:
        (str | None): 当前使用的鼠标指针名称
    """
    executable = _readconfig_executable()
    if executable is None:
        return None

    result = run_cmd(
        [
            executable,
            "--file",
            "kcminputrc",
            "--group",
            "Mouse",
            "--key",
            "cursorTheme",
        ],
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
        return None

    result = run_cmd(
        [
            executable,
            "--file",
            "kcminputrc",
            "--group",
            "Mouse",
            "--key",
            "cursorSize",
        ],
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
        run_cmd(
            [executable, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", cursor_name],
            live=False,
            check=False,
        )

    _apply_cursor_theme(cursor_name)


def set_kde_cursor_size(
    cursor_size: int,
) -> None:
    """设置 KDE 桌面当前使用的鼠标指针大小

    Args:
        cursor_size (int): 要设置的鼠标指针大小
    """
    executable = _writeconfig_executable()
    if executable is None:
        return

    run_cmd(
        [executable, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorSize", str(cursor_size)],
        live=False,
        check=False,
    )

    cursor_name = get_kde_cursor_theme()
    if cursor_name is not None:
        _apply_cursor_theme(cursor_name)
