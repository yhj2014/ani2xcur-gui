"""Windows 鼠标指针配置解析"""

from pathlib import Path
from typing import (
    Any,
    Literal,
    Protocol,
    TypedDict,
)

from ani2xcur.config_parse.parse import (
    ParsedINF,
    parse_inf_file,
)


CursorShemeINF = TypedDict(
    "CursorShemeINF",
    {
        "Version": dict[str, str | list[str]],  # 版本信息
        "DefaultInstall": dict[str, list[str]],  # 默认需要安装的配置
        "DestinationDirs": dict[str, str | list[str]],  # 目的路径
        "Scheme.Reg": list[str],  # 鼠标指针方案在注册表中的存储位置
        "Wreg": list[str],  # 当前应用的鼠标指针设置
        "Scheme.Cur": list[str],  # 需要复制到系统中的光标文件名列表
        "Strings": dict[str, str],  # 配置中使用的变量
    },
    total=False,
)
"""预处理后的鼠标指针配置 INF 结构"""

INFSectionName = Literal[
    "Version",  # 版本信息
    "DefaultInstall",  # 默认需要安装的配置
    "DestinationDirs",  # 目的路径
    "Scheme.Reg",  # 鼠标指针方案在注册表中的存储位置
    "Scheme.Cur",  # 需要复制到系统中的光标文件名列表
    "Wreg",  # 当前应用的鼠标指针设置
    "Strings",  # 配置中使用的变量
]
"""INF 文件已知键名"""


class INFSectionDict(Protocol):
    """INF 选项结构字典"""

    def get(  # pylint: disable=missing-function-docstring
        self,
        key: Literal["var", "constant"],
        default: Any = ...,
    ) -> str | dict[str, str | list[str]] | Any:
        """获取 INF 节中的指定字段。

        Args:
            key: 要获取的字段名
            default: 字段不存在时返回的默认值
        Returns:
            str | dict[str, str | list[str]] | Any: 字段值或默认值
        """
        ...


class KnownINFSections(Protocol):
    """已知的 INF 结构"""

    def __getitem__(
        self,
        key: INFSectionName,
    ) -> INFSectionDict: ...
    def __contains__(
        self,
        key: object,
    ) -> bool: ...


def _section_var(
    parsed: ParsedINF,
    section_name: str,
) -> dict[str, str | list[str]]:
    """获取指定节中的变量映射，并保留解析器返回的具体类型。"""
    return parsed[section_name].get("var", {})


def _section_constant(
    parsed: ParsedINF,
    section_name: str,
) -> list[str]:
    """获取指定节中的常量行列表，并保留解析器返回的具体类型。"""
    return parsed[section_name].get("constant", [])


def _ensure_str_dict(
    data: dict[str, str | list[str]],
    section_name: str,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(value, str):
            raise ValueError(f"{section_name} 中的 {key} 必须为字符串")
        result[key] = value
    return result


def preprocess_inf_to_cursor_scheme(
    parsed: ParsedINF,
) -> CursorShemeINF:
    """将 ParsedINF 处理为鼠标指针已知键的扁平结构

    返回包含常见节的字典:
    - Version: 该节的 var & constant 原样返回 (若存在)
    - DefaultInstall: 各键保证为 list[str]
    - DestinationDirs: 直接返回 var 映射 (值可能为 str 或 list[str])
    - Scheme.Reg: Scheme.Reg 节的常量行列表
    - Wreg: Wreg 节的常量行列表
    - Scheme.Cur: Scheme.Cur 节的常量行列表
    - Strings: Strings 节的 var 映射

    Args:
        parsed (ParsedINF): INF 类型字典
    Returns:
        CursorShemeINF: 预处理后的鼠标指针 INF 信息字典
    Raises:
        ValueError: 当鼠标指针配置文件不完整时
    """

    def _ensure_list(
        v: str | list[str],
    ) -> list[str]:
        return v if isinstance(v, list) else [v]

    out: CursorShemeINF = {}

    if "Version" in parsed:
        out["Version"] = _section_var(parsed, "Version")

    if "DefaultInstall" in parsed:
        di: dict[str, list[str]] = {}
        for k, v in _section_var(parsed, "DefaultInstall").items():
            di[k] = _ensure_list(v)
        out["DefaultInstall"] = di

    if "DestinationDirs" in parsed:
        out["DestinationDirs"] = _section_var(parsed, "DestinationDirs")

    # 一些节在不同 INF 中可能为 var 或 constant，这里以常见样式提取
    if "Scheme.Reg" in parsed:
        out["Scheme.Reg"] = _section_constant(parsed, "Scheme.Reg")
    else:
        raise ValueError("未找到 Scheme.Reg 键, 鼠标指针配置不完整")

    if "Wreg" in parsed:
        out["Wreg"] = _section_constant(parsed, "Wreg")

    if "Scheme.Cur" in parsed:
        out["Scheme.Cur"] = _section_constant(parsed, "Scheme.Cur")
    else:
        raise ValueError("未找到 Scheme.Cur 键, 鼠标指针配置不完整")

    if "Strings" in parsed:
        out["Strings"] = _ensure_str_dict(_section_var(parsed, "Strings"), "Strings")
    else:
        raise ValueError("未找到 Strings 键, 鼠标指针配置不完整")

    return out


def parse_inf_file_content(
    inf_path: Path,
) -> CursorShemeINF:
    """从 INF 文件中获取鼠标指针配置数据

    Args:
        inf_path (Path): 鼠标指针的 INF 配置文件
    Returns:
        CursorShemeINF: 鼠标指针配置数据
    Raises:
        ValueError: 当鼠标指针配置文件不完整时
    """
    inf = parse_inf_file(inf_path)
    try:
        return preprocess_inf_to_cursor_scheme(inf)
    except ValueError as e:
        raise e


def dict_to_inf_strings_format(
    data_dict: dict[str, str],
    indent_width: int = 12,
) -> str:
    """将字典转换为 INF 文件 [Strings] 部分的格式
    
    Args:
        data_dict (dict[str, str]): 包含键值对的字典
        indent_width (int): 缩进宽度, 默认为 12 个空格
    Returns:
        str: 格式化的字符串
    """
    lines = []
    for key, value in data_dict.items():
        # 使用制表符或空格对齐，保持与原格式一致
        separator = "\t\t" if len(key) < indent_width else "\t"
        line = f'{key}{separator}= "{value}"'
        lines.append(line)

    return "\n".join(lines)
