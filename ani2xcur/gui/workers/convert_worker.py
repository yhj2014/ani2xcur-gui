"""转换后台 Worker"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QThread, Signal

from ani2xcur.gui import logger
from ani2xcur.gui.models.conversion_options import ConversionOptions
from ani2xcur.config import SMART_FINDER_SEARCH_DEPTH


class ConvertWorker(QThread):
    """转换后台线程"""

    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(self, options: ConversionOptions, parent=None):
        super().__init__(parent)
        self._options = options
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if self._options.direction == "win2x":
                result = self._run_win2x()
            else:
                result = self._run_x2win()

            if self._is_cancelled:
                self.finished.emit(False, "转换已取消")
            else:
                self.finished.emit(True, result)
        except FileNotFoundError as e:
            logger.error("转换失败 - 文件未找到: %s", e)
            self.finished.emit(False, f"文件未找到: {e}")
        except PermissionError as e:
            logger.error("转换失败 - 权限不足: %s", e)
            self.finished.emit(False, f"权限不足: {e}")
        except Exception as e:
            logger.error("转换失败: %s", e, exc_info=True)
            self.finished.emit(False, f"转换失败: {e}")

    def _resolve_output_path(self) -> Path:
        from ani2xcur.utils import is_http_or_https
        if self._options.output_path.strip():
            return Path(self._options.output_path).resolve()
        if is_http_or_https(self._options.input_path):
            return Path.cwd()
        return Path(self._options.input_path).resolve().parent

    def _run_win2x(self) -> str:
        from ani2xcur.cursor_conversion.convert import win_cursor_to_x11
        from ani2xcur.smart_finder import find_inf_file, find_desktop_entry_file
        from ani2xcur.file_operations.archive_manager import create_archive

        self.progress.emit(5, "正在查找 INF 配置文件...")
        output_path = self._resolve_output_path()

        with TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            inf_file = find_inf_file(input_file=self._options.input_path, temp_dir=temp_dir, depth=SMART_FINDER_SEARCH_DEPTH)
            if inf_file is None:
                raise FileNotFoundError("未找到鼠标指针的 INF 配置文件")
            if self._is_cancelled:
                return ""

            self.progress.emit(20, f"找到配置文件: {inf_file.name}")
            self.progress.emit(30, "正在转换光标文件...")

            win2x_args = self._options.to_win2x_args()
            save_path = win_cursor_to_x11(inf_file=inf_file, output_path=output_path, win2x_args=win2x_args)

            if self._is_cancelled:
                return ""

            self.progress.emit(70, f"转换完成: {save_path.name}")

            if self._options.auto_install and sys.platform == "linux":
                self.progress.emit(80, "正在安装光标...")
                from ani2xcur.manager.linux_cur_manager import install_linux_cursor
                from ani2xcur.manager.base import LINUX_USER_ICONS_PATH

                desktop_entry_file = find_desktop_entry_file(input_file=save_path, temp_dir=temp_dir, depth=SMART_FINDER_SEARCH_DEPTH)
                if desktop_entry_file is None:
                    raise FileNotFoundError("未找到 DesktopEntry 配置文件")
                install_path = Path(self._options.install_path) if self._options.install_path else LINUX_USER_ICONS_PATH
                install_linux_cursor(desktop_entry_file=desktop_entry_file, cursor_install_path=install_path)
                self.progress.emit(90, "安装完成")

            if self._options.compress:
                self.progress.emit(85, "正在打包...")
                archive_path = output_path / f"{save_path.name}{self._options.compress_format}"
                create_archive(sources=[save_path], archive_path=archive_path)
                self.progress.emit(95, f"打包完成: {archive_path.name}")

            self.progress.emit(100, f"转换完成: {save_path}")
            return str(save_path)

    def _run_x2win(self) -> str:
        from ani2xcur.cursor_conversion.convert import x11_cursor_to_win
        from ani2xcur.smart_finder import find_desktop_entry_file, find_inf_file
        from ani2xcur.file_operations.archive_manager import create_archive

        self.progress.emit(5, "正在查找主题配置文件...")
        output_path = self._resolve_output_path()

        with TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            desktop_entry_file = find_desktop_entry_file(input_file=self._options.input_path, temp_dir=temp_dir, depth=SMART_FINDER_SEARCH_DEPTH)
            if desktop_entry_file is None:
                raise FileNotFoundError("未找到 DesktopEntry 配置文件")
            if not (desktop_entry_file.parent / "cursors").is_dir():
                raise FileNotFoundError("鼠标指针目录缺失")
            if self._is_cancelled:
                return ""

            self.progress.emit(20, f"找到配置文件: {desktop_entry_file.name}")
            self.progress.emit(30, "正在转换光标文件...")

            x2win_args = self._options.to_x2win_args()
            save_path = x11_cursor_to_win(desktop_entry_file=desktop_entry_file, output_path=output_path, x2win_args=x2win_args)

            if self._is_cancelled:
                return ""

            self.progress.emit(70, f"转换完成: {save_path.name}")

            if self._options.auto_install and sys.platform == "win32":
                self.progress.emit(80, "正在安装光标...")
                from ani2xcur.manager.win_cur_manager import install_windows_cursor
                from ani2xcur.manager.base import WINDOWS_USER_CURSOR_PATH

                inf_file = find_inf_file(input_file=save_path, temp_dir=temp_dir, depth=SMART_FINDER_SEARCH_DEPTH)
                if inf_file is None:
                    raise FileNotFoundError("未找到 INF 配置文件")
                install_path = Path(self._options.install_path) if self._options.install_path else WINDOWS_USER_CURSOR_PATH
                install_windows_cursor(inf_file=inf_file, cursor_install_path=install_path)
                self.progress.emit(90, "安装完成")

            if self._options.compress:
                self.progress.emit(85, "正在打包...")
                archive_path = output_path / f"{save_path.name}{self._options.compress_format}"
                create_archive(sources=[save_path], archive_path=archive_path)
                self.progress.emit(95, f"打包完成: {archive_path.name}")

            self.progress.emit(100, f"转换完成: {save_path}")
            return str(save_path)
