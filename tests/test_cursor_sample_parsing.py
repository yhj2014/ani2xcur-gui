from pathlib import Path

import pytest

from ani2xcur.config_parse.parse import parse_inf_text
from ani2xcur.config_parse.linux import parse_desktop_entry_content
from ani2xcur.config_parse.win import parse_inf_file_content, preprocess_inf_to_cursor_scheme
from ani2xcur.manager.base import CURSOR_KEYS
from ani2xcur.manager.linux_cur_manager import extract_scheme_info_from_desktop_entry
from ani2xcur.manager.win_cur_manager import extract_scheme_info_from_inf


CUSTOM_SECTION_INF = r"""
[Version]
signature="$CHICAGO$"

[DefaultInstall]
CopyFiles = Cursor.Files
AddReg    = Cursor.Scheme,Cursor.Apply

[DestinationDirs]
Cursor.Files = 10,"%CUR_DIR%"

[Cursor.Scheme]
HKCU,"Control Panel\Cursors\Schemes","%SCHEME_NAME%",0x00020000,"%10%\%CUR_DIR%\%Arrow%,%10%\%CUR_DIR%\%Help%"

[Cursor.Apply]
HKCU,"Control Panel\Cursors",,0x00020000,"%SCHEME_NAME%"

[Cursor.Files]
"Arrow.ani"
"Help.cur"

[Strings]
SCHEME_NAME = "CustomScheme"
CUR_DIR = "Cursors\CustomScheme"
Arrow = "Arrow.ani"
Help = "Help.cur"
""".strip()


def test_parse_real_windows_inf_sample(windows_inf_file: Path, windows_cursor_dir: Path):
    parsed = parse_inf_file_content(windows_inf_file)

    assert parsed["Strings"]["SCHEME_NAME"] == "DMZ-White"
    assert parsed["CursorFilesSection"] == "Scheme.Cur"
    assert len(parsed["CursorFiles"]) == len(CURSOR_KEYS["win"])
    assert parsed["SchemeRegSection"] == "Scheme.Reg"
    assert len(parsed["SchemeReg"]) == 1

    for cursor_file in parsed["CursorFiles"]:
        assert (windows_cursor_dir / cursor_file).is_file()


def test_parse_windows_inf_accepts_defaultinstall_custom_sections(tmp_path: Path):
    inf_file = tmp_path / "Custom.inf"
    inf_file.write_text(CUSTOM_SECTION_INF, encoding="utf-8")
    (tmp_path / "Arrow.ani").write_bytes(b"")
    (tmp_path / "Help.cur").write_bytes(b"")

    parsed = parse_inf_file_content(inf_file)
    scheme_info = extract_scheme_info_from_inf(inf_file)

    assert parsed["CursorFilesSection"] == "Cursor.Files"
    assert parsed["CursorFiles"] == ["Arrow.ani", "Help.cur"]
    assert parsed["CopyFiles"]["Cursor.Files"] == ["Arrow.ani", "Help.cur"]
    assert parsed["SchemeRegSection"] == "Cursor.Scheme"
    assert len(parsed["SchemeReg"]) == 1
    assert parsed["AddReg"]["Cursor.Apply"] == ['HKCU,"Control Panel\\Cursors",,0x00020000,"%SCHEME_NAME%"']
    assert scheme_info["scheme_name"] == "CustomScheme"
    assert scheme_info["cursor_map"]["Arrow"]["src_path"] == tmp_path / "Arrow.ani"
    assert scheme_info["cursor_map"]["Help"]["src_path"] == tmp_path / "Help.cur"


@pytest.mark.parametrize("section_name", ["Version", "DefaultInstall", "DestinationDirs", "Strings"])
def test_parse_windows_inf_requires_core_sections(section_name: str):
    parsed = parse_inf_text(CUSTOM_SECTION_INF)
    parsed.pop(section_name)

    with pytest.raises(ValueError, match=section_name):
        preprocess_inf_to_cursor_scheme(parsed)


@pytest.mark.parametrize("install_key", ["CopyFiles", "AddReg"])
def test_parse_windows_inf_requires_defaultinstall_references(install_key: str):
    parsed = parse_inf_text(CUSTOM_SECTION_INF)
    parsed["DefaultInstall"]["var"].pop(install_key)

    with pytest.raises(ValueError, match=install_key):
        preprocess_inf_to_cursor_scheme(parsed)


def test_extract_real_windows_scheme_info(windows_inf_file: Path):
    scheme_info = extract_scheme_info_from_inf(windows_inf_file)

    assert scheme_info["scheme_name"] == "DMZ-White"
    assert len(scheme_info["cursor_paths"]) == len(CURSOR_KEYS["win"])

    for key in CURSOR_KEYS["win"]:
        cursor_pair = scheme_info["cursor_map"][key]
        assert cursor_pair["src_path"] is not None
        assert cursor_pair["src_path"].is_file()
        assert cursor_pair["src_path"].suffix.lower() in {".cur", ".ani"}
        assert cursor_pair["dst_path"] is not None


def test_parse_real_linux_cursor_theme(linux_theme_file: Path):
    parsed = parse_desktop_entry_content(linux_theme_file)

    assert parsed["Icon Theme"]["Name"] == "DMZ-White"
    assert parsed["Icon Theme"]["Inherits"] == "default"


def test_extract_real_linux_scheme_info(linux_theme_file: Path):
    scheme_info = extract_scheme_info_from_desktop_entry(linux_theme_file)

    assert scheme_info["scheme_name"] == "DMZ-White"
    assert scheme_info["vars_dict"]["Inherits"] == "default"
    assert len(scheme_info["cursor_map"]) == len(CURSOR_KEYS["win"])
    assert scheme_info["cursor_map"]["Arrow"]["src_path"] is not None
    assert scheme_info["cursor_map"]["Arrow"]["src_path"].name == "left_ptr"
    assert scheme_info["cursor_map"]["Wait"]["src_path"] is None
    assert scheme_info["cursor_map"]["Pin"]["src_path"] is None


def test_extract_real_linux_index_theme(linux_cursor_dir: Path):
    scheme_info = extract_scheme_info_from_desktop_entry(linux_cursor_dir / "index.theme")

    assert scheme_info["scheme_name"] == "DMZ (White)"
    assert scheme_info["cursor_map"]["Arrow"]["src_path"] is not None
