from pathlib import Path

from ani2xcur.config_parse.linux import parse_desktop_entry_content
from ani2xcur.config_parse.win import parse_inf_file_content
from ani2xcur.manager.base import CURSOR_KEYS
from ani2xcur.manager.linux_cur_manager import extract_scheme_info_from_desktop_entry
from ani2xcur.manager.win_cur_manager import extract_scheme_info_from_inf


def test_parse_real_windows_inf_sample(windows_inf_file: Path, windows_cursor_dir: Path):
    parsed = parse_inf_file_content(windows_inf_file)

    assert parsed["Strings"]["SCHEME_NAME"] == "DMZ-White"
    assert len(parsed["Scheme.Cur"]) == len(CURSOR_KEYS["win"])
    assert len(parsed["Scheme.Reg"]) == 1

    for cursor_file in parsed["Scheme.Cur"]:
        assert (windows_cursor_dir / cursor_file).is_file()


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
    assert parsed["Icon Theme"]["Inherits"] == "DMZ-White"


def test_extract_real_linux_scheme_info(linux_theme_file: Path):
    scheme_info = extract_scheme_info_from_desktop_entry(linux_theme_file)

    assert scheme_info["scheme_name"] == "DMZ-White"
    assert scheme_info["vars_dict"]["Inherits"] == "DMZ-White"
    assert len(scheme_info["cursor_map"]) == len(CURSOR_KEYS["win"])
    assert scheme_info["cursor_map"]["Arrow"]["src_path"] is not None
    assert scheme_info["cursor_map"]["Arrow"]["src_path"].name == "left_ptr"
    assert scheme_info["cursor_map"]["Wait"]["src_path"] is None
    assert scheme_info["cursor_map"]["Pin"]["src_path"] is None


def test_extract_real_linux_index_theme(linux_cursor_dir: Path):
    scheme_info = extract_scheme_info_from_desktop_entry(linux_cursor_dir / "index.theme")

    assert scheme_info["scheme_name"] == "DMZ (White)"
    assert scheme_info["cursor_map"]["Arrow"]["src_path"] is not None
