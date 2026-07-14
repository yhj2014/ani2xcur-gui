"""主题管理器"""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from ani2xcur.gui import logger


def get_theme_dir() -> Path:
    return Path(__file__).parent.parent / "themes"


def available_themes() -> list[str]:
    theme_dir = get_theme_dir()
    if not theme_dir.exists():
        return ["Light", "Dark"]

    themes = []
    for item in theme_dir.iterdir():
        if item.is_file() and item.suffix == ".qss":
            themes.append(item.stem.capitalize())

    return sorted(themes) if themes else ["Light", "Dark"]


def load_theme(theme_name: str) -> str:
    theme_dir = get_theme_dir()
    theme_file = theme_dir / f"{theme_name.lower()}.qss"

    if not theme_file.exists():
        logger.warning("主题文件不存在: %s，使用默认样式", theme_file)
        return get_default_theme(theme_name)

    try:
        with open(theme_file, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error("加载主题失败: %s", e)
        return get_default_theme(theme_name)


def get_default_theme(theme_name: str) -> str:
    if theme_name.lower() == "dark":
        return _get_dark_theme()
    return _get_light_theme()


def apply_theme(theme_name: str):
    style_sheet = load_theme(theme_name)
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(style_sheet)
        logger.info("主题已切换为: %s", theme_name)


def _get_light_theme() -> str:
    return """
QWidget { font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; font-size: 13px; color: #333; }
QMainWindow { background-color: #f8f9fa; }
QMenuBar { background-color: #e9ecef; padding: 4px 8px; }
QMenuBar::item { padding: 4px 12px; background: transparent; border-radius: 4px; }
QMenuBar::item:hover { background-color: #dee2e6; }
QMenu { background-color: white; border: 1px solid #dee2e6; border-radius: 6px; padding: 4px 0; }
QMenu::item { padding: 6px 24px 6px 20px; }
QMenu::item:hover { background-color: #e9ecef; }
QWidget#sidebar { background-color: #e9ecef; border-right: 1px solid #dee2e6; }
QWidget#tools-sidebar { background-color: #f0f0f0; border-right: 1px solid #ddd; }
QGroupBox { font-weight: bold; border: 1px solid #dee2e6; border-radius: 8px; margin-top: 8px; padding-top: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px; }
QPushButton { padding: 6px 16px; border: 1px solid #ced4da; border-radius: 4px; background-color: white; color: #333; }
QPushButton:hover { background-color: #e9ecef; border-color: #adb5bd; }
QPushButton:disabled { background-color: #e9ecef; color: #adb5bd; border-color: #dee2e6; }
QPushButton#primary-btn { background-color: #2196F3; color: white; border-color: #2196F3; }
QPushButton#primary-btn:hover { background-color: #1976D2; border-color: #1976D2; }
QPushButton#danger-btn { background-color: #dc3545; color: white; border-color: #dc3545; }
QPushButton#danger-btn:hover { background-color: #c82333; border-color: #c82333; }
QLabel { color: #333; }
QLineEdit { padding: 6px 10px; border: 1px solid #ced4da; border-radius: 4px; background-color: white; }
QLineEdit:focus { border-color: #80bdff; outline: none; }
QComboBox { padding: 6px 10px; border: 1px solid #ced4da; border-radius: 4px; background-color: white; min-width: 120px; }
QComboBox:focus { border-color: #80bdff; }
QCheckBox { spacing: 8px; }
QProgressBar { height: 20px; border: 1px solid #ced4da; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background-color: #2196F3; border-radius: 3px; }
QTextEdit { border: 1px solid #ced4da; border-radius: 4px; padding: 8px; }
QListWidget { border: 1px solid #ced4da; border-radius: 4px; }
QListWidget::item { padding: 8px 12px; }
QListWidget::item:hover { background-color: #e9ecef; }
QListWidget::item:selected { background-color: #2196F3; color: white; }
QFrame[frameShape="4"] { color: #dee2e6; }
"""


def _get_dark_theme() -> str:
    return """
QWidget { font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; font-size: 13px; color: #d4d4d4; }
QMainWindow { background-color: #1e1e1e; }
QMenuBar { background-color: #252526; padding: 4px 8px; }
QMenuBar::item { padding: 4px 12px; background: transparent; border-radius: 4px; color: #d4d4d4; }
QMenuBar::item:hover { background-color: #3c3c3c; }
QMenu { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 6px; padding: 4px 0; }
QMenu::item { padding: 6px 24px 6px 20px; color: #d4d4d4; }
QMenu::item:hover { background-color: #3c3c3c; }
QWidget#sidebar { background-color: #252526; border-right: 1px solid #3c3c3c; }
QWidget#tools-sidebar { background-color: #252526; border-right: 1px solid #3c3c3c; }
QGroupBox { font-weight: bold; border: 1px solid #3c3c3c; border-radius: 8px; margin-top: 8px; padding-top: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px; }
QPushButton { padding: 6px 16px; border: 1px solid #3c3c3c; border-radius: 4px; background-color: #2d2d2d; color: #d4d4d4; }
QPushButton:hover { background-color: #3c3c3c; border-color: #4c4c4c; }
QPushButton:disabled { background-color: #2d2d2d; color: #666; border-color: #3c3c3c; }
QPushButton#primary-btn { background-color: #2196F3; color: white; border-color: #2196F3; }
QPushButton#primary-btn:hover { background-color: #1976D2; border-color: #1976D2; }
QPushButton#danger-btn { background-color: #dc3545; color: white; border-color: #dc3545; }
QPushButton#danger-btn:hover { background-color: #c82333; border-color: #c82333; }
QLabel { color: #d4d4d4; }
QLineEdit { padding: 6px 10px; border: 1px solid #3c3c3c; border-radius: 4px; background-color: #2d2d2d; color: #d4d4d4; }
QLineEdit:focus { border-color: #2196F3; outline: none; }
QComboBox { padding: 6px 10px; border: 1px solid #3c3c3c; border-radius: 4px; background-color: #2d2d2d; color: #d4d4d4; min-width: 120px; }
QComboBox:focus { border-color: #2196F3; }
QCheckBox { spacing: 8px; color: #d4d4d4; }
QProgressBar { height: 20px; border: 1px solid #3c3c3c; border-radius: 4px; text-align: center; background-color: #2d2d2d; }
QProgressBar::chunk { background-color: #2196F3; border-radius: 3px; }
QTextEdit { border: 1px solid #3c3c3c; border-radius: 4px; padding: 8px; background-color: #2d2d2d; color: #d4d4d4; }
QListWidget { border: 1px solid #3c3c3c; border-radius: 4px; background-color: #2d2d2d; }
QListWidget::item { padding: 8px 12px; color: #d4d4d4; }
QListWidget::item:hover { background-color: #3c3c3c; }
QListWidget::item:selected { background-color: #2196F3; color: white; }
QFrame[frameShape="4"] { color: #3c3c3c; }
"""
