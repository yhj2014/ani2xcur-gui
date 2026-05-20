"""Xfce 桌面环境配置工具

参考资料:
- xfconf-query 命令参数: https://docs.xfce.org/xfce/xfconf/xfconf-query
- xfsettingsd 监听并应用 xsettings: https://docs.xfce.org/xfce/xfce4-settings/xfsettingsd
"""

import shutil

from ani2xcur.cmd import run_cmd
from ani2xcur.config import LOGGER_COLOR, LOGGER_LEVEL, LOGGER_NAME
from ani2xcur.logger import get_logger
from ani2xcur.utils import safe_convert_to_int

logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)

XFCONF_QUERY = "xfconf-query"
XSETTINGS_CHANNEL = "xsettings"
CURSOR_THEME_PROPERTY = "/Gtk/CursorThemeName"
CURSOR_SIZE_PROPERTY = "/Gtk/CursorThemeSize"


def _xfconf_query_executable() -> str | None:
    if shutil.which(XFCONF_QUERY):
        logger.debug("找到 xfconf-query 可执行文件")
        return XFCONF_QUERY
    logger.debug("未找到 xfconf-query")
    return None


def _set_xfce_property(property_name: str, property_type: str, value: str) -> None:
    executable = _xfconf_query_executable()
    if executable is None:
        logger.debug("跳过 Xfce 属性写入: property=%s, value=%s", property_name, value)
        return

    logger.debug("写入 Xfce 属性: property=%s, type=%s, value=%s", property_name, property_type, value)
    run_cmd(
        [
            executable,
            "--channel",
            XSETTINGS_CHANNEL,
            "--property",
            property_name,
            "--create",
            "--type",
            property_type,
            "--set",
            value,
        ],
        live=False,
        check=False,
    )


def get_xfce_cursor_theme() -> str | None:
    """获取 Xfce 桌面当前使用的鼠标指针配置名称

    Returns:
        (str | None): 当前使用的鼠标指针名称
    """
    executable = _xfconf_query_executable()
    if executable is None:
        return None

    result = run_cmd(
        [
            executable,
            "--channel",
            XSETTINGS_CHANNEL,
            "--property",
            CURSOR_THEME_PROPERTY,
        ],
        live=False,
        check=False,
    )

    if not isinstance(result, str):
        return None

    result = result.strip()
    if result == "":
        logger.debug("Xfce 当前光标主题读取结果为空")
        return None

    logger.debug("Xfce 当前光标主题读取结果: %s", result)
    return result


def get_xfce_cursor_size() -> int | None:
    """获取 Xfce 桌面当前使用的鼠标指针大小

    Returns:
        (int | None): 当前使用的鼠标指针大小
    """
    executable = _xfconf_query_executable()
    if executable is None:
        return None

    result = run_cmd(
        [
            executable,
            "--channel",
            XSETTINGS_CHANNEL,
            "--property",
            CURSOR_SIZE_PROPERTY,
        ],
        live=False,
        check=False,
    )

    if not isinstance(result, str):
        return None

    result = result.strip()
    if result == "":
        logger.debug("Xfce 当前光标大小读取结果为空")
        return None

    cursor_size = safe_convert_to_int(result)
    if isinstance(cursor_size, int):
        logger.debug("Xfce 当前光标大小读取结果: %s", cursor_size)
        return cursor_size
    logger.debug("Xfce 当前光标大小读取结果不是整数: %r", result)
    return None


def set_xfce_cursor_theme(
    cursor_name: str,
) -> None:
    """设置 Xfce 桌面当前使用的鼠标指针配置名称

    Args:
        cursor_name (str): 要设置的鼠标指针配置名称
    """
    _set_xfce_property(CURSOR_THEME_PROPERTY, "string", cursor_name)


def set_xfce_cursor_size(
    cursor_size: int,
) -> None:
    """设置 Xfce 桌面当前使用的鼠标指针大小

    Args:
        cursor_size (int): 要设置的鼠标指针大小
    """
    _set_xfce_property(CURSOR_SIZE_PROPERTY, "int", str(cursor_size))
