"""设置页面"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGroupBox,
    QComboBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ani2xcur.gui.utils import available_themes


class SettingsPage(QWidget):
    """设置页面"""

    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("设置")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        appearance_group = QGroupBox("外观")
        appearance_layout = QVBoxLayout(appearance_group)
        appearance_layout.setSpacing(10)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(available_themes())
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)

        hint = QLabel("选择应用程序的外观主题")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        appearance_layout.addWidget(hint)
        layout.addWidget(appearance_group)

        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        from ani2xcur.version import VERSION
        about_label = QLabel(
            f"<h3>Ani2xcur GUI v{VERSION}</h3>"
            "<p>跨平台光标转换与管理工具</p>"
            "<p style='color: gray; font-size: 11px;'>支持 Windows ↔ Linux 双向转换</p>"
        )
        about_label.setTextFormat(Qt.RichText)
        about_layout.addWidget(about_label)
        layout.addWidget(about_group)
        layout.addStretch()

    def _on_theme_changed(self, theme_name: str):
        self.theme_changed.emit(theme_name)

    def current_theme(self) -> str:
        return self.theme_combo.currentText()

    def set_current_theme(self, theme_name: str):
        self.theme_combo.blockSignals(True)
        index = self.theme_combo.findText(theme_name)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.blockSignals(False)
