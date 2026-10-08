"""Tests for pyretort.cli.commands.check command."""

from pathlib import Path

import tomli_w
from typer.testing import CliRunner

from pyretort.cli import app

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

    def test_check_default_path_when_no_file(self) -> None:
        """Test check command uses default path (cwd/pyproject.toml)."""
        result = runner.invoke(app, ["check"])

        assert result.exit_code != 0


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
