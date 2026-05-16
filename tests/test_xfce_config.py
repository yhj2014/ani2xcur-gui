from ani2xcur.manager.desktop_config import xfce


def test_set_xfce_cursor_theme_creates_missing_property(monkeypatch):
    calls = []

    def fake_which(name):
        if name == "xfconf-query":
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        return None

    monkeypatch.setattr(xfce.shutil, "which", fake_which)
    monkeypatch.setattr(xfce, "run_cmd", fake_run_cmd)

    xfce.set_xfce_cursor_theme("Bibata")

    assert calls == [
        [
            "xfconf-query",
            "--channel",
            "xsettings",
            "--property",
            "/Gtk/CursorThemeName",
            "--create",
            "--type",
            "string",
            "--set",
            "Bibata",
        ]
    ]


def test_set_xfce_cursor_size_creates_missing_property(monkeypatch):
    calls = []

    def fake_which(name):
        if name == "xfconf-query":
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        return None

    monkeypatch.setattr(xfce.shutil, "which", fake_which)
    monkeypatch.setattr(xfce, "run_cmd", fake_run_cmd)

    xfce.set_xfce_cursor_size(32)

    assert calls == [
        [
            "xfconf-query",
            "--channel",
            "xsettings",
            "--property",
            "/Gtk/CursorThemeSize",
            "--create",
            "--type",
            "int",
            "--set",
            "32",
        ]
    ]


def test_get_xfce_cursor_size_returns_none_for_invalid_value(monkeypatch):
    def fake_which(name):
        if name == "xfconf-query":
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        return "invalid\n"

    monkeypatch.setattr(xfce.shutil, "which", fake_which)
    monkeypatch.setattr(xfce, "run_cmd", fake_run_cmd)

    assert xfce.get_xfce_cursor_size() is None
