"""日志查看器"""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
)
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QTextCursor, QFont

from ani2xcur.gui import logger as root_logger


class _LogBridge(QObject):
    log_received = Signal(str, int)


class LogViewer(QWidget):
    """日志查看器"""

    MAX_LINES = 2000
    log_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_handler = None
        self._current_level = logging.INFO
        self._log_bridge = _LogBridge()
        self._log_bridge.log_received.connect(self._on_log_received)
        self._init_ui()
        self._install_handler()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(QLabel("级别:"))
        self._level_combo = QComboBox()
        self._level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_combo.setCurrentText("INFO")
        self._level_combo.currentTextChanged.connect(self._on_level_changed)
        toolbar.addWidget(self._level_combo)
        toolbar.addStretch()
        self._clear_btn = QPushButton("清空")
        self._clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(self._clear_btn)
        layout.addLayout(toolbar)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setLineWrapMode(QTextEdit.NoWrap)
        font = QFont("Menlo")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(9)
        self._text_edit.setFont(font)
        self._text_edit.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #333; }")
        layout.addWidget(self._text_edit, 1)

    def _install_handler(self):
        try:
            self._log_handler = _QtLogHandler(self._log_bridge)
            self._log_handler.setFormatter(
                logging.Formatter(fmt="[%(name)s]-|%(asctime)s|-%(levelname)s: %(message)s", datefmt="%H:%M:%S")
            )
            root_logger.addHandler(self._log_handler)
        except Exception as e:
            root_logger.warning("安装日志 Handler 失败: %s", e)

    def _on_level_changed(self, level_text: str):
        self._current_level = getattr(logging, level_text, logging.INFO)

    def _on_log_received(self, message: str, level: int):
        self._append_log(message, level)

    def _append_log(self, message: str, level: int):
        if level < self._current_level:
            return
        color = self._level_color(level)
        html = f'<span style="color: {color};">{self._escape_html(message)}</span>'
        self._text_edit.append(html)
        if self._text_edit.document().blockCount() > self.MAX_LINES:
            cursor = self._text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.deleteChar()
        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._text_edit.setTextCursor(cursor)

    def _level_color(self, level: int) -> str:
        if level >= logging.CRITICAL:
            return "#ff6b6b"
        elif level >= logging.ERROR:
            return "#ff8a80"
        elif level >= logging.WARNING:
            return "#ffd54f"
        elif level >= logging.INFO:
            return "#81c784"
        return "#90a4ae"

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def clear_log(self):
        self._text_edit.clear()
        self.log_cleared.emit()

    def closeEvent(self, event):
        if self._log_handler is not None:
            try:
                root_logger.removeHandler(self._log_handler)
            except Exception:
                pass
        super().closeEvent(event)


class _QtLogHandler(logging.Handler):
    def __init__(self, bridge: _LogBridge):
        super().__init__()
        self._bridge = bridge

    def emit(self, record):
        try:
            msg = self.format(record)
            self._bridge.log_received.emit(msg, record.levelno)
        except Exception:
            self.handleError(record)
