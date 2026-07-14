# Ani2xcur Code Wiki

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 整体架构](#2-整体架构)
- [3. 核心模块详解](#3-核心模块详解)
  - [3.1 CLI 层 (ani2xcur/cli)](#31-cli-层-ani2xcurcli)
  - [3.2 光标转换模块 (ani2xcur/cursor_conversion)](#32-光标转换模块-ani2xcurcursor_conversion)
  - [3.3 光标管理模块 (ani2xcur/manager)](#33-光标管理模块-ani2xcurmanager)
  - [3.4 配置解析模块 (ani2xcur/config_parse)](#34-配置解析模块-ani2xcurconfig_parse)
  - [3.5 文件操作模块 (ani2xcur/file_operations)](#35-文件操作模块-ani2xcurfile_operations)
  - [3.6 智能查找模块 (ani2xcur/smart_finder.py)](#36-智能查找模块-ani2xcursmart_finderpy)
- [4. 工具模块](#4-工具模块)
  - [4.1 日志模块 (logger.py)](#41-日志模块-loggerpy)
  - [4.2 工具函数 (utils.py)](#42-工具函数-utilspy)
  - [4.3 配置管理 (config.py)](#43-配置管理-configpy)
  - [4.4 下载器 (downloader.py)](#44-下载器-downloaderpy)
  - [4.5 更新器 (updater.py)](#45-更新器-updaterpy)
- [5. 数据结构与类型定义](#5-数据结构与类型定义)
- [6. 依赖关系](#6-依赖关系)
- [7. 项目运行方式](#7-项目运行方式)
- [8. 测试体系](#8-测试体系)
- [9. CI/CD 流程](#9-cicd-流程)

---

## 1. 项目概述

**Ani2xcur** 是一个功能强大的跨平台命令行工具，专门用于鼠标指针主题的管理、转换和安装，支持 Windows 和 Linux 双平台。

### 核心功能

- **双向格式转换**：支持 Windows (.inf/.ani/.cur) ↔ Linux (Xcursor/index.theme) 格式互转
- **指针主题管理**：安装、卸载、设置主题、调整大小、查看信息、导出备份
- **智能识别**：自动在压缩包或目录中查找指针配置文件
- **跨桌面环境**：支持 KDE、Gnome、Xfce、Cinnamon、Mate、LXQt 等多种 Linux 桌面环境
- **ImageMagick 辅助管理**：保留独立的 ImageMagick 安装/卸载命令（当前转换流程不依赖）

### 技术栈

- **语言**：Python 3.10+
- **CLI 框架**：Typer
- **图像处理**：Pillow (PIL)
- **压缩支持**：zstandard, py7zr, rarfile
- **网络请求**：requests
- **进度展示**：tqdm, rich
- **Windows 平台**：pywin32 (仅 Windows)

---

## 2. 整体架构

### 2.1 架构分层

```
┌───────────────────────────────────────────────────┐
│                   CLI 层                          │
│  (cli/app.py, cli/*.py)                           │
│  - 命令解析与参数处理                              │
│  - 用户交互与输出                                  │
└───────────────────┬───────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────┐
│                业务逻辑层                         │
├───────────────────┬───────────────────────────────┤
│  转换模块         │  管理模块                      │
│  (cursor_conver-  │  (manager/)                   │
│   sion/)          │  - Windows 光标管理            │
│  - Win → Xcursor  │  - Linux 光标管理              │
│  - Xcursor → Win  │  - 桌面环境配置                │
│  - 图像处理       │  - 注册表操作                  │
└───────────────────┴───────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────┐
│                基础设施层                         │
├──────────────┬──────────────┬────────────────────┤
│ 配置解析     │ 文件操作     │ 智能查找            │
│ (config_     │ (file_       │ (smart_finder)      │
│  parse/)     │  operations) │                     │
└──────────────┴──────────────┴────────────────────┘
                    │
┌───────────────────▼───────────────────────────────┐
│                工具层                             │
│  logger / utils / config / downloader / updater   │
└───────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
ani2xcur/
├── cli/                    # CLI 命令行接口
│   ├── app.py              # 主应用入口
│   ├── cli.py              # Typer 工厂
│   ├── convert.py          # 转换命令
│   ├── cursor.py           # 光标管理命令
│   ├── image_magick.py     # ImageMagick 管理命令
│   └── system.py           # 系统命令（version/update/env）
├── cursor_conversion/      # 光标转换核心
│   ├── convert.py          # 包级转换入口
│   └── native_cursor/      # 基于 Pillow 的原生转换器
│       ├── models.py       # 数据模型
│       ├── parsers.py      # 格式解析器
│       ├── transforms.py   # 图像变换
│       ├── writers.py      # 格式写入器
│       └── process.py      # 转换流程
├── manager/                # 光标管理
│   ├── base.py             # 基础配置与类型定义
│   ├── win_cur_manager.py  # Windows 光标管理
│   ├── linux_cur_manager.py# Linux 光标管理
│   ├── regedit.py          # 注册表操作封装
│   ├── image_magick_manager.py  # ImageMagick 管理
│   └── desktop_config/     # 桌面环境配置
│       ├── base.py         # 基础工具
│       ├── windows.py      # Windows 配置
│       ├── gnome.py        # Gnome 配置
│       ├── kde.py          # KDE 配置
│       ├── xfce.py         # Xfce 配置
│       ├── cinnamon.py     # Cinnamon 配置
│       ├── mate.py         # Mate 配置
│       ├── lxqt.py         # LXQt 配置
│       ├── gtk.py          # GTK 配置
│       ├── x_org.py        # X.Org 配置
│       ├── xdg.py          # XDG 配置
│       ├── x_cursor.py     # Xcursor 配置
│       └── xsettings.py    # XSettings 配置
├── config_parse/           # 配置文件解析
│   ├── parse.py            # 通用解析
│   ├── win.py              # Windows INF 解析
│   └── linux.py            # Linux Desktop Entry 解析
├── file_operations/        # 文件操作
│   ├── file_manager.py     # 文件管理工具
│   └── archive_manager.py  # 压缩包管理
├── source/                 # 光标补全资源
│   └── (21 个 Xcursor 补全文件)
├── config.py               # 全局配置
├── logger.py               # 日志工具
├── utils.py                # 工具函数
├── smart_finder.py         # 智能查找
├── downloader.py           # 文件下载
├── updater.py              # 自更新
├── version.py              # 版本信息
├── cmd.py                  # 命令执行
└── __main__.py             # 模块入口
```

---

## 3. 核心模块详解

### 3.1 CLI 层 (ani2xcur/cli)

#### 3.1.1 主入口 (app.py)

**文件**：[app.py](file:///workspace/ani2xcur/cli/app.py)

**核心函数**：

- `get_app() -> typer.Typer`：构建并返回完整的 Typer 命令树
- `main() -> None`：主函数，统一异常处理

**命令树结构**：

```
ani2xcur
├── version                # 显示版本信息
├── update                 # 更新 Ani2xcur
├── env                    # 列出环境变量
├── convert                # 鼠标指针转换
│   ├── win2x              # Windows → Linux
│   └── x2win              # Linux → Windows
├── cursor                 # 鼠标指针管理
│   ├── install            # 安装指针
│   ├── uninstall          # 卸载指针
│   ├── export             # 导出指针
│   ├── list               # 列出已安装指针
│   ├── status             # 显示当前指针状态
│   └── set                # 设置指针
│       ├── theme          # 设置主题
│       └── size           # 设置大小
└── imagemagick            # ImageMagick 管理
    ├── install            # 安装 ImageMagick
    └── uninstall          # 卸载 ImageMagick
```

**异常处理策略**：
- `Exit`：正常退出，返回对应退出码
- `Abort`：用户取消操作
- `ClickException`：Typer/Click 内部异常
- `Exception`：通用异常，打印堆栈并退出

---

### 3.2 光标转换模块 (ani2xcur/cursor_conversion)

#### 3.2.1 包级转换入口 (convert.py)

**文件**：[convert.py](file:///workspace/ani2xcur/cursor_conversion/convert.py)

**核心函数**：

| 函数 | 功能 | 关键参数 | 返回值 |
|------|------|---------|--------|
| `win_cursor_to_x11()` | Windows 指针包 → Linux Xcursor 指针包 | `inf_file`: INF 文件路径<br>`output_path`: 输出目录<br>`win2x_args`: 转换参数 | `Path`: 转换后的指针包路径 |
| `x11_cursor_to_win()` | Linux Xcursor 指针包 → Windows 指针包 | `desktop_entry_file`: 主题文件路径<br>`output_path`: 输出目录<br>`x2win_args`: 转换参数 | `Path`: 转换后的指针包路径 |
| `generate_linux_cursor_config()` | 生成 Linux 光标配置文件 (index.theme / cursor.theme) | `cursor_name`: 指针名称<br>`cursor_path`: 保存路径 | `None` |
| `generate_win_cursor_config()` | 生成 Windows 光标配置文件 (AutoSetup.inf) | `cursor_name`: 指针名称<br>`cursor_path`: 保存路径<br>`cursor_save_paths`: 指针文件路径列表 | `None` |

**Windows → Linux 转换流程**：

1. 解析 INF 文件提取指针方案信息
2. 构建转换列表（Windows 键 → Linux 键映射）
3. 逐个转换光标文件（调用 `win2xcur_process`）
4. 补全缺失的光标文件（从 `source/` 目录复制）
5. 创建符号链接（光标别名）
6. 补齐 Xcursor 名义尺寸
7. 生成配置文件 (index.theme / cursor.theme)
8. 生成安装脚本 (install_cursor.sh)
9. 复制到输出目录

**Linux → Windows 转换流程**：

1. 解析 Desktop Entry 文件提取指针方案信息
2. 构建转换列表（Linux 键 → Windows 键映射）
3. 逐个转换光标文件（调用 `x2wincur_process`）
4. 生成 AutoSetup.inf 配置文件
5. 复制到输出目录

---

#### 3.2.2 原生转换器 (native_cursor/)

**模块说明**：基于 Pillow 的纯 Python 光标转换器，不依赖 ImageMagick。

**数据模型** ([models.py](file:///workspace/ani2xcur/cursor_conversion/native_cursor/models.py))：

```python
@dataclass
class CursorImage:
    image: Image.Image      # Pillow 图像对象
    hotspot: tuple[int, int]  # 热点坐标 (x, y)
    nominal: int            # 名义尺寸

@dataclass
class CursorFrame:
    images: list[CursorImage]  # 该帧的多个尺寸图像
    delay: float = 0.0         # 动画延迟（秒）
```

**解析器** ([parsers.py](file:///workspace/ani2xcur/cursor_conversion/native_cursor/parsers.py))：

- `parse_blob(blob: bytes) -> list[CursorFrame]`：自动识别并解析 CUR/ANI/Xcursor 格式

**变换器** ([transforms.py](file:///workspace/ani2xcur/cursor_conversion/native_cursor/transforms.py))：

| 函数 | 功能 |
|------|------|
| `scale_frames(frames, scale)` | 按比例缩放所有帧 |
| `add_shadow_to_frames(frames, color, opacity, radius, sigma, xoffset, yoffset)` | 给光标添加阴影效果 |
| `normalize_xcursor_sizes(frames, target_sizes)` | 补齐 Xcursor 名义尺寸 |

**默认 Xcursor 尺寸**：`[24, 28, 32, 40, 48, 56, 64, 72, 80]`

**写入器** ([writers.py](file:///workspace/ani2xcur/cursor_conversion/native_cursor/writers.py))：

| 函数 | 功能 |
|------|------|
| `to_xcursor(frames) -> bytes` | 写入 Xcursor 格式 |
| `to_smart(frames) -> tuple[str, bytes]` | 智能选择格式（单帧→.cur，多帧→.ani） |

**处理流程** ([process.py](file:///workspace/ani2xcur/cursor_conversion/native_cursor/process.py))：

**Win2xcur 流程**：

```
读取 CUR/ANI 文件 → 解析为帧列表 → 可选缩放 → 可选加阴影 → 补齐尺寸 → 写入 Xcursor
```

**X2wincur 流程**：

```
读取 Xcursor/CUR/ANI 文件 → 解析为帧列表 → 可选缩放 → 智能写入 (CUR 或 ANI)
```

**参数类型**：

```python
class Win2xcurArgs(TypedDict, total=False):
    input_file: Path
    output_path: Path
    save_name: str | None
    shadow: bool | None
    shadow_opacity: int | None
    shadow_radius: float | None
    shadow_sigma: float | None
    shadow_x: float | None
    shadow_y: float | None
    shadow_color: str | None
    scale: float | None
    xcursor_sizes: list[int] | None

class X2wincurArgs(TypedDict, total=False):
    input_file: Path
    output_path: Path
    save_name: str | None
    scale: float | None
```

---

### 3.3 光标管理模块 (ani2xcur/manager)

#### 3.3.1 基础配置 (base.py)

**文件**：[base.py](file:///workspace/ani2xcur/manager/base.py)

**光标类型映射**：

支持 17 种标准光标类型的双向映射：

| Windows 键 | Linux 键 | 说明 |
|-----------|----------|------|
| Arrow | left_ptr | 正常选择 |
| Help | question_arrow | 帮助选择 |
| AppStarting | left_ptr_watch | 后台运行 |
| Wait | wait | 忙 |
| Crosshair | cross | 精确选择 |
| IBeam | xterm | 文本选择 |
| NWPen | pencil | 手写 |
| No | circle | 不可用 |
| SizeNS | bottom_side | 垂直调整 |
| SizeWE | left_side | 水平调整 |
| SizeNWSE | bottom_right_corner | 对角线调整1 |
| SizeNESW | bottom_left_corner | 对角线调整2 |
| SizeAll | move | 移动 |
| UpArrow | dotbox | 候选 |
| Hand | hand2 | 链接选择 |
| Pin | center_ptr | 位置选择 |
| Person | right_ptr | 个人选择 |

**Linux 光标别名链接**：定义了大量软链接别名（如 `default` → `left_ptr`、`watch` → `wait` 等），确保各种应用都能找到对应光标。

**路径常量**：

| 常量 | 值 | 说明 |
|------|----|------|
| `LINUX_ICONS_PATH` | `/usr/share/icons` | 系统图标目录 |
| `LINUX_USER_ICONS_PATH` | `~/.icons` | 用户图标目录 |
| `WINDOWS_USER_CURSOR_PATH` | `~/AppData/Local/Cursors` | Windows 用户光标目录 |

---

#### 3.3.2 Windows 光标管理 (win_cur_manager.py)

**文件**：[win_cur_manager.py](file:///workspace/ani2xcur/manager/win_cur_manager.py)

**核心功能**：

| 函数 | 功能 |
|------|------|
| `extract_scheme_info_from_inf(inf_file)` | 从 INF 文件提取指针方案信息 |
| `list_windows_cursors()` | 列出已安装的光标主题 |
| `set_windows_cursor_theme(cursor_name)` | 设置当前光标主题 |
| `set_windows_cursor_size(cursor_size)` | 设置光标大小 |
| `get_windows_cursor_info()` | 获取当前光标信息 |
| `delete_windows_cursor(cursor_name)` | 删除指定光标主题 |
| `install_windows_cursor(inf_file, cursor_install_path)` | 安装光标主题 |
| `export_windows_cursor(cursor_name, output_path)` | 导出光标主题 |
| `parse_scheme_reg_string(scheme_reg_string)` | 解析 INF 中 Scheme.Reg 格式 |
| `generate_scheme_reg_string(...)` | 生成 Scheme.Reg 格式字符串 |
| `generate_cursor_scheme_inf_string(...)` | 生成完整 INF 文件内容 |
| `generate_cursor_scheme_config(...)` | 生成导出配置字典 |

**Windows 安装流程**：

1. 解析 INF 文件获取方案信息
2. 计算源文件和目标文件路径映射
3. 复制光标文件到目标目录
4. 将方案注册到注册表 (`HKCU\Control Panel\Cursors\Schemes`)

**Windows 删除流程**：

1. 检查光标是否存在且未被使用
2. 计算需要删除的文件（排除其他主题共用的文件）
3. 删除光标文件
4. 清理空目录
5. 从注册表删除方案项

---

#### 3.3.3 Linux 光标管理 (linux_cur_manager.py)

**文件**：[linux_cur_manager.py](file:///workspace/ani2xcur/manager/linux_cur_manager.py)

**核心功能**：

| 函数 | 功能 |
|------|------|
| `extract_scheme_info_from_desktop_entry(file)` | 从 Desktop Entry 提取方案信息 |
| `list_linux_cursors()` | 列出已安装的光标主题 |
| `set_linux_cursor_theme(cursor_name)` | 设置光标主题（所有桌面环境） |
| `set_linux_cursor_size(cursor_size)` | 设置光标大小（所有桌面环境） |
| `get_linux_cursor_info()` | 获取各桌面环境的光标状态 |
| `delete_linux_cursor(cursor_name)` | 删除指定光标主题 |
| `install_linux_cursor(file, install_path)` | 安装光标主题 |
| `export_linux_cursor(name, output_path)` | 导出光标主题 |
| `generate_install_script(name, save_dir)` | 生成安装脚本 |

**Linux 主题设置策略**：

同时写入所有支持的桌面环境配置，确保无论用户使用哪种 DE 都能生效：

- Cinnamon (gsettings)
- Gnome (gsettings)
- GTK 2/3/4 (配置文件)
- KDE (配置文件 + DBus 通知)
- LXQt (配置文件)
- Mate (gsettings)
- X.Org (Xresources)
- XDG (环境变量配置)
- Xfce (xfconf-query)
- XSettings (xsettingsd)

**实时刷新机制**：
- KDE: 通过 DBus 发送 `KGlobalSettings.notifyChange` 信号
- LXQt: 更新环境变量和配置文件
- 其他 DE: 需要重新登录或重启应用生效

---

#### 3.3.4 桌面环境配置 (desktop_config/)

**文件结构**：

| 文件 | 功能 |
|------|------|
| [base.py](file:///workspace/ani2xcur/manager/desktop_config/base.py) | 基础工具、范围检查、会话类型检测 |
| [windows.py](file:///workspace/ani2xcur/manager/desktop_config/windows.py) | Windows 注册表配置 |
| [gnome.py](file:///workspace/ani2xcur/manager/desktop_config/gnome.py) | Gnome 桌面配置 (gsettings) |
| [kde.py](file:///workspace/ani2xcur/manager/desktop_config/kde.py) | KDE 桌面配置 |
| [xfce.py](file:///workspace/ani2xcur/manager/desktop_config/xfce.py) | Xfce 桌面配置 |
| [cinnamon.py](file:///workspace/ani2xcur/manager/desktop_config/cinnamon.py) | Cinnamon 桌面配置 |
| [mate.py](file:///workspace/ani2xcur/manager/desktop_config/mate.py) | Mate 桌面配置 |
| [lxqt.py](file:///workspace/ani2xcur/manager/desktop_config/lxqt.py) | LXQt 桌面配置 |
| [gtk.py](file:///workspace/ani2xcur/manager/desktop_config/gtk.py) | GTK 2/3/4 配置 |
| [x_org.py](file:///workspace/ani2xcur/manager/desktop_config/x_org.py) | X.Org Xresources 配置 |
| [xdg.py](file:///workspace/ani2xcur/manager/desktop_config/xdg.py) | XDG 环境变量配置 |
| [x_cursor.py](file:///workspace/ani2xcur/manager/desktop_config/x_cursor.py) | Xcursor 相关配置 |
| [xsettings.py](file:///workspace/ani2xcur/manager/desktop_config/xsettings.py) | XSettings 守护进程配置 |

**每个桌面环境模块通常提供**：

```python
get_<de>_cursor_theme() -> str | None     # 获取当前主题
get_<de>_cursor_size() -> int | None      # 获取当前大小
set_<de>_cursor_theme(name: str) -> None  # 设置主题
set_<de>_cursor_size(size: int) -> None   # 设置大小
```

**关键值范围**：

| 平台 | 大小范围 | 默认值 |
|------|---------|--------|
| Windows | 1-15 (档位) | 1 |
| Windows CursorBaseSize | 32-256 (步长 16) | 32 |
| Linux | 16-96 (像素) | 24 |

---

#### 3.3.5 注册表操作封装 (regedit.py)

**文件**：[regedit.py](file:///workspace/ani2xcur/manager/regedit.py)

提供跨平台的注册表操作抽象（Windows 上使用 pywin32，Linux 上提供空实现避免导入错误）。

**主要类型**：

```python
class RegistryRootKey(Enum):
    CLASSES_ROOT = ...
    CURRENT_USER = ...
    LOCAL_MACHINE = ...
    USERS = ...
    PERFORMANCE_DATA = ...
    CURRENT_CONFIG = ...

class RegistryAccess(Enum):
    READ = ...
    SET_VALUE = ...
    CREATE_SUB_KEY = ...

class RegistryValueType(Enum):
    SZ = ...              # 字符串
    EXPAND_SZ = ...       # 可扩展字符串
    BINARY = ...          # 二进制
    DWORD = ...           # 32 位数值
    QWORD = ...           # 64 位数值
    MULTI_SZ = ...        # 多字符串
```

---

### 3.4 配置解析模块 (ani2xcur/config_parse)

#### 3.4.1 Windows INF 解析 (win.py)

**核心功能**：

- `parse_inf_file_content(path) -> ParsedINF`：解析 INF 文件
- `dict_to_inf_strings_format(d) -> str`：字典转 INF [Strings] 格式

**INF 解析规则**：
- 支持 `[Section]` 节
- 支持 `key = value` 变量行
- 支持逗号分隔的多值（引号内逗号不分割）
- 支持引号包裹的字符串值
- 忽略以 `;` 或 `//` 开头的注释行
- 忽略全为 `/` 的分隔行

**返回结构**：

```python
ParsedINF = dict[str, INFSection]

class INFSection(TypedDict, total=False):
    var: dict[str, str | list[str]]   # 键值对变量
    constant: list[str]               # 常量行
```

---

#### 3.4.2 Linux Desktop Entry 解析 (linux.py)

解析符合 Freedesktop Icon Theme 规范的 `index.theme` / `cursor.theme` 文件。

---

### 3.5 文件操作模块 (ani2xcur/file_operations)

#### 3.5.1 文件管理 (file_manager.py)

**文件**：[file_manager.py](file:///workspace/ani2xcur/file_operations/file_manager.py)

**核心函数**：

| 函数 | 功能 | 特点 |
|------|------|------|
| `remove_files(path)` | 删除文件/目录 | 支持删除只读文件、非空目录、软链接 |
| `copy_files(src, dst)` | 复制文件/目录 | 保留软链接、目录合并、防循环 |
| `copy_files_merge(src, dst)` | 目录合并复制 | 源目录内容直接合并到目标 |
| `move_files(src, dst)` | 移动文件/目录 | 支持目录合并 |
| `move_files_merge(src, dst)` | 目录合并移动 | 源目录内容直接合并到目标 |
| `get_file_list(path, max_depth, include_dirs)` | 获取文件列表 | 支持深度限制、进度条 |
| `save_create_symlink(target, link)` | 创建软链接 | 失败则回退为复制文件 |
| `safe_is_file(path)` | 检查文件存在 | 大小写不敏感 |
| `get_real_path(path)` | 获取真实路径 | 大小写不敏感匹配 |

**设计要点**：
- 所有操作都有完善的错误处理和日志记录
- 软链接优先保留本身，而非复制指向内容
- Linux 下保留软链接复制失败时自动回退为内容复制
- 防止循环复制/移动（目录复制到自身子目录）

---

#### 3.5.2 压缩包管理 (archive_manager.py)

支持格式：`.zip`, `.7z`, `.rar`, `.tar`, `.tar.Z`, `.tar.lz`, `.tar.lzma`, `.tar.bz2`, `.tar.7z`, `.tar.gz`, `.tar.xz`, `.tar.zst`

**核心函数**：
- `is_supported_archive_format(path)`：检查是否为支持的压缩格式
- `extract_archive(archive_path, extract_to)`：解压压缩包

---

### 3.6 智能查找模块 (ani2xcur/smart_finder.py)

**文件**：[smart_finder.py](file:///workspace/ani2xcur/smart_finder.py)

**核心函数**：

| 函数 | 功能 |
|------|------|
| `find_inf_file(input_file, temp_dir, depth)` | 智能查找 INF 文件 |
| `find_desktop_entry_file(input_file, temp_dir, depth)` | 智能查找 Desktop Entry 文件 |

**支持的输入源**：
- 本地文件路径（.inf / .theme / .ani / .cur）
- 本地目录路径
- 本地压缩包路径
- HTTP/HTTPS 压缩包下载链接

**查找策略**（递归深度优先）：

```
输入 → 判断类型
  ├─ URL → 下载 → 解压 → 递归搜索解压目录
  ├─ 压缩包文件 → 解压 → 递归搜索解压目录
  ├─ 配置文件 (.inf/.theme) → 验证有效性 → 返回
  ├─ 光标文件 (.ani/.cur) → 取父目录继续搜索
  └─ 目录 → 遍历子项 → 递归搜索每一项
```

**防死循环机制**：
- `visited` 集合记录已访问路径
- `depth` 参数控制递归深度
- URL 和 Path 统一去重检查

---

## 4. 工具模块

### 4.1 日志模块 (logger.py)

**文件**：[logger.py](file:///workspace/ani2xcur/logger.py)

**核心组件**：

- `LoggingColoredFormatter`：彩色日志格式化器
  - DEBUG: 青色
  - INFO: 绿色
  - WARNING: 黄色
  - ERROR: 红色
  - CRITICAL: 红底白字

- `get_logger(name, level, color)`：获取日志器
  - 有 name: 格式为 `[name]-|时间|-级别: 消息`
  - 无 name: 格式为 `[模块:函数:行号]-|时间|-级别: 消息`
  - 默认输出到 stdout
  - 单例模式（重复调用不重复添加 handler）

**日志级别控制**：通过环境变量 `ANI2XCUR_LOGGER_LEVEL` 设置

---

### 4.2 工具函数 (utils.py)

**文件**：[utils.py](file:///workspace/ani2xcur/utils.py)

**工具分类**：

| 类别 | 函数 | 功能 |
|------|------|------|
| 类型转换 | `save_convert_to_float(value)` | 安全转浮点数 |
| | `safe_convert_to_int(value)` | 安全转整数 |
| 文件操作 | `open_file_as_bytes(input_file)` | 二进制读文件 |
| | `save_bytes_to_file(data, output_path)` | 二进制写文件 |
| 编码检测 | `is_utf8_bom_encoding_file(path)` | 检测 UTF-8 BOM |
| | `detect_encoding(file_path)` | 检测文件编码 (utf-8/utf-8-sig/gbk) |
| 字典工具 | `lowercase_dict_keys(d)` | 递归转小写键（冲突则保留原键） |
| 列表工具 | `extend_list_to_length(lst, target, fill)` | 扩展列表到指定长度 |
| 权限检测 | `is_admin_on_windows()` | 检测 Windows 管理员权限 |
| | `is_root_on_linux()` | 检测 Linux root 权限 |
| 随机生成 | `generate_random_string(...)` | 生成随机字符串 |
| URL 检测 | `is_http_or_https(url)` | 检测是否为 HTTP/HTTPS 链接 |

---

### 4.3 配置管理 (config.py)

**文件**：[config.py](file:///workspace/ani2xcur/config.py)

所有配置均可通过环境变量覆盖：

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `LOGGER_NAME` | `ANI2XCUR_LOGGER_NAME` | `"Ani2xcur"` | 日志器名称 |
| `LOGGER_LEVEL` | `ANI2XCUR_LOGGER_LEVEL` | `INFO (20)` | 日志级别 |
| `LOGGER_COLOR` | `ANI2XCUR_LOGGER_COLOR` | `True` | 是否启用彩色日志 |
| `ROOT_PATH` | - | 包目录 | 项目根路径 |
| `LINUX_CURSOR_SOURCE_PATH` | - | `ROOT_PATH/source` | 光标补全文件目录 |
| `IMAGE_MAGICK_WINDOWS_DOWNLOAD_URL` | `IMAGE_MAGICK_WINDOWS_DOWNLOAD_URL` | ModelScope 地址 | ImageMagick 下载地址 |
| `IMAGE_MAGICK_WINDOWS_INSTALL_PATH` | - | `Program Files/ImageMagick-7.1.2-Q16-HDRI` | Windows 默认安装路径 |
| `ANI2XCUR_REPOSITORY_URL` | `ANI2XCUR_REPOSITORY_URL` | GitHub 地址 | 仓库地址 |
| `SMART_FINDER_SEARCH_DEPTH` | `ANI2XCUR_SMART_FINDER_SEARCH_DEPTH` | `3` | 智能搜索深度 |

---

### 4.4 下载器 (downloader.py)

**文件**：[downloader.py](file:///workspace/ani2xcur/downloader.py)

**核心函数**：`download_file_from_url(url, save_path)`

功能：从 URL 下载文件，带进度条显示。

---

### 4.5 更新器 (updater.py)

**文件**：[updater.py](file:///workspace/ani2xcur/updater.py)

功能：Ani2xcur 自更新，支持 PyPI 更新和源码安装两种方式。

---

## 5. 数据结构与类型定义

### 5.1 核心类型字典

```python
# 光标文件配对
class CursorFilePair(TypedDict):
    dst_path: Path | None    # 目标路径
    src_path: Path | None    # 源路径

CursorMap = dict[str, CursorFilePair]  # 类型名 → 路径映射

# 本地光标方案
class LocalCursor(TypedDict):
    name: str                    # 方案名称
    cursor_files: list[Path]     # 光标文件列表
    install_paths: list[Path]    # 安装路径列表

CursorSchemesList = list[LocalCursor]

# 当前光标信息
class CurrentCursorInfo(TypedDict):
    platform: str                # 平台/桌面环境名
    cursor_name: str | None      # 光标主题名
    cursor_size: int | None      # 光标大小

CurrentCursorInfoList = list[CurrentCursorInfo]
```

### 5.2 转换参数类型

```python
class Win2xcurArgs(TypedDict, total=False):
    input_file: Path
    output_path: Path
    save_name: str | None
    shadow: bool | None
    shadow_opacity: int | None
    shadow_radius: float | None
    shadow_sigma: float | None
    shadow_x: float | None
    shadow_y: float | None
    shadow_color: str | None
    scale: float | None
    xcursor_sizes: list[int] | None

class X2wincurArgs(TypedDict, total=False):
    input_file: Path
    output_path: Path
    save_name: str | None
    scale: float | None
```

---

## 6. 依赖关系

### 6.1 外部依赖

| 包 | 版本要求 | 用途 |
|----|---------|------|
| Pillow | >=10.0 | 图像解码与处理 |
| typer | >=0.26.7 | CLI 框架 |
| zstandard | - | Zstandard 压缩格式支持 |
| py7zr | - | 7z 压缩格式支持 |
| rarfile | - | RAR 压缩格式支持 |
| requests | - | HTTP 网络请求 |
| tqdm | - | 进度条显示 |
| rich | - | 富文本输出 |
| pywin32 | - (仅 Windows) | Windows 注册表等 API 调用 |

### 6.2 内部模块依赖图

```
cli/app.py
    ├── cli/cli.py (typer_factory)
    ├── cli/convert.py
    │   └── cursor_conversion/convert.py
    │       ├── cursor_conversion/native_cursor/
    │       ├── manager/win_cur_manager.py
    │       ├── manager/linux_cur_manager.py
    │       └── file_operations/file_manager.py
    ├── cli/cursor.py
    │   └── manager/ (win_cur_manager, linux_cur_manager)
    ├── cli/image_magick.py
    │   └── manager/image_magick_manager.py
    └── cli/system.py
        ├── version.py
        ├── updater.py
        └── config.py

manager/
    ├── base.py
    ├── win_cur_manager.py
    │   ├── config_parse/win.py
    │   ├── manager/regedit.py
    │   └── manager/desktop_config/windows.py
    ├── linux_cur_manager.py
    │   ├── config_parse/linux.py
    │   └── manager/desktop_config/*.py (所有 DE)
    └── desktop_config/
        └── base.py (共享工具)

smart_finder.py
    ├── config_parse/win.py
    ├── config_parse/linux.py
    ├── file_operations/archive_manager.py
    ├── file_operations/file_manager.py
    ├── downloader.py
    └── utils.py

几乎所有模块都依赖:
    ├── config.py (全局配置)
    ├── logger.py (日志工具)
    └── utils.py (工具函数)
```

---

## 7. 项目运行方式

### 7.1 环境要求

- Python 3.10+
- pip 或 uv 包管理器

### 7.2 安装方式

**从 PyPI 安装**：

```bash
pip install ani2xcur
```

**从源码安装（开发模式）**：

```bash
git clone <repo-url>
cd ani2xcur
pip install -e .
```

**使用 uv**：

```bash
uv venv
uv pip install -e .
```

### 7.3 运行命令

```bash
# 查看帮助
ani2xcur --help

# Windows 转 Linux
ani2xcur convert win2x <指针路径或下载链接>

# Linux 转 Windows
ani2xcur convert x2win <指针路径或下载链接>

# 安装指针
ani2xcur cursor install <指针路径>

# 设置主题
ani2xcur cursor set theme <主题名>

# 设置大小
ani2xcur cursor set size <大小>

# 查看已安装指针
ani2xcur cursor list

# 查看当前状态
ani2xcur cursor status

# 启用调试日志
ani2xcur --debug <command>
# 或
ANI2XCUR_LOGGER_LEVEL=10 ani2xcur <command>
```

### 7.4 作为模块运行

```bash
python -m ani2xcur --help
```

---

## 8. 测试体系

### 8.1 测试框架

- **框架**：pytest
- **测试目录**：`tests/`
- **配置文件**：`pyproject.toml` 中的 `[tool.pytest.ini_options]`

### 8.2 测试标记

| 标记 | 说明 |
|------|------|
| `integration` | 真实样本转换烟雾测试 |
| `wayland` | 需要 headless Weston 和 libwayland-cursor 的集成测试 |

### 8.3 测试文件一览

| 测试文件 | 测试内容 |
|---------|---------|
| `test_cli_convert_samples.py` | CLI 转换命令集成测试 |
| `test_cli_cursor_install.py` | CLI 光标安装命令测试 |
| `test_cli_debug.py` | CLI 调试日志测试 |
| `test_cursor_conversion_samples.py` | 光标转换样本测试 |
| `test_cursor_manager_samples.py` | 光标管理样本测试 |
| `test_native_cursor_converter.py` | 原生转换器单元测试 |
| `test_cursor_sample_parsing.py` | 光标样本解析测试 |
| `test_cursor_sample_finder_archive.py` | 压缩包智能查找测试 |
| `test_file_manager.py` | 文件管理器测试 |
| `test_kde_config.py` | KDE 配置测试 |
| `test_linux_cursor_config.py` | Linux 光标配置测试 |
| `test_lxqt_config.py` | LXQt 配置测试 |
| `test_mate_config.py` | Mate 配置测试 |
| `test_wayland_cursor_loader.py` | Wayland 光标加载测试 |
| `test_windows_cursor_size.py` | Windows 光标大小测试 |
| `test_x_cursor_config.py` | Xcursor 配置测试 |
| `test_xfce_config.py` | Xfce 配置测试 |
| `test_cmd_logging.py` | 命令日志测试 |

### 8.4 测试样本

`tests/` 目录下包含真实光标样本用于集成测试：

- `DMZ-White-Windows/`：Windows 格式光标 (DMZ-White 主题)
- `DMZ-White-X11/`：Linux Xcursor 格式光标
- `Hiiro-Windows/`：中文命名的 Windows 光标
- `Sunaokami-Shiroko-Windows/`：另一个 Windows 光标主题

### 8.5 运行测试

```bash
# 运行所有非集成测试
pytest -m "not integration"

# 运行集成测试
pytest -m "integration and not wayland"

# 运行 Wayland 测试
ANI2XCUR_REQUIRE_WAYLAND_TEST=1 pytest -m wayland
```

---

## 9. CI/CD 流程

### 9.1 GitHub Actions 工作流

| 工作流文件 | 触发条件 | 功能 |
|-----------|---------|------|
| `lint.yml` | push / PR | Ruff 代码检查 |
| `pytest.yml` | push / PR / 手动 | 单元测试与集成测试 |
| `release.yml` | - | 发布流程 |

### 9.2 Pytest 工作流详解

**测试矩阵**：

- **操作系统**：ubuntu-latest, windows-latest
- **Python 版本**：3.10, 3.11, 3.12, 3.13, 3.14

**三个测试任务**：

1. **test**：单元测试（排除 integration 标记）
   - 所有 OS × Python 版本组合
   - 使用 uv 管理依赖

2. **integration**：集成测试
   - ubuntu-latest + windows-latest
   - Python 3.12
   - 运行 `integration and not wayland` 标记的测试

3. **wayland-loader**：Wayland 光标加载测试
   - 仅 ubuntu-latest
   - Python 3.12
   - 安装 Weston 和 libwayland-dev
   - 运行 `wayland` 标记的测试

---

## 附录：光标补全资源

项目内置 21 个 Xcursor 补全文件（位于 `ani2xcur/source/`），用于转换时填补源主题缺失的光标类型：

| 文件名 | 用途 |
|--------|------|
| bottom_left_corner | 左下/右上对角线缩放 |
| bottom_right_corner | 右下/左上对角线缩放 |
| bottom_side | 垂直缩放 |
| center_ptr | 位置选择 |
| circle | 不可用 |
| cross | 精确选择 |
| dotbox | 候选 |
| hand2 | 链接选择 |
| left_ptr | 正常选择 |
| left_ptr_watch | 后台运行 |
| left_side | 水平缩放 |
| move | 移动 |
| pencil | 手写 |
| question_arrow | 帮助选择 |
| right_ptr | 个人选择 |
| vertical-text | 垂直文本 |
| wait | 忙 |
| wayland-cursor | Wayland 光标标识 |
| xterm | 文本选择 |
| zoom-in | 放大 |
| zoom-out | 缩小 |
