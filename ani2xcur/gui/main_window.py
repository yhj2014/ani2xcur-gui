"""主窗口"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from ani2xcur.gui.utils.theme_manager import apply_theme


class MainWindow(QMainWindow):
    """主窗口 - 侧边栏导航 + 页面堆栈"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_window()
        self._init_menu()
        self._init_ui()

    def _init_window(self):
        self.setWindowTitle("Ani2xcur GUI")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

    def _init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("视图")
        from ani2xcur.gui.utils.theme_manager import available_themes
        theme_menu = view_menu.addMenu("主题")
        for theme_name in available_themes():
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, t=theme_name: apply_theme(t))
            theme_menu.addAction(action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(160)
        sidebar_layout = QHBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(
            "QListWidget { border: none; background: transparent; }"
            "QListWidget::item { padding: 10px 14px; border-radius: 6px; margin: 2px 0; }"
            "QListWidget::item:hover { background-color: rgba(0,0,0,0.06); }"
            "QListWidget::item:selected { background-color: #2196F3; color: white; }"
        )

        pages_info = [("转换", 0), ("管理", 1), ("工具", 2), ("设置", 3)]
        for name, idx in pages_info:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, idx)
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)
        layout.addWidget(sidebar)

        self.stack = QStackedWidget()

        from ani2xcur.gui.views.convert_page import ConvertPage
        from ani2xcur.gui.views.manage_page import ManagePage
        from ani2xcur.gui.views.tools_page import ToolsPage
        from ani2xcur.gui.views.settings_page import SettingsPage

        self.convert_page = ConvertPage()
        self.manage_page = ManagePage()
        self.tools_page = ToolsPage()
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.convert_page)
        self.stack.addWidget(self.manage_page)
        self.stack.addWidget(self.tools_page)
        self.stack.addWidget(self.settings_page)

        layout.addWidget(self.stack, 1)
        self.settings_page.theme_changed.connect(apply_theme)

    def _on_nav_changed(self, row):
        item = self.nav_list.item(row)
        if item is not None:
            self.stack.setCurrentIndex(item.data(Qt.UserRole))

    def _show_about(self):
        from PySide6.QtWidgets import QMessageBox
        from ani2xcur.version import VERSION
        QMessageBox.about(
            self,
            "关于 Ani2xcur GUI",
            f"<h3>Ani2xcur GUI v{VERSION}</h3>"
            "<p>跨平台光标转换与管理工具</p>"
            "<p>支持 Windows ↔ Linux 双向转换</p>",
        )
