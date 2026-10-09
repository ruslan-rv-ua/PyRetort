"""Tests for pyretort.cli.commands.check command."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomli_w
from typer.testing import CliRunner

from pyretort.cli import app
from tests.conftest import write_standalone_pyproject

runner = CliRunner()


class TestCheckCommand:
    """Tests for the check command."""

    def test_check_valid_config(self, tmp_path: Path) -> None:
        """Test check command with valid configuration."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__main__.py").write_text("")

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_check_nonexistent_file(self, tmp_path: Path) -> None:
        """Test check command with non-existent file."""
        nonexistent = tmp_path / "nonexistent.toml"

        result = runner.invoke(app, ["check", "-p", str(nonexistent)])

        assert result.exit_code != 0

    def test_check_invalid_python_version(self, tmp_path: Path) -> None:
        """Test check command with Python version < 3.11."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.10.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__main__.py").write_text("")

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "error" in result.output.lower()

    def test_check_missing_pyretort_section(self, tmp_path: Path) -> None:
        """Test check command with missing [tool.pyretort] section."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code == 1

    def test_check_quiet_mode_valid(self, tmp_path: Path) -> None:
        """Test check command in quiet mode with valid config."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__main__.py").write_text("")

        result = runner.invoke(app, ["--quiet", "check", "-p", str(pyproject)])

        assert result.exit_code == 0
        assert result.output == ""

    def test_check_default_path_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that without -p and without a pyproject.toml in cwd check fails."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 1
        assert "Configuration file not found" in result.stderr

    def test_check_defaults_to_pyproject_in_current_directory(
        self, valid_pyproject_toml: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that without -p the pyproject.toml in the current directory is used."""
        monkeypatch.chdir(valid_pyproject_toml.parent)

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 0, result.output
        assert f"Configuration at {valid_pyproject_toml} is valid." in result.output

    def test_check_accepts_standalone_mode(self, tmp_path: Path) -> None:
        """Test that a script project without [build-system] passes check."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": ".",
                    "main_file": "main.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": True,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "main.py").write_text("print('hello')")

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        assert f"Configuration at {pyproject} is valid." in result.output

    def test_check_rejects_invalid_project_name(self, tmp_path: Path) -> None:
        """Test that a project name uv rejects fails check, not the build."""
        pyproject = write_standalone_pyproject(tmp_path, name="System Monitor")

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code == 1
        assert (
            "Configuration validation failed: Invalid name in [project]: "
            "'System Monitor'."
        ) in result.output
        assert "is valid" not in result.output


class TestCheckCommandEdgeCases:
    """Edge case tests for check command."""

    def test_check_empty_toml(self, tmp_path: Path) -> None:
        """Test check command with empty TOML file."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code == 1

    def test_check_invalid_toml_syntax(self, tmp_path: Path) -> None:
        """Test check command with invalid TOML syntax."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml [[[")

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code != 0

    def test_check_missing_project_name(self, tmp_path: Path) -> None:
        """Test check command with missing project name."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "version": "0.1.0",
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["check", "-p", str(pyproject)])

        assert result.exit_code == 1
