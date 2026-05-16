import shutil
from collections.abc import Callable
from pathlib import Path

import pytest


SAMPLES_DIR = Path(__file__).resolve().parent


@pytest.fixture
def windows_cursor_dir() -> Path:
    return SAMPLES_DIR / "DMZ-White-Windows"


@pytest.fixture
def windows_inf_file(windows_cursor_dir: Path) -> Path:
    return windows_cursor_dir / "AutoSetup.inf"


@pytest.fixture
def linux_cursor_dir() -> Path:
    return SAMPLES_DIR / "DMZ-White-X11"


@pytest.fixture
def linux_theme_file(linux_cursor_dir: Path) -> Path:
    return linux_cursor_dir / "cursor.theme"


@pytest.fixture
def tmp_sample_copy(tmp_path: Path) -> Callable[[Path, str | None], Path]:
    def _copy(src: Path, name: str | None = None) -> Path:
        dst = tmp_path / (name or src.name)
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return dst

    return _copy
