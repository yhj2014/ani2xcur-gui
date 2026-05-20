from ani2xcur.manager.desktop_config import kde


def test_get_kde_cursor_theme_prefers_plasma_6(monkeypatch):
    calls = []

    def fake_which(name):
        if name in {"kreadconfig5", "kreadconfig6"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        return "Breeze\n"

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)

    assert kde.get_kde_cursor_theme() == "Breeze"
    assert calls[0][0] == "kreadconfig6"


def test_set_kde_cursor_theme_writes_config_without_refresh(monkeypatch):
    calls = []
    x_calls = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def fake_which(name):
        if name in {"kwriteconfig6", "plasma-apply-cursortheme"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        return None

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kde, "apply_x_cursor_theme", lambda name, size=None: x_calls.append((name, size)))

    kde.set_kde_cursor_theme("MyCursor")

    assert calls == [
        ["kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", "MyCursor"],
    ]
    assert x_calls == []


def test_set_kde_cursor_theme_does_not_refresh_when_writeconfig_is_missing(monkeypatch):
    calls = []
    x_calls = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def fake_which(name):
        if name == "plasma-apply-cursortheme":
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        return None

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kde, "apply_x_cursor_theme", lambda name, size=None: x_calls.append((name, size)))

    kde.set_kde_cursor_theme("MyCursor")

    assert calls == []
    assert x_calls == []


def test_refresh_kde_cursor_session_uses_kde_x11_helpers(monkeypatch):
    calls = []
    x_calls = []
    root_envs = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def fake_which(name):
        if name in {"kwriteconfig6", "kreadconfig6", "plasma-apply-cursortheme", "dbus-send", "xsetroot"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        if command[0] == "kreadconfig6":
            return "32\n"
        if command[0] == "xsetroot":
            root_envs.append(kwargs.get("custom_env"))
        return None

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kde, "apply_x_cursor_theme", lambda name, size=None: x_calls.append((name, size)))

    kde.refresh_kde_cursor_session("MyCursor", 32)

    assert calls == [
        ["plasma-apply-cursortheme", "MyCursor"],
        ["plasma-apply-cursortheme", "MyCursor", "--size", "32"],
        [
            "dbus-send",
            "--session",
            "--type=signal",
            "/KGlobalSettings",
            "org.kde.KGlobalSettings.notifyChange",
            "int32:5",
            "int32:0",
        ],
        ["xsetroot", "-cursor_name", "left_ptr"],
    ]
    assert x_calls == [("MyCursor", 32)]
    assert root_envs[0]["XCURSOR_THEME"] == "MyCursor"
    assert root_envs[0]["XCURSOR_SIZE"] == "32"


def test_refresh_kde_cursor_session_can_apply_size_without_theme_name(monkeypatch):
    calls = []
    x_calls = []
    root_envs = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def fake_which(name):
        if name in {"plasma-apply-cursortheme", "dbus-send", "xsetroot"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        if command[0] == "xsetroot":
            root_envs.append(kwargs.get("custom_env"))
        return None

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kde, "apply_x_cursor_theme", lambda name, size=None: x_calls.append((name, size)))

    kde.refresh_kde_cursor_session(None, 32)

    assert calls == [
        [
            "dbus-send",
            "--session",
            "--type=signal",
            "/KGlobalSettings",
            "org.kde.KGlobalSettings.notifyChange",
            "int32:5",
            "int32:0",
        ],
        ["xsetroot", "-cursor_name", "left_ptr"],
    ]
    assert x_calls == [(None, 32)]
    assert root_envs[0]["XCURSOR_SIZE"] == "32"
    assert "XCURSOR_THEME" not in root_envs[0]


def test_set_kde_cursor_size_refreshes_current_theme(monkeypatch):
    calls = []
    x_calls = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def fake_which(name):
        if name in {"kwriteconfig6", "kreadconfig6", "plasma-apply-cursortheme"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        if command[0] == "kreadconfig6":
            return "Breeze\n"
        return None

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kde, "apply_x_cursor_theme", lambda name, size=None: x_calls.append((name, size)))

    kde.set_kde_cursor_size(32)

    assert calls == [
        ["kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorSize", "32"],
    ]
    assert x_calls == []


def test_refresh_kde_cursor_session_on_wayland_uses_plasma_apply_without_x11_refresh(monkeypatch):
    calls = []
    x_calls = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":0")

    def fake_which(name):
        if name in {"kwriteconfig5", "kreadconfig5", "plasma-apply-cursortheme", "dbus-send"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        if command[0] == "kreadconfig5":
            return "24\n"
        return None

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kde, "apply_x_cursor_theme", lambda name, size=None: x_calls.append((name, size)))

    kde.refresh_kde_cursor_session("Blue", 24)

    assert calls == [
        ["plasma-apply-cursortheme", "Blue"],
        ["plasma-apply-cursortheme", "Blue", "--size", "24"],
        [
            "dbus-send",
            "--session",
            "--type=signal",
            "/KGlobalSettings",
            "org.kde.KGlobalSettings.notifyChange",
            "int32:5",
            "int32:0",
        ],
    ]
    assert x_calls == []


def test_set_kde_cursor_theme_on_wayland_writes_config_without_refresh(monkeypatch):
    calls = []
    x_calls = []
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":0")

    def fake_which(name):
        if name in {"kwriteconfig5", "kreadconfig5", "plasma-apply-cursortheme", "dbus-send"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        if command[0] == "kreadconfig5":
            return "Blue\n"
        return None

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kde, "apply_x_cursor_theme", lambda name, size=None: x_calls.append((name, size)))

    kde.set_kde_cursor_theme("Blue")

    assert calls == [
        ["kwriteconfig5", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", "Blue"],
    ]
    assert x_calls == []


def test_get_kde_cursor_size_returns_none_for_invalid_value(monkeypatch):
    def fake_which(name):
        if name == "kreadconfig6":
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        return "invalid\n"

    monkeypatch.setattr(kde.shutil, "which", fake_which)
    monkeypatch.setattr(kde, "run_cmd", fake_run_cmd)

    assert kde.get_kde_cursor_size() is None
