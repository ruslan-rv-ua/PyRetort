"""Tests for pyretort.cli module entry point and callback."""

from unittest.mock import patch

from typer.testing import CliRunner

from pyretort.cli import app

runner = CliRunner()


class TestCLIEntry:
    """Tests for CLI entry point."""

    def test_cli_without_command_shows_help(self) -> None:
        """Test that running without command shows help."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "PyRetort" in result.output or "help" in result.output.lower()

    def test_cli_help_flag(self) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "pyretort" in result.output.lower()

    def test_cli_quiet_flag(self) -> None:
        """Test --quiet flag is recognized."""
        result = runner.invoke(app, ["--quiet"])
        assert result.exit_code == 0

    def test_cli_quiet_short_flag(self) -> None:
        """Test -q short flag is recognized."""
        result = runner.invoke(app, ["-q"])
        assert result.exit_code == 0

    def test_cli_version_subcommand_listed(self) -> None:
        """Test that version command is listed in help."""
        result = runner.invoke(app, ["--help"])
        assert "version" in result.output

    def test_cli_init_subcommand_listed(self) -> None:
        """Test that init command is listed in help."""
        result = runner.invoke(app, ["--help"])
        assert "init" in result.output

    def test_cli_check_subcommand_listed(self) -> None:
        """Test that check command is listed in help."""
        result = runner.invoke(app, ["--help"])
        assert "check" in result.output

    def test_cli_build_subcommand_listed(self) -> None:
        """Test that build command is listed in help."""
        result = runner.invoke(app, ["--help"])
        assert "build" in result.output


class TestCLIPlatformCheck:
    """Tests for platform check in CLI."""

    def test_cli_exits_on_non_windows(self) -> None:
        """Test that CLI exits on non-Windows platforms."""
        with patch("pyretort.cli.sys.platform", "linux"):
            result = runner.invoke(app, ["version"])
            assert result.exit_code == 1
            assert "windows" in result.output.lower()

    def test_cli_exits_on_darwin(self) -> None:
        """Test that CLI exits on macOS."""
        with patch("pyretort.cli.sys.platform", "darwin"):
            result = runner.invoke(app, ["version"])
            assert result.exit_code == 1

    def test_cli_works_on_windows(self) -> None:
        """Test that CLI works on Windows."""
        with patch("pyretort.cli.sys.platform", "win32"):
            result = runner.invoke(app, ["version"])
            assert result.exit_code == 0
