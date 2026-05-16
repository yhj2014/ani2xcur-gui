from ani2xcur.manager.desktop_config import x_cursor


def test_apply_x_cursor_theme_skips_without_display(monkeypatch):
    load_calls = []

    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr(x_cursor, "_load_library", lambda name: load_calls.append(name))

    x_cursor.apply_x_cursor_theme("Bibata", 32)

    assert load_calls == []
