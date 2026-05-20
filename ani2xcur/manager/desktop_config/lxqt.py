"""LXQT 桌面环境配置工具

参考资料:
- LXQt 1.4.0 将鼠标指针配置写入 Xresources: https://lxqt-project.org/release/2023/11/05/lxqt-config-1-4-0/
"""

import shutil
import os
import configparser
from pathlib import Path

from ani2xcur.cmd import run_cmd
from ani2xcur.config import LOGGER_COLOR, LOGGER_LEVEL, LOGGER_NAME
from ani2xcur.logger import get_logger
from ani2xcur.utils import safe_convert_to_int
from ani2xcur.manager.desktop_config.base import is_wayland_session
from ani2xcur.manager.desktop_config import x_org
from ani2xcur.manager.desktop_config.x_cursor import apply_x_cursor_theme

logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)

LXQT_CONFIG_PATH = Path("~/.config/lxqt/session.conf").expanduser()
"""LXQT 桌面的配置文件路径"""

LXQT_GENERAL_SECTION = "General"
CURSOR_THEME_KEY = "cursor_theme"
CURSOR_SIZE_KEY = "cursor_size"


def _read_lxqt_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(LXQT_CONFIG_PATH, encoding="utf-8")
    logger.debug("读取 LXQt 配置文件: '%s', sections=%s", LXQT_CONFIG_PATH, config.sections())
    return config


def _write_lxqt_config(config: configparser.ConfigParser) -> None:
    LXQT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LXQT_CONFIG_PATH, "w", encoding="utf-8") as f:
        config.write(f, space_around_delimiters=False)
    logger.debug("写入 LXQt 配置文件: '%s'", LXQT_CONFIG_PATH)


def _ensure_general_section(config: configparser.ConfigParser) -> None:
    if LXQT_GENERAL_SECTION not in config:
        config[LXQT_GENERAL_SECTION] = {}


def _merge_x_resources() -> None:
    if is_wayland_session():
        logger.debug("当前为 Wayland 会话, 跳过 LXQt xrdb 合并")
        return

    if not shutil.which("xrdb"):
        logger.debug("未找到 xrdb, 跳过 LXQt Xresources 合并")
        return

    if not x_org.X_RESOURCES_PATH.is_file():
        logger.debug("Xresources 配置文件不存在, 跳过 LXQt Xresources 合并: '%s'", x_org.X_RESOURCES_PATH)
        return

    logger.debug("执行 LXQt Xresources 合并: '%s'", x_org.X_RESOURCES_PATH)
    run_cmd(["xrdb", "-merge", str(x_org.X_RESOURCES_PATH)], live=False, check=False)


def _refresh_root_cursor(cursor_name: str | None, cursor_size: int | None) -> None:
    if is_wayland_session():
        logger.debug("当前为 Wayland 会话, 跳过 LXQt X11 root 光标刷新")
        return

    if not shutil.which("xsetroot"):
        logger.debug("未找到 xsetroot, 跳过 LXQt X11 root 光标刷新")
        return

    custom_env = None
    if cursor_name is not None or cursor_size is not None:
        custom_env = os.environ.copy()
        if cursor_name is not None:
            custom_env["XCURSOR_THEME"] = cursor_name
        if cursor_size is not None:
            custom_env["XCURSOR_SIZE"] = str(cursor_size)

    logger.debug("执行 LXQt X11 root 光标刷新: cursor_name=%r, cursor_size=%r", cursor_name, cursor_size)
    run_cmd(["xsetroot", "-cursor_name", "left_ptr"], custom_env=custom_env, live=False, check=False)


