import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from ani2xcur.file_operations.archive_manager import create_archive, extract_archive
from ani2xcur.config_parse.win import parse_inf_file_content
from ani2xcur.smart_finder import find_desktop_entry_file, find_inf_file


SCHEME_ANI_INF = r"""
[Version]
signature="$CHICAGO$"

[DefaultInstall]
CopyFiles = Scheme.ani
AddReg    = Scheme.Reg,Wreg

[DestinationDirs]
Scheme.ani = 10,"%CUR_DIR%"

[Scheme.Reg]
HKCU,"Control Panel\Cursors\Schemes","%SCHEME_NAME%",0x00020000,"%10%\%CUR_DIR%\%Arrow%,%10%\%CUR_DIR%\%Hand%"

[Wreg]
HKCU,"Control Panel\Cursors",,0x00020000,"%SCHEME_NAME%"

[Scheme.ani]
"Arrow.ani"
"Hand.cur"

[Strings]
SCHEME_NAME = "SchemeAni"
CUR_DIR = "Cursors\SchemeAni"
Arrow = "Arrow.ani"
Hand = "Hand.cur"
""".strip()


def test_find_inf_file_from_real_windows_sample_inputs(windows_cursor_dir: Path, windows_inf_file: Path, tmp_path: Path):
    assert find_inf_file(windows_cursor_dir, tmp_path, depth=1) == windows_inf_file.resolve()
    assert find_inf_file(windows_inf_file, tmp_path, depth=0) == windows_inf_file.resolve()
    assert find_inf_file(windows_cursor_dir / "Arrow.cur", tmp_path, depth=1) == windows_inf_file.resolve()
    assert find_inf_file(windows_cursor_dir / "Wait.ani", tmp_path, depth=1) == windows_inf_file.resolve()
    assert find_inf_file(str(windows_cursor_dir / "Arrow.cur"), tmp_path, depth=1) == windows_inf_file.resolve()


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


def test_find_inf_file_accepts_copyfiles_cursor_section_alias(tmp_path: Path):
    package_dir = tmp_path / "scheme-ani"
    package_dir.mkdir()
    (package_dir / "AutoSetup.inf").write_text(SCHEME_ANI_INF, encoding="utf-8")
    (package_dir / "Arrow.ani").write_bytes(b"")
    (package_dir / "Hand.cur").write_bytes(b"")
    archive_path = tmp_path / "scheme-ani.zip"

    create_archive(package_dir, archive_path)

    found = find_inf_file(archive_path, tmp_path / "finder", depth=3)

    assert found is not None
    assert found.name == "AutoSetup.inf"
    assert parse_inf_file_content(found)["CursorFiles"] == ["Arrow.ani", "Hand.cur"]


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


def test_create_archive_accepts_single_directory_path(windows_cursor_dir: Path, tmp_path: Path):
    archive_path = tmp_path / "single-dir.zip"
    extract_to = tmp_path / "extract-dir"

    create_archive(windows_cursor_dir, archive_path)
    extract_archive(archive_path, extract_to)

    assert (extract_to / windows_cursor_dir.name / "AutoSetup.inf").is_file()


def test_create_archive_accepts_single_file_path(windows_inf_file: Path, tmp_path: Path):
    archive_path = tmp_path / "single-file.zip"
    extract_to = tmp_path / "extract-file"

    create_archive(windows_inf_file, archive_path)
    extract_archive(archive_path, extract_to)

    assert (extract_to / windows_inf_file.name).is_file()


def test_extract_zip_rejects_path_traversal(tmp_path: Path):
    archive_path = tmp_path / "unsafe.zip"
    extract_to = tmp_path / "extract-zip"

    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("../outside.txt", "unsafe")

    with pytest.raises(ValueError, match="不安全"):
        extract_archive(archive_path, extract_to)

    assert not (tmp_path / "outside.txt").exists()


def test_extract_tar_rejects_path_traversal(tmp_path: Path):
    archive_path = tmp_path / "unsafe.tar"
    extract_to = tmp_path / "extract-tar"
    data = b"unsafe"

    with tarfile.open(archive_path, "w") as tar_ref:
        member = tarfile.TarInfo("../outside.txt")
        member.size = len(data)
        tar_ref.addfile(member, io.BytesIO(data))

    with pytest.raises(ValueError, match="不安全"):
        extract_archive(archive_path, extract_to)

    assert not (tmp_path / "outside.txt").exists()
