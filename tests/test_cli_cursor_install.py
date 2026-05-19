from pathlib import Path

from typer.testing import CliRunner

from ani2xcur.cli import app as cli_app
from ani2xcur.cli import cursor as cli_cursor


def test_cursor_install_cli_keeps_url_input(monkeypatch, tmp_path: Path):
    input_url = "https://example.com/cursor.zip"
    theme_file = tmp_path / "theme" / "cursor.theme"
    (theme_file.parent / "cursors").mkdir(parents=True)
    theme_file.write_text("[Icon Theme]\nName=test\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_find_desktop_entry_file(
        input_file: Path | str,
        temp_dir: Path,
        depth: int = 0,
        visited: set[Path | str] | None = None,
        is_toplevel: bool = True,
    ) -> Path:
        captured["input_file"] = input_file
        captured["temp_dir"] = temp_dir
        captured["depth"] = depth
        captured["visited"] = visited
        captured["is_toplevel"] = is_toplevel
        return theme_file

    def fake_install_linux_cursor(
        desktop_entry_file: Path,
        cursor_install_path: Path,
    ) -> None:
        captured["desktop_entry_file"] = desktop_entry_file
        captured["cursor_install_path"] = cursor_install_path

    monkeypatch.setattr(cli_cursor.sys, "platform", "linux")
    monkeypatch.setattr(cli_cursor, "find_desktop_entry_file", fake_find_desktop_entry_file)
    monkeypatch.setattr(cli_cursor, "install_linux_cursor", fake_install_linux_cursor)

    result = CliRunner().invoke(cli_app.get_app(), ["cursor", "install", input_url])

    assert result.exit_code == 0, result.exception
    assert captured["input_file"] == input_url
    assert isinstance(captured["input_file"], str)