def _update_session_environment(cursor_name: str | None, cursor_size: int | None) -> None:
    if not shutil.which("dbus-update-activation-environment"):
        logger.debug("未找到 dbus-update-activation-environment, 跳过会话环境更新")
        return

    variables = []
    if cursor_name is not None:
        variables.append(f"XCURSOR_THEME={cursor_name}")
    if cursor_size is not None:
        variables.append(f"XCURSOR_SIZE={cursor_size}")
    if not variables:
        logger.debug("未提供 Xcursor 会话环境变量, 跳过会话环境更新")
        return

    logger.debug("更新会话环境变量: %s", variables)
    run_cmd(
        ["dbus-update-activation-environment", "--systemd", *variables],
        live=False,
        check=False,
    )


def refresh_lxqt_cursor_session(cursor_name: str | None, cursor_size: int | None) -> None:
    """在光标配置文件写入后刷新 LXQt/Xcursor 会话状态。

    Args:
        cursor_name (str | None): 要应用的光标主题名称。
        cursor_size (int | None): 要应用的光标大小。
    """
    logger.debug("刷新 LXQt 光标会话: cursor_name=%r, cursor_size=%r", cursor_name, cursor_size)
    _merge_x_resources()
    _update_session_environment(cursor_name, cursor_size)
    apply_x_cursor_theme(cursor_name, cursor_size)
    _refresh_root_cursor(cursor_name, cursor_size)
    logger.debug("LXQt 光标会话刷新完成")


def get_lxqt_cursor_theme() -> str | None:
    """获取 LXQT 桌面当前使用的鼠标指针配置名称

    Returns:
        (str | None): 当前使用的鼠标指针名称
    """
    config = _read_lxqt_config()
    if LXQT_GENERAL_SECTION in config and CURSOR_THEME_KEY in config[LXQT_GENERAL_SECTION]:
        cursor_theme = config.get(LXQT_GENERAL_SECTION, CURSOR_THEME_KEY).strip()
        if cursor_theme != "":
            logger.debug("LXQt 当前光标主题读取结果: %s", cursor_theme)
            return cursor_theme

    logger.debug("LXQt 配置未提供光标主题, 回退读取 Xresources")
    return x_org.get_x_resources_cursor_theme()


def get_lxqt_cursor_size() -> int | None:
    """获取 LXQT 桌面当前使用的鼠标指针大小

    Returns:
        (int | None): 当前使用的鼠标指针大小
    """
    config = _read_lxqt_config()
    if LXQT_GENERAL_SECTION in config and CURSOR_SIZE_KEY in config[LXQT_GENERAL_SECTION]:
        cursor_size = safe_convert_to_int(config.get(LXQT_GENERAL_SECTION, CURSOR_SIZE_KEY))
        if isinstance(cursor_size, int):
            logger.debug("LXQt 当前光标大小读取结果: %s", cursor_size)
            return cursor_size

    logger.debug("LXQt 配置未提供有效光标大小, 回退读取 Xresources")
    return x_org.get_x_resources_cursor_size()


def set_lxqt_cursor_theme(
    cursor_name: str,
) -> None:
    """设置 LXQT 桌面当前使用的鼠标指针配置名称

    Args:
        cursor_name (str): 要设置的鼠标指针配置名称
    """
    config = _read_lxqt_config()
    _ensure_general_section(config)
    config[LXQT_GENERAL_SECTION][CURSOR_THEME_KEY] = cursor_name
    logger.debug("写入 LXQt 光标主题: %s", cursor_name)
    _write_lxqt_config(config)

    x_org.set_x_resources_cursor_theme(cursor_name)


def set_lxqt_cursor_size(
    cursor_size: int,
) -> None:
    """设置 LXQT 桌面当前使用的鼠标指针大小

    Args:
        cursor_size (int): 要设置的鼠标指针大小
    """
    config = _read_lxqt_config()
    _ensure_general_section(config)
    config[LXQT_GENERAL_SECTION][CURSOR_SIZE_KEY] = str(cursor_size)
    logger.debug("写入 LXQt 光标大小: %s", cursor_size)
    _write_lxqt_config(config)

    x_org.set_x_resources_cursor_size(cursor_size)
