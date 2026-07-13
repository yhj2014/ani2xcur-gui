"""工具页面"""

import sys

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGroupBox,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ani2xcur.gui import logger
from ani2xcur.gui.views.log_viewer import LogViewer


class ToolsPage(QWidget):
    """工具页面"""

    install_im_requested = Signal()
    uninstall_im_requested = Signal()
    check_im_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._create_sidebar(layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_im_page())
        self.stacked_widget.addWidget(self._create_log_page())
        layout.addWidget(self.stacked_widget, 1)

    def _create_sidebar(self, parent_layout):
        sidebar = QFrame()
        sidebar.setObjectName("tools-sidebar")
        sidebar.setFixedWidth(140)
        sidebar.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #ddd;")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(4)

        self.tool_list = QListWidget()
        self.tool_list.setStyleSheet(
            "QListWidget { border: none; background: transparent; }"
            "QListWidget::item { padding: 8px 12px; border-radius: 4px; }"
            "QListWidget::item:hover { background-color: #e0e0e0; }"
            "QListWidget::item:selected { background-color: #2196F3; color: white; }"
        )

        im_item = QListWidgetItem("ImageMagick")
        im_item.setData(Qt.UserRole, 0)
        self.tool_list.addItem(im_item)

        log_item = QListWidgetItem("日志查看器")
        log_item.setData(Qt.UserRole, 1)
        self.tool_list.addItem(log_item)

        self.tool_list.setCurrentRow(0)
        self.tool_list.currentRowChanged.connect(self._on_tool_changed)
        sidebar_layout.addWidget(self.tool_list)
        sidebar_layout.addStretch()
        parent_layout.addWidget(sidebar)

    def _create_im_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("ImageMagick 管理")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        status_group = QGroupBox("状态")
        status_layout = QVBoxLayout(status_group)
        self.im_status_label = QLabel("检测中...")
        self.im_status_label.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.im_status_label)
        im_desc = QLabel("ImageMagick 用于处理高质量光标图像。\n如未安装，将使用 Pillow 替代。")
        im_desc.setStyleSheet("color: gray; font-size: 11px;")
        status_layout.addWidget(im_desc)
        layout.addWidget(status_group)

        actions_group = QGroupBox("操作")
        actions_layout = QHBoxLayout(actions_group)
        self.im_install_btn = QPushButton("安装 ImageMagick")
        self.im_install_btn.clicked.connect(self.install_im_requested.emit)
        actions_layout.addWidget(self.im_install_btn)
        self.im_uninstall_btn = QPushButton("卸载 ImageMagick")
        self.im_uninstall_btn.clicked.connect(self.uninstall_im_requested.emit)
        actions_layout.addWidget(self.im_uninstall_btn)
        self.im_check_btn = QPushButton("重新检测")
        self.im_check_btn.clicked.connect(self.check_im_requested.emit)
        actions_layout.addWidget(self.im_check_btn)
        actions_layout.addStretch()
        layout.addWidget(actions_group)

        self.im_progress_bar = QProgressBar()
        self.im_progress_bar.setValue(0)
        self.im_progress_bar.setVisible(False)
        layout.addWidget(self.im_progress_bar)
        layout.addStretch()
        return page

    def _create_log_page(self) -> QWidget:
        self.log_viewer = LogViewer()
        return self.log_viewer

    def _on_tool_changed(self, row):
        item = self.tool_list.item(row)
        if item is None:
            return
        self.stacked_widget.setCurrentIndex(item.data(Qt.UserRole))

    def update_im_status(self, installed: bool, version_info: str = ""):
        if installed:
            status = "已安装" + (f" - {version_info}" if version_info else "")
            self.im_status_label.setText(f"✅ {status}")
            self.im_status_label.setStyleSheet("font-size: 14px; color: #2e7d32;")
            self.im_install_btn.setEnabled(False)
            self.im_uninstall_btn.setEnabled(True)
        else:
            self.im_status_label.setText("❌ 未安装")
            self.im_status_label.setStyleSheet("font-size: 14px; color: #c62828;")
            self.im_install_btn.setEnabled(True)
            self.im_uninstall_btn.setEnabled(False)

    def set_im_busy(self, is_busy: bool, message: str = ""):
        self.im_install_btn.setEnabled(not is_busy)
        self.im_uninstall_btn.setEnabled(not is_busy)
        self.im_check_btn.setEnabled(not is_busy)
        self.im_progress_bar.setVisible(is_busy)
        if is_busy and message:
            self.im_status_label.setText(message)
