"""Tests for pyretort.cli._output module."""

from unittest.mock import MagicMock, patch

import typer

from pyretort.cli._output import echo


class TestEcho:
    """Tests for echo function."""

    def test_echo_normal_mode(self) -> None:
        """Test that echo outputs message in normal mode."""
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = {"quiet": False}

        with patch("typer.echo") as mock_echo:
            echo(ctx, "Test message")
            mock_echo.assert_called_once_with("Test message", err=False)

    def test_echo_quiet_mode_suppresses_output(self) -> None:
        """Test that echo suppresses output in quiet mode."""
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = {"quiet": True}

        with patch("typer.echo") as mock_echo:
            echo(ctx, "This should not appear")
            mock_echo.assert_not_called()

    def test_echo_with_none_obj(self) -> None:
        """Test that echo handles None context object."""
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = None

        with patch("typer.echo") as mock_echo:
            echo(ctx, "Test message")
            mock_echo.assert_called_once()

    def test_echo_with_empty_obj(self) -> None:
        """Test that echo handles empty context object."""
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = {}

        with patch("typer.echo") as mock_echo:
            echo(ctx, "Test message")
            mock_echo.assert_called_once()

    def test_echo_with_err_flag(self) -> None:
        """Test that echo respects err flag."""
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = {"quiet": False}

        with patch("typer.echo") as mock_echo:
            echo(ctx, "Error message", err=True)
            mock_echo.assert_called_once_with("Error message", err=True)
