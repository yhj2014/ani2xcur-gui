import configparser

from ani2xcur.manager.desktop_config import lxqt, x_org


def _set_config_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(lxqt, "LXQT_CONFIG_PATH", tmp_path / "session.conf")
    monkeypatch.setattr(x_org, "X_RESOURCES_PATH", tmp_path / ".Xresources")


def test_set_lxqt_cursor_theme_writes_session_and_xresources(monkeypatch, tmp_path):
    calls = []
    _set_config_paths(monkeypatch, tmp_path)

    def fake_which(name):
        if name in {"xrdb", "xsetroot"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        return None

    monkeypatch.setattr(lxqt.shutil, "which", fake_which)
    monkeypatch.setattr(lxqt, "run_cmd", fake_run_cmd)

    lxqt.set_lxqt_cursor_theme("Bibata")

    config = configparser.ConfigParser()
    config.read(lxqt.LXQT_CONFIG_PATH, encoding="utf-8")

    assert config.get("General", "cursor_theme") == "Bibata"
    assert x_org.X_RESOURCES_PATH.read_text(encoding="utf-8") == "Xcursor.theme: Bibata\n"
    assert calls == [
        ["xrdb", "-merge", str(x_org.X_RESOURCES_PATH)],
        ["xsetroot", "-cursor_name", "left_ptr"],
    ]


def test_set_lxqt_cursor_size_writes_session_and_xresources(monkeypatch, tmp_path):
    calls = []
    _set_config_paths(monkeypatch, tmp_path)

    def fake_which(name):
        if name in {"xrdb", "xsetroot"}:
            return f"/usr/bin/{name}"
        return None

    def fake_run_cmd(command, **kwargs):
        calls.append(command)
        return None

    monkeypatch.setattr(lxqt.shutil, "which", fake_which)
    monkeypatch.setattr(lxqt, "run_cmd", fake_run_cmd)

    lxqt.set_lxqt_cursor_size(32)

    config = configparser.ConfigParser()
    config.read(lxqt.LXQT_CONFIG_PATH, encoding="utf-8")

    assert config.get("General", "cursor_size") == "32"
    assert x_org.X_RESOURCES_PATH.read_text(encoding="utf-8") == "Xcursor.size: 32\n"
    assert calls == [
        ["xrdb", "-merge", str(x_org.X_RESOURCES_PATH)],
        ["xsetroot", "-cursor_name", "left_ptr"],
    ]


def test_get_lxqt_cursor_theme_falls_back_to_xresources(monkeypatch, tmp_path):
    _set_config_paths(monkeypatch, tmp_path)
    x_org.X_RESOURCES_PATH.write_text("Xcursor.theme: Breeze\n", encoding="utf-8")

    assert lxqt.get_lxqt_cursor_theme() == "Breeze"


def test_get_lxqt_cursor_size_returns_none_for_invalid_session_value(monkeypatch, tmp_path):
    _set_config_paths(monkeypatch, tmp_path)
    lxqt.LXQT_CONFIG_PATH.write_text("[General]\ncursor_size=invalid\n", encoding="utf-8")

    assert lxqt.get_lxqt_cursor_size() is None
