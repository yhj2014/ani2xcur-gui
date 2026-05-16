import shutil
from pathlib import Path

from ani2xcur.config_parse.win import parse_inf_file_content
from ani2xcur.manager import linux_cur_manager, win_cur_manager
from ani2xcur.manager.base import CURSOR_KEYS
from ani2xcur.manager.regedit import RegistryValueType


def _windows_scheme_value(windows_cursor_dir: Path) -> str:
    files_by_stem = {path.stem: path for path in windows_cursor_dir.iterdir() if path.suffix.lower() in {".cur", ".ani"}}
    return ",".join(str(files_by_stem[key]) for key in CURSOR_KEYS["win"])


def test_install_linux_cursor_copies_real_theme(tmp_sample_copy, linux_cursor_dir: Path, tmp_path: Path):
    sample_dir = tmp_sample_copy(linux_cursor_dir)
    install_root = tmp_path / "icons"

    linux_cur_manager.install_linux_cursor(sample_dir / "cursor.theme", install_root)

    installed_dir = install_root / "DMZ-White"
    assert (installed_dir / "cursor.theme").is_file()
    assert (installed_dir / "cursors" / "left_ptr").is_file()


def test_list_export_and_delete_linux_cursor_with_real_theme(monkeypatch, tmp_sample_copy, linux_cursor_dir: Path, tmp_path: Path):
    sample_dir = tmp_sample_copy(linux_cursor_dir)
    user_icons = tmp_path / "user-icons"
    system_icons = tmp_path / "system-icons"
    installed_dir = user_icons / "DMZ-White"
    shutil.copytree(sample_dir, installed_dir)
    system_icons.mkdir()

    monkeypatch.setattr(linux_cur_manager, "LINUX_USER_ICONS_PATH", user_icons)
    monkeypatch.setattr(linux_cur_manager, "LINUX_ICONS_PATH", system_icons)

    cursors = linux_cur_manager.list_linux_cursors()
    assert [cursor["name"] for cursor in cursors] == ["DMZ-White"]

    exported_dir = linux_cur_manager.export_linux_cursor("DMZ-White", tmp_path / "exports")
    assert (exported_dir / "cursor.theme").is_file()
    assert (exported_dir / "install_cursor.sh").is_file()

    linux_cur_manager.delete_linux_cursor("DMZ-White")
    assert not installed_dir.exists()


def test_list_windows_cursors_reads_mock_registry_paths(monkeypatch, windows_cursor_dir: Path):
    scheme_value = _windows_scheme_value(windows_cursor_dir)

    monkeypatch.setattr(win_cur_manager, "registry_enum_values", lambda **kwargs: {"DMZ-White": scheme_value})

    cursors = win_cur_manager.list_windows_cursors()

    assert len(cursors) == 1
    assert cursors[0]["name"] == "DMZ-White"
    assert len(cursors[0]["cursor_files"]) == len(CURSOR_KEYS["win"])


def test_install_windows_cursor_copies_real_files_and_registers_scheme(monkeypatch, windows_inf_file: Path, tmp_path: Path):
    registry_calls = []

    def fake_registry_set_value(**kwargs):
        registry_calls.append(kwargs)

    monkeypatch.setattr(win_cur_manager, "registry_set_value", fake_registry_set_value)

    install_root = tmp_path / "windows-cursors"
    win_cur_manager.install_windows_cursor(windows_inf_file, install_root)

    installed_dir = install_root / "DMZ-White"
    for key in CURSOR_KEYS["win"]:
        assert any((installed_dir / f"{key}{suffix}").is_file() for suffix in [".cur", ".ani"])

    assert len(registry_calls) == 1
    assert registry_calls[0]["name"] == "DMZ-White"
    assert registry_calls[0]["reg_type"] == RegistryValueType.SZ


def test_export_windows_cursor_copies_real_files_and_writes_inf(monkeypatch, windows_cursor_dir: Path, tmp_path: Path):
    scheme_value = _windows_scheme_value(windows_cursor_dir)

    monkeypatch.setattr(win_cur_manager, "registry_enum_values", lambda **kwargs: {"DMZ-White": scheme_value})
    monkeypatch.setattr(win_cur_manager, "registry_query_value", lambda **kwargs: scheme_value)

    exported_dir = win_cur_manager.export_windows_cursor("DMZ-White", tmp_path / "exports")
    parsed = parse_inf_file_content(exported_dir / "AutoSetup.inf")

    assert parsed["Strings"]["SCHEME_NAME"] == "DMZ-White"
    assert len(parsed["Scheme.Cur"]) == len(CURSOR_KEYS["win"])
    assert (exported_dir / "Arrow.cur").is_file()
    assert (exported_dir / "Wait.ani").is_file()


def test_delete_windows_cursor_removes_files_and_registry_value(monkeypatch, windows_cursor_dir: Path, tmp_path: Path):
    installed_dir = tmp_path / "windows-cursors" / "DMZ-White"
    installed_dir.mkdir(parents=True)
    cursor_files = []
    for name in ["Arrow.cur", "Help.cur"]:
        cursor_file = installed_dir / name
        shutil.copy2(windows_cursor_dir / name, cursor_file)
        cursor_files.append(cursor_file)

    registry_calls = []

    monkeypatch.setattr(
        win_cur_manager,
        "list_windows_cursors",
        lambda: [{"name": "DMZ-White", "cursor_files": cursor_files, "install_paths": [installed_dir]}],
    )
    monkeypatch.setattr(win_cur_manager, "get_windows_cursor_theme", lambda: "Other")
    monkeypatch.setattr(win_cur_manager, "registry_delete_value", lambda **kwargs: registry_calls.append(kwargs))

    win_cur_manager.delete_windows_cursor("DMZ-White")

    assert not installed_dir.exists()
    assert registry_calls[0]["name"] == "DMZ-White"
