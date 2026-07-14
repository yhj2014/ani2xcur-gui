"""光标管理页面"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGroupBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QSpinBox,
    QFileDialog,
    QDialog,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ani2xcur.gui.models.cursor_info import CursorSchemeInfo


class ManagePage(QWidget):
    """光标管理页面"""

    list_requested = Signal()
    install_requested = Signal()
    uninstall_requested = Signal()
    export_requested = Signal()
    set_theme_requested = Signal()
    set_size_requested = Signal()
    status_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("光标管理")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        status_group = QGroupBox("当前状态")
        status_layout = QHBoxLayout(status_group)
        self.status_label = QLabel("未检测")
        self.status_label.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.status_label)
        self.refresh_status_btn = QPushButton("刷新状态")
        self.refresh_status_btn.clicked.connect(self.status_requested.emit)
        status_layout.addWidget(self.refresh_status_btn)
        layout.addWidget(status_group)

        list_group = QGroupBox("已安装光标")
        list_layout = QVBoxLayout(list_group)
        self.cursor_list = QListWidget()
        self.cursor_list.setSelectionMode(QListWidget.SingleSelection)
        list_layout.addWidget(self.cursor_list)
        list_btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.list_requested.emit)
        list_btn_layout.addWidget(self.refresh_btn)
        list_btn_layout.addStretch()
        list_layout.addLayout(list_btn_layout)
        layout.addWidget(list_group)

        actions_group = QGroupBox("操作")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(8)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("设置主题:"))
        self.theme_name_edit = QLineEdit()
        self.theme_name_edit.setPlaceholderText("光标主题名称")
        theme_layout.addWidget(self.theme_name_edit, 1)
        self.set_theme_btn = QPushButton("应用")
        self.set_theme_btn.clicked.connect(self._on_set_theme)
        theme_layout.addWidget(self.set_theme_btn)
        actions_layout.addLayout(theme_layout)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("设置大小:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 256)
        self.size_spin.setValue(24)
        size_layout.addWidget(self.size_spin)
        self.set_size_btn = QPushButton("应用")
        self.set_size_btn.clicked.connect(lambda: self.set_size_requested.emit())
        size_layout.addWidget(self.set_size_btn)
        size_layout.addStretch()
        actions_layout.addLayout(size_layout)

        cursor_actions = QHBoxLayout()
        self.install_btn = QPushButton("安装光标")
        self.install_btn.clicked.connect(self.install_requested.emit)
        cursor_actions.addWidget(self.install_btn)
        self.uninstall_btn = QPushButton("卸载选中")
        self.uninstall_btn.clicked.connect(self._on_uninstall)
        cursor_actions.addWidget(self.uninstall_btn)
        self.export_btn = QPushButton("导出选中")
        self.export_btn.clicked.connect(self._on_export)
        cursor_actions.addWidget(self.export_btn)
        cursor_actions.addStretch()
        actions_layout.addLayout(cursor_actions)

        layout.addWidget(actions_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet("color: gray;")
        layout.addWidget(self.msg_label)

        layout.addStretch()

    def _on_set_theme(self):
        name = self.theme_name_edit.text().strip()
        if name:
            self.set_theme_requested.emit()
        else:
            self.show_error("请输入主题名称")

    def _on_uninstall(self):
        item = self.cursor_list.currentItem()
        if item is None:
            self.show_error("请先选择要卸载的光标")
            return
        self.uninstall_requested.emit()

    def _on_export(self):
        item = self.cursor_list.currentItem()
        if item is None:
            self.show_error("请先选择要导出的光标")
            return
        self.export_requested.emit()

    def set_busy(self, busy: bool):
        self.refresh_btn.setEnabled(not busy)
        self.install_btn.setEnabled(not busy)
        self.uninstall_btn.setEnabled(not busy)
        self.export_btn.setEnabled(not busy)
        self.set_theme_btn.setEnabled(not busy)
        self.set_size_btn.setEnabled(not busy)
        self.refresh_status_btn.setEnabled(not busy)

    def update_progress(self, percent: int, message: str):
        self.progress_bar.setValue(percent)
        self.msg_label.setText(message)

    def update_cursor_list(self, cursors: list[CursorSchemeInfo]):
        self.cursor_list.clear()
        for cursor in cursors:
            item = QListWidgetItem(cursor.name)
            item.setData(Qt.UserRole, cursor)
            self.cursor_list.addItem(item)

    def update_cursor_status(self, statuses):
        if statuses:
            parts = []
            for s in statuses:
                text = s.cursor_name or "未知"
                if s.cursor_size:
                    text += f" ({s.cursor_size}px)"
                parts.append(text)
            self.status_label.setText(" | ".join(parts))
            self.status_label.setStyleSheet("font-size: 14px; color: #2e7d32;")
        else:
            self.status_label.setText("无法获取")
            self.status_label.setStyleSheet("font-size: 14px; color: #c62828;")

    def show_error(self, message: str):
        self.msg_label.setText(f"错误: {message}")
        self.msg_label.setStyleSheet("color: #c62828;")

    def show_info(self, message: str):
        self.msg_label.setText(message)
        self.msg_label.setStyleSheet("color: #2e7d32;")

    def get_selected_cursor_name(self) -> str:
        item = self.cursor_list.currentItem()
        if item:
            cursor = item.data(Qt.UserRole)
            return cursor.name if cursor else ""
        return ""


class InstallDialog(QDialog):
    """安装对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("安装光标")
        self.setMinimumWidth(450)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("输入路径:"))
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择光标文件包...")
        input_layout.addWidget(self.input_edit, 1)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse)
        input_layout.addWidget(self.browse_btn)
        layout.addLayout(input_layout)

        install_layout = QHBoxLayout()
        install_layout.addWidget(QLabel("安装路径:"))
        self.install_edit = QLineEdit()
        self.install_edit.setPlaceholderText("默认路径")
        install_layout.addWidget(self.install_edit, 1)
        layout.addLayout(install_layout)

        self.use_inf_check = QCheckBox("使用 INF 配置的安装路径")
        self.use_inf_check.setChecked(True)
        layout.addWidget(self.use_inf_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择光标目录")
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "选择光标文件")
        if path:
            self.input_edit.setText(path)


class ExportDialog(QDialog):
    """导出对话框"""

    def __init__(self, cursor_name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出光标")
        self.setMinimumWidth(400)
        self._cursor_name = cursor_name
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(QLabel(f"导出光标: {self._cursor_name}"))

        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_edit = QLineEdit()
        output_layout.addWidget(self.output_edit, 1)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse)
        output_layout.addWidget(self.browse_btn)
        layout.addLayout(output_layout)

        self.compress_check = QCheckBox("打包为压缩文件")
        self.compress_check.setChecked(True)
        layout.addWidget(self.compress_check)

        self.format_combo = QComboBox()
        self.format_combo.addItems([".7z", ".zip", ".tar.gz"])
        layout.addWidget(self.format_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_edit.setText(path)
