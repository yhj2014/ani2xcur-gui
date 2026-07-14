"""转换 Presenter"""

from ani2xcur.gui import logger
from ani2xcur.gui.presenters.base_presenter import BasePresenter
from ani2xcur.gui.models.conversion_options import ConversionOptions
from ani2xcur.gui.workers.convert_worker import ConvertWorker


class ConvertPresenter(BasePresenter):
    """转换功能 Presenter"""

    def __init__(self):
        super().__init__()
        self._worker: ConvertWorker | None = None
        self._options = ConversionOptions()

    @property
    def options(self) -> ConversionOptions:
        return self._options

    @property
    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def start_conversion(self):
        if self.is_busy:
            logger.warning("转换任务正在进行中")
            return
        if not self._options.input_path.strip():
            logger.error("未设置输入路径")
            if self._view:
                self._view.show_error("请设置输入路径")
            return
        try:
            self._worker = ConvertWorker(self._options)
            self._worker.progress.connect(self._on_progress)
            self._worker.finished.connect(self._on_finished)
            self._worker.start()
            logger.info("转换任务已启动: %s", self._options.input_path)
            if self._view:
                self._view.set_busy(True)
        except Exception as e:
            logger.error("启动转换失败: %s", e)
            if self._view:
                self._view.show_error(f"启动转换失败: {e}")

    def cancel_conversion(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.quit()
            self._worker.wait(3000)
            logger.info("转换任务已取消")
            if self._view:
                self._view.set_busy(False)
                self._view.show_info("转换已取消")

    def set_input_path(self, path: str):
        self._options.input_path = path

    def set_output_path(self, path: str):
        self._options.output_path = path

    def set_direction(self, direction: str):
        self._options.direction = direction

    def set_auto_install(self, enabled: bool):
        self._options.auto_install = enabled

    def set_compress(self, enabled: bool):
        self._options.compress = enabled

    def _on_progress(self, percent: int, message: str):
        logger.debug("转换进度: %d%% - %s", percent, message)
        if self._view:
            self._view.update_progress(percent, message)

    def _on_finished(self, success: bool, message: str):
        logger.info("转换完成: success=%s, message=%s", success, message)
        self._worker = None
        if self._view:
            self._view.set_busy(False)
            if success:
                self._view.show_info(f"转换完成: {message}")
            else:
                self._view.show_error(f"转换失败: {message}")
