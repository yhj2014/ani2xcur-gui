from ani2xcur.manager.desktop_config import x_cursor


def test_apply_x_cursor_theme_skips_without_display(monkeypatch):
    load_calls = []

    monkeypatch.setattr(x_cursor.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr(x_cursor, "_load_library", lambda name: load_calls.append(name))

    x_cursor.apply_x_cursor_theme("Bibata", 32)

    assert load_calls == []


def test_apply_x_cursor_theme_skips_on_wayland_session(monkeypatch):
    load_calls = []

    monkeypatch.setattr(x_cursor.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setattr(x_cursor, "_load_library", lambda name: load_calls.append(name))

    x_cursor.apply_x_cursor_theme("Bibata", 32)

    assert load_calls == []


def test_apply_x_cursor_theme_skips_on_wayland_display_without_session_type(monkeypatch):
    load_calls = []

    monkeypatch.setattr(x_cursor.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.setattr(x_cursor, "_load_library", lambda name: load_calls.append(name))

    x_cursor.apply_x_cursor_theme("Bibata", 32)

    assert load_calls == []


def test_apply_x_cursor_theme_uses_display_on_explicit_x11_session(monkeypatch):
    load_calls = []

    monkeypatch.setattr(x_cursor.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setattr(x_cursor, "_load_library", lambda name: load_calls.append(name))

    x_cursor.apply_x_cursor_theme("Bibata", 32)

    assert load_calls == ["X11", "Xcursor", "Xfixes"]


def test_iter_cursor_names_includes_installed_theme_files(monkeypatch, tmp_path):
    cursors_dir = tmp_path / "icons" / "Bibata" / "cursors"
    cursors_dir.mkdir(parents=True)
    (cursors_dir / "left_ptr").write_bytes(b"cursor")
    (cursors_dir / "kde_custom_cursor").write_bytes(b"cursor")

    monkeypatch.setattr(x_cursor, "_XCURSOR_THEME_PATHS", (tmp_path / "icons",))

    names = list(x_cursor._iter_cursor_names("Bibata"))

    assert "left_ptr" in names
    assert "dnd-copy" in names
    assert "kde_custom_cursor" in names
    assert names.count("left_ptr") == 1
