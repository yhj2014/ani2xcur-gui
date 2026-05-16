import pytest

from ani2xcur.manager.linux_cur_manager import extract_scheme_info_from_desktop_entry


def _write_cursor_theme(tmp_path, content):
    cursor_dir = tmp_path / "cursors"
    cursor_dir.mkdir()
    (cursor_dir / "left_ptr").write_text("", encoding="utf-8")
    theme_file = tmp_path / "cursor.theme"
    theme_file.write_text(content, encoding="utf-8")
    return theme_file


def test_extract_scheme_info_uses_inherits_when_name_is_missing(tmp_path):
    theme_file = _write_cursor_theme(
        tmp_path,
        "[Icon Theme]\nInherits=DMZ-White\n",
    )

    scheme_info = extract_scheme_info_from_desktop_entry(theme_file)

    assert scheme_info["scheme_name"] == "DMZ-White"


def test_extract_scheme_info_uses_first_inherits_value_when_list(tmp_path):
    theme_file = _write_cursor_theme(
        tmp_path,
        "[Icon Theme]\nInherits=DMZ-White,Adwaita\n",
    )

    scheme_info = extract_scheme_info_from_desktop_entry(theme_file)

    assert scheme_info["scheme_name"] == "DMZ-White"


def test_extract_scheme_info_requires_name_or_inherits(tmp_path):
    theme_file = _write_cursor_theme(
        tmp_path,
        "[Icon Theme]\nComment=missing name\n",
    )

    with pytest.raises(ValueError, match="Inherits"):
        extract_scheme_info_from_desktop_entry(theme_file)
