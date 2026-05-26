import os

import pytest

from ani2xcur.file_operations.file_manager import (
    copy_files,
    copy_files_merge,
    move_files,
    move_files_merge,
)


def test_copy_files_copies_directory_under_existing_destination(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "item.txt").write_text("source", encoding="utf-8")

    dst = tmp_path / "dst"
    dst.mkdir()

    copy_files(src, dst)

    assert (dst / "src" / "item.txt").read_text(encoding="utf-8") == "source"


def test_copy_files_merge_copies_directory_contents_to_destination(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "new.txt").write_text("new", encoding="utf-8")

    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "existing.txt").write_text("existing", encoding="utf-8")

    copy_files_merge(src, dst)

    assert (dst / "new.txt").read_text(encoding="utf-8") == "new"
    assert (dst / "existing.txt").read_text(encoding="utf-8") == "existing"
    assert not (dst / "src").exists()


def test_move_files_merges_into_existing_destination_directory(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "item.txt").write_text("moved", encoding="utf-8")

    dst = tmp_path / "dst"
    dst.mkdir()

    move_files(src, dst)

    assert not src.exists()
    assert (dst / "src" / "item.txt").read_text(encoding="utf-8") == "moved"


def test_move_files_merge_moves_directory_contents_to_destination(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "item.txt").write_text("moved", encoding="utf-8")

    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "existing.txt").write_text("existing", encoding="utf-8")

    move_files_merge(src, dst)

    assert not src.exists()
    assert (dst / "item.txt").read_text(encoding="utf-8") == "moved"
    assert (dst / "existing.txt").read_text(encoding="utf-8") == "existing"
    assert not (dst / "src").exists()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="当前平台不支持软链接")
def test_copy_files_preserves_and_replaces_broken_symlink(tmp_path):
    src = tmp_path / "src-link"
    src.symlink_to("missing-target")

    dst = tmp_path / "dst-link"
    dst.symlink_to("old-missing-target")

    copy_files(src, dst)

    assert dst.is_symlink()
    assert os.readlink(dst) == "missing-target"
