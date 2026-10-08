"""Tests for pyretort.cli.commands.version command."""

from unittest.mock import patch

from typer.testing import CliRunner

from pyretort.cli import app

runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_command_success(self) -> None:
        """Test that version command runs successfully."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_version_command_shows_pyretort(self) -> None:
        """Test that version output contains PyRetort."""
        result = runner.invoke(app, ["version"])
        assert "PyRetort" in result.output

    def test_version_command_with_known_version(self) -> None:
        """Test version command with mocked version."""
        with patch("pyretort.cli.commands.version.metadata.version") as mock_version:
            mock_version.return_value = "1.2.3"
            result = runner.invoke(app, ["version"])

            assert result.exit_code == 0
            assert "1.2.3" in result.output

    def test_version_command_unknown_version(self) -> None:
        """Test version command when package not found."""
        from importlib import metadata

        with patch(
            "pyretort.cli.commands.version.metadata.version",
            side_effect=metadata.PackageNotFoundError,
        ):
            result = runner.invoke(app, ["version"])

            assert result.exit_code == 0
            assert "unknown" in result.output

    def test_version_command_quiet_mode(self) -> None:
        """Test version command in quiet mode."""
        result = runner.invoke(app, ["--quiet", "version"])
        assert result.exit_code == 0
        assert result.output == ""
