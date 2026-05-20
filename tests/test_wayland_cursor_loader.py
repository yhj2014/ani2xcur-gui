import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import NoReturn

import pytest

from ani2xcur.cursor_conversion import convert as cursor_convert


TOOLS_DIR = Path(__file__).resolve().parent / "tools"


@pytest.mark.integration
@pytest.mark.wayland
def test_generated_xcursor_theme_loads_with_libwayland_cursor(windows_inf_file: Path, tmp_path: Path):
    """Load a converted theme through libwayland-cursor against headless Weston."""
    verifier = _compile_wayland_cursor_verifier(tmp_path)
    save_dir = cursor_convert.win_cursor_to_x11(windows_inf_file, tmp_path, {})

    assert (save_dir / "index.theme").read_text(encoding="utf-8").count("Inherits=DMZ-White") == 0
    assert (save_dir / "cursor.theme").read_text(encoding="utf-8").count("Inherits=DMZ-White") == 0

    xdg_runtime_dir = tmp_path / "xdg-runtime"
    xdg_runtime_dir.mkdir()
    os.chmod(xdg_runtime_dir, 0o700)
    socket_name = "ani2xcur-wayland-test"

    weston_env = os.environ.copy()
    weston_env["XDG_RUNTIME_DIR"] = str(xdg_runtime_dir)
    weston = subprocess.Popen(
        [
            _require_program("weston"),
            "--backend=headless-backend.so",
            f"--socket={socket_name}",
            "--idle-time=0",
            "--no-config",
        ],
        env=weston_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    results: dict[int, subprocess.CompletedProcess[str]] = {}
    try:
        _wait_for_wayland_socket(weston, xdg_runtime_dir / socket_name)

        verifier_env = weston_env.copy()
        verifier_env["WAYLAND_DISPLAY"] = socket_name
        verifier_env["XCURSOR_PATH"] = str(tmp_path)
        results = {
            size: subprocess.run(
                [str(verifier), "DMZ-White", str(size), str(size)],
                env=verifier_env,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            for size in [24, 32, 48, 64, 80]
        }
    finally:
        _stop_process(weston)

    for size, result in results.items():
        output = result.stdout + result.stderr
        assert result.returncode == 0, f"size={size}\n{output}"
        assert "OK left_ptr images=" in output
        assert "OK default images=" in output
        assert "OK wayland-cursor images=" in output
        assert "OK watch images=23" in output
        assert "SIZE_MISMATCH" not in output


def _compile_wayland_cursor_verifier(tmp_path: Path) -> Path:
    cc = _require_program("cc")
    _require_program("pkg-config")
    flags = _pkg_config_flags()
    verifier = tmp_path / "verify_wayland_cursor"
    result = subprocess.run(
        [
            cc,
            str(TOOLS_DIR / "verify_wayland_cursor.c"),
            "-o",
            str(verifier),
            *flags,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return verifier


def _pkg_config_flags() -> list[str]:
    result = subprocess.run(
        ["pkg-config", "--cflags", "--libs", "wayland-client", "wayland-cursor"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        _skip_or_fail(f"libwayland-cursor development files are unavailable:\n{result.stderr}")
    return shlex.split(result.stdout)


def _require_program(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        _skip_or_fail(f"{name} is unavailable")
    return path


def _wait_for_wayland_socket(process: subprocess.Popen[str], socket_path: Path) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if socket_path.exists():
            return
        if process.poll() is not None:
            output, _ = process.communicate(timeout=1)
            _skip_or_fail(f"headless Weston could not start:\n{output or ''}")
        time.sleep(0.05)
    _skip_or_fail(f"headless Weston did not create socket: {socket_path}")


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate(timeout=5)


def _skip_or_fail(message: str) -> NoReturn:
    if os.environ.get("ANI2XCUR_REQUIRE_WAYLAND_TEST") == "1":
        pytest.fail(message)
    pytest.skip(message)
