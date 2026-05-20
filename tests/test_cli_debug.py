import logging

from typer.testing import CliRunner

from ani2xcur.cli import app as cli_app


def test_global_debug_option_enables_debug_logging():
    app_logger = logging.getLogger(cli_app.LOGGER_NAME)
    previous_level = app_logger.level
    try:
        result = CliRunner().invoke(cli_app.get_app(), ["--debug", "env"])

        assert result.exit_code == 0, result.exception
        assert app_logger.level == logging.DEBUG
    finally:
        app_logger.setLevel(previous_level)
