"""管理后台 Worker"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QThread, Signal

from ani2xcur.gui import logger
from ani2xcur.gui.models.cursor_info import CursorSchemeInfo, CurrentCursorStatus, ManageAction
from ani2xcur.config import SMART_FINDER_SEARCH_DEPTH


class ManageWorker(QThread):
    """管理操作后台线程"""

    progress = Signal(int, str)
    list_result = Signal(object)
    status_result = Signal(object)
    finished = Signal(bool, str)

    def __init__(self, action: ManageAction, parent=None):
        super().__init__(parent)
        self._action = action

    @property
    def action_type(self) -> str:
        return self._action.action

    def run(self):
        try:
            action = self._action.action
            logger.info("管理操作开始: %s", action)

            if action == "list":
                self._do_list()
            elif action == "get_info":
                self._do_get_info()
            elif action == "install":
                self._do_install()
            elif action == "uninstall":
                self._do_uninstall()
            elif action == "set_theme":
                self._do_set_theme()
            elif action == "set_size":
                self._do_set_size()
            elif action == "export":
                self._do_export()
            else:
                self.finished.emit(False, f"未知操作: {action}")

        except FileNotFoundError as e:
            logger.error("管理操作失败 - 文件未找到: %s", e)
            self.finished.emit(False, f"文件未找到: {e}")
        except PermissionError as e:
            logger.error("管理操作失败 - 权限不足: %s", e)
            self.finished.emit(False, f"权限不足: {e}")
        except Exception as e:
            logger.error("管理操作失败: %s", e, exc_info=True)
            self.finished.emit(False, f"操作失败: {e}")

    def _do_list(self):
        self.progress.emit(10, "正在扫描已安装光标...")

        if sys.platform == "win32":
            from ani2xcur.manager.win_cur_manager import list_windows_cursors
            raw_list = list_windows_cursors()
        elif sys.platform == "linux":
            from ani2xcur.manager.linux_cur_manager import list_linux_cursors
            raw_list = list_linux_cursors()
        else:
            self.finished.emit(False, f"不支持的系统: {sys.platform}")
            return

        self.progress.emit(70, "正在整理列表...")
        cursors = [
            CursorSchemeInfo(
                name=item["name"],
                cursor_files=item.get("cursor_files", []),
                install_paths=item.get("install_paths", []),
            )
            for item in raw_list
        ]
        self.progress.emit(90, f"发现 {len(cursors)} 个光标")
        self.list_result.emit(cursors)
        self.finished.emit(True, f"已加载 {len(cursors)} 个光标")

    def _do_get_info(self):
        self.progress.emit(30, "正在获取光标状态...")

        if sys.platform == "win32":
            from ani2xcur.manager.win_cur_manager import get_windows_cursor_info
            raw_info = get_windows_cursor_info()
        elif sys.platform == "linux":
            from ani2xcur.manager.linux_cur_manager import get_linux_cursor_info
            raw_info = get_linux_cursor_info()
        else:
            self.finished.emit(False, f"不支持的系统: {sys.platform}")
            return

        statuses = [
            CurrentCursorStatus(platform=item.get("platform", ""), cursor_name=item.get("cursor_name"), cursor_size=item.get("cursor_size"))
            for item in raw_info
        ]
        self.progress.emit(100, "状态获取完成")
        self.status_result.emit(statuses)
        self.finished.emit(True, "状态已刷新")

    def _do_install(self):
        self.progress.emit(10, "正在查找配置文件...")

        if sys.platform == "win32":
            from ani2xcur.manager.win_cur_manager import install_windows_cursor
            from ani2xcur.manager.base import WINDOWS_USER_CURSOR_PATH
            from ani2xcur.smart_finder import find_inf_file

            install_path = None
            if self._action.install_path.strip():
                install_path = Path(self._action.install_path)
            elif not self._action.use_inf_config_path:
                install_path = WINDOWS_USER_CURSOR_PATH

            with TemporaryDirectory() as temp_dir:
                inf_file = find_inf_file(input_file=self._action.input_path, temp_dir=Path(temp_dir), depth=SMART_FINDER_SEARCH_DEPTH)
                if inf_file is None:
                    raise FileNotFoundError("未找到 INF 配置文件")
                self.progress.emit(30, "正在安装光标...")
                install_windows_cursor(inf_file=inf_file, cursor_install_path=install_path)

        elif sys.platform == "linux":
            from ani2xcur.manager.linux_cur_manager import install_linux_cursor
            from ani2xcur.manager.base import LINUX_USER_ICONS_PATH
            from ani2xcur.smart_finder import find_desktop_entry_file

            install_path = Path(self._action.install_path) if self._action.install_path.strip() else LINUX_USER_ICONS_PATH

            with TemporaryDirectory() as temp_dir:
                desktop_entry_file = find_desktop_entry_file(input_file=self._action.input_path, temp_dir=Path(temp_dir), depth=SMART_FINDER_SEARCH_DEPTH)
                if desktop_entry_file is None:
                    raise FileNotFoundError("未找到 DesktopEntry 配置文件")
                if not (desktop_entry_file.parent / "cursors").is_dir():
                    raise FileNotFoundError("鼠标指针目录缺失")
                self.progress.emit(30, "正在安装光标...")
                install_linux_cursor(desktop_entry_file=desktop_entry_file, cursor_install_path=install_path)
        else:
            self.finished.emit(False, f"不支持的系统: {sys.platform}")
            return

        self.progress.emit(100, "安装完成")
        self.finished.emit(True, "光标安装成功")

    def _do_uninstall(self):
        self.progress.emit(30, f"正在卸载 {self._action.cursor_name}...")

        if sys.platform == "win32":
            from ani2xcur.manager.win_cur_manager import delete_windows_cursor
            delete_windows_cursor(self._action.cursor_name)
        elif sys.platform == "linux":
            from ani2xcur.manager.linux_cur_manager import delete_linux_cursor
            delete_linux_cursor(self._action.cursor_name)
        else:
            self.finished.emit(False, f"不支持的系统: {sys.platform}")
            return

        self.progress.emit(100, "卸载完成")
        self.finished.emit(True, f"光标 {self._action.cursor_name} 已卸载")

    def _do_set_theme(self):
        self.progress.emit(30, f"正在设置主题: {self._action.cursor_name}...")

        if sys.platform == "win32":
            from ani2xcur.manager.win_cur_manager import set_windows_cursor_theme
            set_windows_cursor_theme(self._action.cursor_name)
        elif sys.platform == "linux":
            from ani2xcur.manager.linux_cur_manager import set_linux_cursor_theme
            set_linux_cursor_theme(self._action.cursor_name)
        else:
            self.finished.emit(False, f"不支持的系统: {sys.platform}")
            return

        self.progress.emit(100, "主题设置完成")
        self.finished.emit(True, f"已切换到主题: {self._action.cursor_name}")

    def _do_set_size(self):
        self.progress.emit(30, f"正在设置大小: {self._action.cursor_size}...")

        if sys.platform == "win32":
            from ani2xcur.manager.win_cur_manager import set_windows_cursor_size
            set_windows_cursor_size(self._action.cursor_size)
        elif sys.platform == "linux":
            from ani2xcur.manager.linux_cur_manager import set_linux_cursor_size
            set_linux_cursor_size(self._action.cursor_size)
        else:
            self.finished.emit(False, f"不支持的系统: {sys.platform}")
            return

        self.progress.emit(100, "大小设置完成")
        self.finished.emit(True, f"光标大小已设置为: {self._action.cursor_size}")

    def _do_export(self):
        self.progress.emit(10, f"正在导出 {self._action.cursor_name}...")
        output_path = Path(self._action.output_path)

        if sys.platform == "win32":
            from ani2xcur.manager.win_cur_manager import export_windows_cursor
            save_path = export_windows_cursor(cursor_name=self._action.cursor_name, output_path=output_path)
        elif sys.platform == "linux":
            from ani2xcur.manager.linux_cur_manager import export_linux_cursor
            save_path = export_linux_cursor(cursor_name=self._action.cursor_name, output_path=output_path)
        else:
            self.finished.emit(False, f"不支持的系统: {sys.platform}")
            return

        self.progress.emit(70, "导出完成")

        if self._action.compress:
            self.progress.emit(80, "正在打包...")
            from ani2xcur.file_operations.archive_manager import create_archive
            archive_path = output_path / f"{save_path.name}{self._action.compress_format}"
            create_archive(sources=[save_path], archive_path=archive_path)
            self.progress.emit(95, f"打包完成: {archive_path.name}")

        self.progress.emit(100, f"导出完成: {save_path}")
        self.finished.emit(True, f"光标已导出到: {save_path}")
