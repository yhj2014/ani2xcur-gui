"""转换选项数据模型"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversionOptions:
    """光标转换选项"""

    input_path: str = ""
    output_path: str = ""
    direction: str = "win2x"
    win2x_cursor_size: int = 32
    win2x_cursor_scale: list[int] = field(default_factory=lambda: [1])
    win2x_use_xcursor_default: bool = False
    x2win_cursor_size: int = 32
    x2win_animated_cursor_delay: int = 50
    x2win_static_cursor_delay: int = 0
    x2win_cursor_scale: list[int] = field(default_factory=lambda: [1])
    auto_install: bool = False
    install_path: str = ""
    compress: bool = False
    compress_format: str = ".7z"
    use_inf_config_path: bool = True

    def to_win2x_args(self) -> dict[str, Any]:
        return {
            "cursor_size": self.win2x_cursor_size,
            "cursor_scale": self.win2x_cursor_scale,
            "use_xcursor_default": self.win2x_use_xcursor_default,
        }

    def to_x2win_args(self) -> dict[str, Any]:
        return {
            "cursor_size": self.x2win_cursor_size,
            "animated_cursor_delay": self.x2win_animated_cursor_delay,
            "static_cursor_delay": self.x2win_static_cursor_delay,
            "cursor_scale": self.x2win_cursor_scale,
        }
