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


def test_root_command_debug_option_enables_debug_logging():
    app_logger = logging.getLogger(cli_app.LOGGER_NAME)
    previous_level = app_logger.level
    try:
        result = CliRunner().invoke(cli_app.get_app(), ["env", "--debug"])

        assert result.exit_code == 0, result.exception
        assert app_logger.level == logging.DEBUG
    finally:
        app_logger.setLevel(previous_level)


def test_subcommand_group_debug_option_enables_debug_logging():
    app_logger = logging.getLogger(cli_app.LOGGER_NAME)
    previous_level = app_logger.level
    try:
        result = CliRunner().invoke(cli_app.get_app(), ["convert", "--debug", "win2x", "--help"])

        assert result.exit_code == 0, result.exception
        assert "--debug" in result.output
        assert app_logger.level == logging.DEBUG
    finally:
        app_logger.setLevel(previous_level)


def test_nested_command_debug_option_enables_debug_logging():
    app_logger = logging.getLogger(cli_app.LOGGER_NAME)
    previous_level = app_logger.level
    try:
        result = CliRunner().invoke(cli_app.get_app(), ["cursor", "set", "theme", "--debug", "--help"])

        assert result.exit_code == 0, result.exception
        assert "--debug" in result.output
        assert app_logger.level == logging.DEBUG
    finally:
        app_logger.setLevel(previous_level)
