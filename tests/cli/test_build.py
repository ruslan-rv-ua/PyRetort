"""Tests for pyretort.cli.commands.build command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import tomli_w
from typer.testing import CliRunner

from pyretort.cli import app

runner = CliRunner()


class TestBuildCommand:
    """Tests for the build command."""

    def test_build_nonexistent_config(self, tmp_path: Path) -> None:
        """Test build command with non-existent config file."""
        nonexistent = tmp_path / "nonexistent.toml"

        result = runner.invoke(app, ["build", "-p", str(nonexistent)])

        assert result.exit_code != 0

    def test_build_invalid_config(self, tmp_path: Path) -> None:
        """Test build command with invalid configuration."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app"},
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        result = runner.invoke(app, ["build", "-p", str(pyproject)])

        assert result.exit_code == 1

    def test_build_calls_uv_builder(self, tmp_path: Path) -> None:
        """Test that build command uses UVBuilder for uv_build backend."""
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

        mock_builder_instance = MagicMock()
        mock_builder_class = MagicMock(return_value=mock_builder_instance)

        with patch("pyretort.builder.uv_builder.UVBuilder", mock_builder_class):
            result = runner.invoke(app, ["build", "-p", str(pyproject)])

            mock_builder_class.assert_called_once()
            mock_builder_instance.build.assert_called_once()
            assert result.exit_code == 0

    def test_build_with_hatchling_backend_uses_uv_builder(self, tmp_path: Path) -> None:
        """Test that build accepts hatchling: uv pip install handles any backend."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
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

        mock_builder_instance = MagicMock()
        mock_builder_class = MagicMock(return_value=mock_builder_instance)

        with patch("pyretort.builder.uv_builder.UVBuilder", mock_builder_class):
            result = runner.invoke(app, ["build", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        mock_builder_class.assert_called_once()
        mock_builder_instance.build.assert_called_once()

    def test_build_rejects_standalone_mode_without_traceback(
        self, tmp_path: Path
    ) -> None:
        """Test that install_as_package = false fails cleanly and creates nothing."""
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
                    "main_file": "main.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")

        result = runner.invoke(app, ["build", "-p", str(pyproject)])

        assert result.exit_code == 1
        assert "not supported yet" in result.output
        assert "Traceback" not in result.output
        assert not (tmp_path / "build").exists()
        assert not (tmp_path / "downloads").exists()
        assert not (tmp_path / "dist").exists()

    def test_build_with_invalid_python_version(self, tmp_path: Path) -> None:
        """Test build command with Python version < 3.11."""
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

        result = runner.invoke(app, ["build", "-p", str(pyproject)])

        assert result.exit_code == 1


class TestBuildCommandEdgeCases:
    """Edge case tests for build command."""

    def test_build_default_path_when_no_file(self) -> None:
        """Test build command uses default path when no -p provided."""
        result = runner.invoke(app, ["build"])

        assert result.exit_code != 0

    def test_build_builder_exception(self, tmp_path: Path) -> None:
        """Test build command handles builder exceptions."""
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

        mock_builder_instance = MagicMock()
        mock_builder_instance.build.side_effect = RuntimeError("Build failed")
        mock_builder_class = MagicMock(return_value=mock_builder_instance)

        with patch("pyretort.builder.uv_builder.UVBuilder", mock_builder_class):
            result = runner.invoke(app, ["build", "-p", str(pyproject)])

            assert result.exit_code != 0
