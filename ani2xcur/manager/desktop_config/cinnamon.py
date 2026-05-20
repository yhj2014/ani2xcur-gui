"""Cinnamon 桌面环境配置工具"""

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

CINNAMON_SCHEMA = "org.cinnamon.desktop.interface"


def get_cinnamon_cursor_theme() -> str | None:
    """获取 Cinnamon 桌面当前使用的鼠标指针配置名称

    Returns:
        (str | None): 当前使用的鼠标指针名称
    """
    if not shutil.which("gsettings"):
        logger.debug("未找到 gsettings, 无法读取 Cinnamon 光标主题")
        return None

    result = run_cmd(
        ["gsettings", "get", CINNAMON_SCHEMA, "cursor-theme"],
        live=False,
        check=False,
    )

    if isinstance(result, str):
        result = result.strip()

    if result == "":
        result = None

    logger.debug("Cinnamon 当前光标主题读取结果: %r", result)
    return result


def get_cinnamon_cursor_size() -> int | None:
    """获取 Cinnamon 桌面当前使用的鼠标指针大小

    Returns:
        (int | None): 当前使用的鼠标指针大小
    """
    if not shutil.which("gsettings"):
        logger.debug("未找到 gsettings, 无法读取 Cinnamon 光标大小")
        return None

    result = run_cmd(
        ["gsettings", "get", CINNAMON_SCHEMA, "cursor-size"],
        live=False,
        check=False,
    )
    if isinstance(result, str):
        result = result.strip()

    if result == "":
        result = None

    cursor_size = safe_convert_to_int(result)
    logger.debug("Cinnamon 当前光标大小读取结果: %r", cursor_size)
    return cursor_size


def set_cinnamon_cursor_theme(
    cursor_name: str,
) -> None:
    """设置 Cinnamon 桌面当前使用的鼠标指针配置名称

    Args:
        cursor_name (str): 要设置的鼠标指针配置名称
    """
    if not shutil.which("gsettings"):
        logger.debug("未找到 gsettings, 跳过 Cinnamon 光标主题写入")
        return

    logger.debug("写入 Cinnamon 光标主题: %s", cursor_name)
    run_cmd(
        ["gsettings", "set", CINNAMON_SCHEMA, "cursor-theme", cursor_name],
        live=False,
        check=False,
    )


def set_cinnamon_cursor_size(
    cursor_size: int,
) -> None:
    """设置 Cinnamon 桌面当前使用的鼠标指针大小

    Args:
        cursor_size (int): 要设置的鼠标指针大小
    """
    if not shutil.which("gsettings"):
        logger.debug("未找到 gsettings, 跳过 Cinnamon 光标大小写入")
        return

    logger.debug("写入 Cinnamon 光标大小: %s", cursor_size)
    run_cmd(
        ["gsettings", "set", CINNAMON_SCHEMA, "cursor-size", str(cursor_size)],
        live=False,
        check=False,
    )
