from ani2xcur.manager.desktop_config import mate


def test_set_mate_cursor_size_uses_gsettings_set(monkeypatch):
    calls = []

    monkeypatch.setattr(mate.shutil, "which", lambda name: f"/usr/bin/{name}" if name == "gsettings" else None)
    monkeypatch.setattr(mate, "run_cmd", lambda command, **kwargs: calls.append(command))

    mate.set_mate_cursor_size(32)

    assert calls == [
        ["gsettings", "set", "org.mate.peripherals-mouse", "cursor-size", "32"],
    ]
