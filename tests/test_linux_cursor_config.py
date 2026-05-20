import pytest

from ani2xcur.manager import linux_cur_manager
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


def _patch_linux_cursor_theme_setters(monkeypatch):
    calls = []
    setter_names = [
        "set_cinnamon_cursor_theme",
        "set_gnome_cursor_theme",
        "set_gtk2_cursor_theme",
        "set_gtk3_cursor_theme",
        "set_gtk4_cursor_theme",
        "set_kde_cursor_theme",
        "set_lxqt_cursor_theme",
        "set_mate_cursor_theme",
        "set_x_resources_cursor_theme",
        "set_xdg_cursor_theme",
        "set_xfce_cursor_theme",
        "set_gtk_xsettings_cursor_theme",
    ]
    for setter_name in setter_names:
        monkeypatch.setattr(linux_cur_manager, setter_name, lambda value, setter_name=setter_name: calls.append(setter_name))
    return calls


def _patch_linux_cursor_size_setters(monkeypatch):
    calls = []
    setter_names = [
        "set_cinnamon_cursor_size",
        "set_gnome_cursor_size",
        "set_gtk2_cursor_size",
        "set_gtk3_cursor_size",
        "set_gtk4_cursor_size",
        "set_kde_cursor_size",
        "set_lxqt_cursor_size",
        "set_mate_cursor_size",
        "set_x_resources_cursor_size",
        "set_xfce_cursor_size",
        "set_gtk_xsettings_cursor_size",
    ]
    for setter_name in setter_names:
        monkeypatch.setattr(linux_cur_manager, setter_name, lambda value, setter_name=setter_name: calls.append(setter_name))
    return calls


def _set_kde_wayland_env(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "plasmawayland")
    monkeypatch.setenv("DESKTOP_SESSION", "plasmawayland")
    monkeypatch.setenv("GDMSESSION", "plasmawayland")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":0")


def test_set_linux_cursor_theme_writes_all_desktop_configs_on_wayland(monkeypatch):
    calls = _patch_linux_cursor_theme_setters(monkeypatch)
    _set_kde_wayland_env(monkeypatch)
    monkeypatch.setattr(linux_cur_manager, "list_linux_cursors", lambda: [{"name": "Blue", "cursor_files": [], "install_paths": []}])
    monkeypatch.setattr(linux_cur_manager, "_get_live_cursor_size", lambda: 32)
    monkeypatch.setattr(linux_cur_manager, "refresh_lxqt_cursor_session", lambda name, size: calls.append("refresh_lxqt_cursor_session"))
    monkeypatch.setattr(linux_cur_manager, "refresh_kde_cursor_session", lambda name, size: calls.append("refresh_kde_cursor_session"))

    linux_cur_manager.set_linux_cursor_theme("Blue")

    assert calls == [
        "set_cinnamon_cursor_theme",
        "set_gnome_cursor_theme",
        "set_gtk2_cursor_theme",
        "set_gtk3_cursor_theme",
        "set_gtk4_cursor_theme",
        "set_kde_cursor_theme",
        "set_lxqt_cursor_theme",
        "set_mate_cursor_theme",
        "set_x_resources_cursor_theme",
        "set_xdg_cursor_theme",
        "set_xfce_cursor_theme",
        "set_gtk_xsettings_cursor_theme",
        "refresh_lxqt_cursor_session",
        "refresh_kde_cursor_session",
    ]


def test_set_linux_cursor_size_writes_all_desktop_configs_on_wayland(monkeypatch):
    calls = _patch_linux_cursor_size_setters(monkeypatch)
    _set_kde_wayland_env(monkeypatch)
    monkeypatch.setattr(linux_cur_manager, "_get_live_cursor_theme", lambda: "Blue")
    monkeypatch.setattr(linux_cur_manager, "refresh_lxqt_cursor_session", lambda name, size: calls.append("refresh_lxqt_cursor_session"))
    monkeypatch.setattr(linux_cur_manager, "refresh_kde_cursor_session", lambda name, size: calls.append("refresh_kde_cursor_session"))

    linux_cur_manager.set_linux_cursor_size(32)

    assert calls == [
        "set_cinnamon_cursor_size",
        "set_gnome_cursor_size",
        "set_gtk2_cursor_size",
        "set_gtk3_cursor_size",
        "set_gtk4_cursor_size",
        "set_kde_cursor_size",
        "set_lxqt_cursor_size",
        "set_mate_cursor_size",
        "set_x_resources_cursor_size",
        "set_xfce_cursor_size",
        "set_gtk_xsettings_cursor_size",
        "refresh_lxqt_cursor_session",
        "refresh_kde_cursor_session",
    ]


def test_set_linux_cursor_size_refreshes_kde_even_without_live_theme(monkeypatch):
    calls = _patch_linux_cursor_size_setters(monkeypatch)
    _set_kde_wayland_env(monkeypatch)
    monkeypatch.setattr(linux_cur_manager, "_get_live_cursor_theme", lambda: None)
    monkeypatch.setattr(linux_cur_manager, "refresh_lxqt_cursor_session", lambda name, size: calls.append(("refresh_lxqt_cursor_session", name, size)))
    monkeypatch.setattr(linux_cur_manager, "refresh_kde_cursor_session", lambda name, size: calls.append(("refresh_kde_cursor_session", name, size)))

    linux_cur_manager.set_linux_cursor_size(32)

    assert calls[-2:] == [
        ("refresh_lxqt_cursor_session", None, 32),
        ("refresh_kde_cursor_session", None, 32),
    ]
