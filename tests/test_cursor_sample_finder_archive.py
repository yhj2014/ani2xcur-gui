from pathlib import Path

from ani2xcur.file_operations.archive_manager import create_archive, extract_archive
from ani2xcur.smart_finder import find_desktop_entry_file, find_inf_file


def test_find_inf_file_from_real_windows_sample_inputs(windows_cursor_dir: Path, windows_inf_file: Path, tmp_path: Path):
    assert find_inf_file(windows_cursor_dir, tmp_path, depth=1) == windows_inf_file.resolve()
    assert find_inf_file(windows_inf_file, tmp_path, depth=0) == windows_inf_file.resolve()
    assert find_inf_file(windows_cursor_dir / "Arrow.cur", tmp_path, depth=1) == windows_inf_file.resolve()
    assert find_inf_file(windows_cursor_dir / "Wait.ani", tmp_path, depth=1) == windows_inf_file.resolve()


def test_find_desktop_entry_file_from_real_linux_sample_inputs(linux_cursor_dir: Path, linux_theme_file: Path, tmp_path: Path):
    found_from_dir = find_desktop_entry_file(linux_cursor_dir, tmp_path, depth=1)

    assert found_from_dir is not None
    assert found_from_dir.parent == linux_cursor_dir.resolve()
    assert found_from_dir.name in {"cursor.theme", "index.theme"}
    assert find_desktop_entry_file(linux_theme_file, tmp_path, depth=0) == linux_theme_file.resolve()
    assert find_desktop_entry_file(linux_cursor_dir / "index.theme", tmp_path, depth=0) == (linux_cursor_dir / "index.theme").resolve()


def test_archive_roundtrip_and_find_inf_file(windows_cursor_dir: Path, tmp_path: Path):
    archive_path = tmp_path / "windows-cursors.zip"
    extract_to = tmp_path / "extract"
    finder_temp = tmp_path / "finder"

    create_archive([windows_cursor_dir], archive_path)
    extract_archive(archive_path, extract_to)

    assert (extract_to / windows_cursor_dir.name / "AutoSetup.inf").is_file()

    found = find_inf_file(archive_path, finder_temp, depth=3)

    assert found is not None
    assert found.name == "AutoSetup.inf"


def test_archive_roundtrip_and_find_desktop_entry_file(linux_cursor_dir: Path, tmp_path: Path):
    archive_path = tmp_path / "linux-cursors.tar"
    extract_to = tmp_path / "extract"
    finder_temp = tmp_path / "finder"

    create_archive([linux_cursor_dir], archive_path)
    extract_archive(archive_path, extract_to)

    assert (extract_to / linux_cursor_dir.name / "cursor.theme").is_file()

    found = find_desktop_entry_file(archive_path, finder_temp, depth=3)

    assert found is not None
    assert found.name in {"cursor.theme", "index.theme"}
