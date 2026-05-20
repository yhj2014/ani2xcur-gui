import subprocess

from ani2xcur import cmd


def test_run_cmd_debug_log_summarizes_selected_environment(monkeypatch):
    records = []

    def fake_debug(message, *args):
        records.append((message, args))

    def fake_run(**kwargs):
        assert kwargs["env"]["SECRET_TOKEN"] == "hidden"
        return subprocess.CompletedProcess(args=kwargs["args"], returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(cmd.logger, "debug", fake_debug)
    monkeypatch.setattr(cmd.subprocess, "run", fake_run)

    cmd.run_cmd(
        ["echo", "ok"],
        custom_env={
            "DISPLAY": ":0",
            "XCURSOR_SIZE": "32",
            "SECRET_TOKEN": "hidden",
        },
        live=False,
        check=False,
    )

    rendered_records = repr(records)
    assert "DISPLAY" in rendered_records
    assert "XCURSOR_SIZE" in rendered_records
    assert "SECRET_TOKEN" not in rendered_records
    assert "hidden" not in rendered_records
