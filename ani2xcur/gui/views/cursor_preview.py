"""光标预览组件"""

from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QFont, QImage

from ani2xcur.gui import logger


class CursorPreview(QWidget):
    """光标图像预览控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cursor_path: Path | None = None
        self._preview_size = 64
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setMinimumSize(120, 120)
        self._image_label.setFrameShape(QFrame.StyledPanel)
        self._image_label.setStyleSheet("QLabel { background-color: #f5f5f5; border: 1px solid #ddd; }")

        self._name_label = QLabel("-")
        self._name_label.setAlignment(Qt.AlignCenter)
        self._name_label.setStyleSheet("color: gray; font-size: 11px;")

        layout.addWidget(self._image_label, 1)
        layout.addWidget(self._name_label)

    def set_cursor_file(self, path):
        if path is None:
            self._cursor_path = None
            self._image_label.clear()
            self._name_label.setText("-")
            self._render_placeholder()
            return

        self._cursor_path = Path(path)
        self._name_label.setText(self._cursor_path.name)

        try:
            self._load_and_render()
        except Exception as e:
            logger.warning("预览光标文件失败: %s - %s", path, e)
            self._render_placeholder("预览失败")

    def _load_and_render(self):
        if self._cursor_path is None:
            return

        suffix = self._cursor_path.suffix.lower()
        pixmap = None

        if suffix in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
            pixmap = QPixmap(str(self._cursor_path))
        elif suffix in (".cur", ".ani", ".ico"):
            pixmap = self._load_with_pillow()
        else:
            self._render_placeholder("不支持预览")
            return

        if pixmap is not None and not pixmap.isNull():
            scaled = pixmap.scaled(self._preview_size, self._preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._image_label.setPixmap(scaled)
        else:
            self._render_placeholder("无法预览")

    def _load_with_pillow(self):
        try:
            from PIL import Image
            img = Image.open(str(self._cursor_path))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.thumbnail((self._preview_size * 2, self._preview_size * 2))
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimg)
        except ImportError:
            return None
        except Exception as e:
            logger.debug("Pillow 加载失败: %s", e)
            return None

    def _render_placeholder(self, text: str = "无预览"):
        pixmap = QPixmap(self._preview_size, self._preview_size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.gray)
        painter.drawRect(0, 0, self._preview_size - 1, self._preview_size - 1)
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(0, 0, self._preview_size, self._preview_size, Qt.AlignCenter, text)
        painter.end()
        self._image_label.setPixmap(pixmap)

    def clear(self):
        self.set_cursor_file(None)

    def sizeHint(self) -> QSize:
        return QSize(120, 140)
