"""转换页面"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QFileDialog,
    QSpinBox,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


class ConvertPage(QWidget):
    """光标转换页面"""

    convert_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("光标转换")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        direction_group = QGroupBox("转换方向")
        direction_layout = QHBoxLayout(direction_group)
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Windows → Linux", "Linux → Windows"])
        direction_layout.addWidget(self.direction_combo)
        direction_layout.addStretch()
        layout.addWidget(direction_group)

        input_group = QGroupBox("输入")
        input_layout = QHBoxLayout(input_group)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择输入文件或目录...")
        input_layout.addWidget(self.input_edit, 1)
        self.input_browse_btn = QPushButton("浏览...")
        self.input_browse_btn.clicked.connect(self._browse_input)
        input_layout.addWidget(self.input_browse_btn)
        layout.addWidget(input_group)

        output_group = QGroupBox("输出")
        output_layout = QHBoxLayout(output_group)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("输出目录（默认与输入同目录）")
        output_layout.addWidget(self.output_edit, 1)
        self.output_browse_btn = QPushButton("浏览...")
        self.output_browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.output_browse_btn)
        layout.addWidget(output_group)

        params_group = QGroupBox("参数")
        params_layout = QVBoxLayout(params_group)
        params_layout.setSpacing(8)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("光标大小:"))
        self.cursor_size_spin = QSpinBox()
        self.cursor_size_spin.setRange(1, 256)
        self.cursor_size_spin.setValue(32)
        size_layout.addWidget(self.cursor_size_spin)
        size_layout.addStretch()
        params_layout.addLayout(size_layout)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("缩放:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["1x", "1.5x", "2x"])
        scale_layout.addWidget(self.scale_combo)
        scale_layout.addStretch()
        params_layout.addLayout(scale_layout)

        self.auto_install_check = QCheckBox("转换后自动安装")
        params_layout.addWidget(self.auto_install_check)
        self.compress_check = QCheckBox("打包为压缩文件")
        params_layout.addWidget(self.compress_check)

        layout.addWidget(params_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setObjectName("primary-btn")
        self.convert_btn.clicked.connect(self.convert_requested.emit)
        btn_layout.addWidget(self.convert_btn)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "选择输入文件")
        if path:
            self.input_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_edit.setText(path)

    def set_busy(self, busy: bool):
        self.convert_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)
        self.input_browse_btn.setEnabled(not busy)
        self.output_browse_btn.setEnabled(not busy)

    def update_progress(self, percent: int, message: str):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def show_error(self, message: str):
        self.status_label.setText(f"错误: {message}")
        self.status_label.setStyleSheet("color: #c62828;")

    def show_info(self, message: str):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #2e7d32;")

    def get_direction(self) -> str:
        return "win2x" if self.direction_combo.currentIndex() == 0 else "x2win"
