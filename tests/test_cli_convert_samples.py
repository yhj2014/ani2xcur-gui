from pathlib import Path

import pytest

from ani2xcur.cli import app as cli_app
from ani2xcur.cli import convert as cli_convert
from ani2xcur.cursor_conversion import convert as cursor_convert


def _fake_win2xcur_process(input_file: Path, output_path: Path, save_name: str | None = None, **kwargs):
    output_file = output_path / (save_name or input_file.stem)
    output_file.write_bytes(b"x11")
    return output_file


def _fake_x2wincur_process(input_file: Path, output_path: Path, save_name: str | None = None, **kwargs):
    output_file = output_path / f"{save_name or input_file.stem}.cur"
    output_file.write_bytes(b"win")
    return output_file


def test_win2xcur_cli_converts_real_sample_without_installing(monkeypatch, windows_cursor_dir: Path, tmp_path: Path):
    monkeypatch.setattr(cursor_convert, "win2xcur_process", _fake_win2xcur_process)

    cli_convert.win2xcur(str(windows_cursor_dir), output_path=tmp_path, install=False)

    assert (tmp_path / "DMZ-White" / "cursor.theme").is_file()
    assert (tmp_path / "DMZ-White" / "cursors" / "left_ptr").is_file()


def test_x2wincur_cli_converts_real_sample_without_installing(monkeypatch, linux_theme_file: Path, tmp_path: Path):
    monkeypatch.setattr(cursor_convert, "x2wincur_process", _fake_x2wincur_process)

    cli_convert.x2wincur(str(linux_theme_file), output_path=tmp_path, install=False)

    assert (tmp_path / "DMZ-White" / "AutoSetup.inf").is_file()
    assert (tmp_path / "DMZ-White" / "Arrow.cur").is_file()


def test_app_main_is_only_sys_exit_boundary(monkeypatch):
    def fake_app():
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_app, "get_app", lambda: fake_app)

    with pytest.raises(SystemExit) as exc_info:
        cli_app.main()

    assert exc_info.value.code == 1
