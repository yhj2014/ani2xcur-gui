"""光标信息数据模型"""

from dataclasses import dataclass


@dataclass
class CursorSchemeInfo:
    """光标方案信息"""
    name: str = ""
    cursor_files: list[str] = None
    install_paths: list[str] = None

    def __post_init__(self):
        if self.cursor_files is None:
            self.cursor_files = []
        if self.install_paths is None:
            self.install_paths = []


@dataclass
class CurrentCursorStatus:
    """当前光标状态"""
    platform: str = ""
    cursor_name: str | None = None
    cursor_size: int | None = None


@dataclass
class ManageAction:
    """管理操作"""
    action: str = ""
    input_path: str = ""
    output_path: str = ""
    cursor_name: str = ""
    cursor_size: int = 24
    install_path: str = ""
    use_inf_config_path: bool = True
    compress: bool = False
    compress_format: str = ".7z"
