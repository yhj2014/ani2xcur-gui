"""GUI 启动入口"""

import sys
import logging

logger = logging.getLogger(__name__)


def _print_error(message: str):
    try:
        sys.stderr.write(f"{message}\n")
        sys.stderr.flush()
    except Exception:
        pass


def run_gui() -> int:
    """启动 GUI 应用程序，返回退出码"""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        logger.error("无法启动 GUI: 缺少 PySide6 依赖")
        _print_error(
            "错误: 缺少 PySide6 依赖。\n"
            "请重新安装 ain2xcur-gui:\n"
            "  pip install ain2xcur-gui\n"
            "或直接安装 PySide6:\n"
            "  pip install PySide6"
        )
        return 1

    try:
        from PySide6.QtCore import Qt

        if hasattr(Qt, "AA_EnableHighDpiScaling"):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        app.setApplicationName("Ani2xcur GUI")
        app.setApplicationDisplayName("Ani2xcur GUI")
        app.setOrganizationName("ain2xcur-gui")

        from ani2xcur.gui.utils.theme_manager import apply_theme
        apply_theme("Light")

        from ani2xcur.gui.main_window import MainWindow
        window = MainWindow()
        window.show()

        logger.info("GUI 应用已启动")
        return app.exec()

    except Exception as e:
        logger.error("GUI 启动失败: %s", e, exc_info=True)
        _print_error(f"GUI 启动失败: {e}")
        return 1
