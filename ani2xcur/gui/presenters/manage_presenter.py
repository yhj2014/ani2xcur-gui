"""管理功能 Presenter"""

import sys

from ani2xcur.gui import logger
from ani2xcur.gui.presenters.base_presenter import BasePresenter
from ani2xcur.gui.models.cursor_info import ManageAction
from ani2xcur.gui.workers.manage_worker import ManageWorker


class ManagePresenter(BasePresenter):
    """光标管理 Presenter"""

    def __init__(self):
        super().__init__()
        self._worker: ManageWorker | None = None

    @property
    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def list_cursors(self):
        if self.is_busy:
            logger.warning("管理操作正在进行中")
            return
        action = ManageAction(action="list")
        self._start_action(action)

    def get_cursor_status(self):
        if self.is_busy:
            return
        action = ManageAction(action="get_info")
        self._start_action(action)

    def install_cursor(self, input_path: str, install_path: str = "", use_inf_config_path: bool = True):
        if self.is_busy:
            return
        action = ManageAction(
            action="install",
            input_path=input_path,
            install_path=install_path,
            use_inf_config_path=use_inf_config_path,
        )
        self._start_action(action)

    def uninstall_cursor(self, cursor_name: str):
        if self.is_busy:
            return
        action = ManageAction(action="uninstall", cursor_name=cursor_name)
        self._start_action(action)

    def set_theme(self, cursor_name: str):
        action = ManageAction(action="set_theme", cursor_name=cursor_name)
        self._start_action(action)

    def set_size(self, cursor_size: int):
        action = ManageAction(action="set_size", cursor_size=cursor_size)
        self._start_action(action)

    def export_cursor(self, cursor_name: str, output_path: str, compress: bool = False, compress_format: str = ".7z"):
        action = ManageAction(
            action="export",
            cursor_name=cursor_name,
            output_path=output_path,
            compress=compress,
            compress_format=compress_format,
        )
        self._start_action(action)

    def _start_action(self, action: ManageAction):
        try:
            self._worker = ManageWorker(action)
            self._worker.progress.connect(self._on_progress)
            self._worker.list_result.connect(self._on_list_result)
            self._worker.status_result.connect(self._on_status_result)
            self._worker.finished.connect(self._on_finished)
            self._worker.start()
            if self._view:
                self._view.set_busy(True)
        except Exception as e:
            logger.error("启动管理操作失败: %s", e)
            if self._view:
                self._view.show_error(f"操作启动失败: {e}")

    def _on_progress(self, percent: int, message: str):
        if self._view:
            self._view.update_progress(percent, message)

    def _on_list_result(self, cursors):
        if self._view:
            self._view.update_cursor_list(cursors)

    def _on_status_result(self, statuses):
        if self._view:
            self._view.update_cursor_status(statuses)

    def _on_finished(self, success: bool, message: str):
        logger.info("管理操作完成: success=%s, message=%s", success, message)
        self._worker = None
        if self._view:
            self._view.set_busy(False)
            if success:
                self._view.show_info(message)
            else:
                self._view.show_error(message)
