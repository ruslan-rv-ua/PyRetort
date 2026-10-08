"""Tests for pyretort.cli.commands.build command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
import tomli_w
from typer.testing import CliRunner

from pyretort.builder.errors import BuildError
from pyretort.cli import app
from tests.conftest import BuildExternals, failing_pydist_manager

runner = CliRunner()


@pytest.mark.usefixtures("externals", "generate_exe")
class TestBuildCommandOutput:
    """Tests for what the build command prints, with the real UVBuilder."""

    def test_build_prints_progress(
        self, tmp_path: Path, valid_pyproject_toml: Path
    ) -> None:
        """Test that the build stages and the final result are printed."""
        result = runner.invoke(app, ["build", "-p", str(valid_pyproject_toml)])

        assert result.exit_code == 0, result.output
        assert "Installing embedded Python 3.13.0 (amd64)" in result.output
        app_dir = tmp_path / "build" / "test-app-0.1.0-amd64"
        assert result.output.endswith(f"Build complete: {app_dir}\n")

    def test_build_prints_archive_path(
        self, tmp_path: Path, valid_pyproject_toml: Path
    ) -> None:
        """Test that the path of the ZIP archive in dist/ is printed."""
        result = runner.invoke(app, ["build", "-p", str(valid_pyproject_toml)])

        assert result.exit_code == 0, result.output
        archive = tmp_path / "dist" / "test-app-0.1.0-amd64.zip"
        assert f"Created archive {archive}\n" in result.output

    def test_build_defaults_to_pyproject_in_current_directory(
        self,
        tmp_path: Path,
        valid_pyproject_toml: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that without -p the pyproject.toml in the current directory is built."""
        monkeypatch.chdir(valid_pyproject_toml.parent)

        result = runner.invoke(app, ["build"])

        assert result.exit_code == 0, result.output
        app_dir = tmp_path / "build" / "test-app-0.1.0-amd64"
        assert result.output.endswith(f"Build complete: {app_dir}\n")

    def test_build_quiet_prints_nothing(self, valid_pyproject_toml: Path) -> None:
        """Test that quiet mode suppresses the progress but still builds."""
        result = runner.invoke(app, ["-q", "build", "-p", str(valid_pyproject_toml)])

        assert result.exit_code == 0
        assert result.output == ""

    def test_build_quiet_hides_config_errors(
        self, invalid_pyproject_missing_fields: Path
    ) -> None:
        """Test that quiet mode hides configuration errors but keeps exit code 1."""
        result = runner.invoke(
            app, ["-q", "build", "-p", str(invalid_pyproject_missing_fields)]
        )

        assert result.exit_code == 1
        assert result.output == ""

    def test_build_reports_locked_build_dir_without_traceback(
        self, tmp_path: Path, valid_pyproject_toml: Path
    ) -> None:
        """Test that a file of the previous build held open is reported, code 1."""
        app_dir = tmp_path / "build" / "test-app-0.1.0-amd64"
        app_dir.mkdir(parents=True)
        (app_dir / "stale.txt").write_text("left over from an earlier build")

        with open(app_dir / "stale.txt", "rb"):
            result = runner.invoke(app, ["build", "-p", str(valid_pyproject_toml)])

        assert result.exit_code == 1
        assert "Could not prepare the build directory" in result.stderr
        assert "Build complete" not in result.output

    def test_build_reports_missing_embedded_python_without_traceback(
        self, valid_pyproject_toml: Path, externals: BuildExternals
    ) -> None:
        """Test that a 404 for the embedded Python is reported without a traceback."""
        url = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip"
        request = httpx.Request("GET", url)
        missing = httpx.HTTPStatusError(
            "Client error '404 Not Found'",
            request=request,
            response=httpx.Response(404, request=request),
        )
        externals.pydist_manager_class.side_effect = failing_pydist_manager(missing)

        result = runner.invoke(app, ["build", "-p", str(valid_pyproject_toml)])

        assert result.exit_code == 1
        assert "python.org has no Windows embeddable package" in result.stderr
        assert "Traceback" not in result.output
        assert "Build complete" not in result.output


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

    def test_build_default_path_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that without -p and without a pyproject.toml in cwd build fails."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["build"])

        assert result.exit_code == 1
        assert "Configuration file not found" in result.stderr

    def test_build_reports_build_error_without_traceback(
        self, valid_pyproject_toml: Path
    ) -> None:
        """Test that a BuildError from the builder is printed as is, with exit code 1."""
        mock_builder_instance = MagicMock()
        mock_builder_instance.build.side_effect = BuildError("boom")
        mock_builder_class = MagicMock(return_value=mock_builder_instance)

        with patch("pyretort.builder.uv_builder.UVBuilder", mock_builder_class):
            result = runner.invoke(app, ["build", "-p", str(valid_pyproject_toml)])

        assert result.exit_code == 1
        assert "boom" in result.stderr
        assert "Traceback" not in result.output
