"""Integration tests for PyRetort.

These tests verify end-to-end functionality and require network access for some tests.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import tomli_w
from typer.testing import CliRunner

from pyretort.builder.cache_manager import CacheManager
from pyretort.builder.downloader import Downloader
from pyretort.builder.pydist_manager import PydistManager
from pyretort.cli import app
from pyretort.types import BuildConfig, PythonArchitecture

runner = CliRunner()


class TestBuildConfigIntegration:
    """Integration tests for BuildConfig."""

    def test_full_config_flow(self, tmp_path: Path) -> None:
        """Test creating config, validating, and using computed fields."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "integration-test-app",
                "version": "1.2.3",
                "dependencies": ["httpx>=0.27.0", "typer>=0.15.0"],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src/integration_test_app",
                    "main_file": "main.py",
                    "install_as_package": True,
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src" / "integration_test_app"
        source_dir.mkdir(parents=True)
        (source_dir / "__init__.py").write_text("")
        (source_dir / "__main__.py").write_text("")
        (source_dir / "main.py").write_text("print('Hello')")

        config = BuildConfig.from_pyproject_toml(pyproject)

        assert config.project_name == "integration-test-app"
        assert config.project_name_slug_dash == "integration-test-app"
        assert config.project_name_slug_underscore == "integration_test_app"
        assert config.python_version_short == "313"
        assert config.dist_name == "integration-test-app-1.2.3-amd64"
        assert len(config.build_hash) == 64


class TestCacheDownloaderIntegration:
    """Integration tests for CacheManager and Downloader."""

    def test_cache_with_downloader(self, tmp_path: Path) -> None:
        """Test that cache and downloader work together."""
        cache_path = tmp_path / "cache"
        download_path = tmp_path / "downloads"
        download_path.mkdir()

        cache = CacheManager(cache_path)
        Downloader(download_path)

        test_file = download_path / "test.txt"
        test_file.write_text("test content")

        assert "test.txt" not in cache

        (cache_path / "test.txt").write_text("cached")
        assert "test.txt" in cache

        cache.cleanup()
        assert "test.txt" not in cache


class TestCLIWorkflow:
    """Integration tests for CLI workflow."""

    def test_init_then_check(self, tmp_path: Path) -> None:
        """Test init command followed by check command."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "workflow-test",
                "version": "0.1.0",
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        source_dir = tmp_path / "src" / "workflow_test"
        source_dir.mkdir(parents=True)
        # Create main.py file that init command will find
        (source_dir / "main.py").write_text("print('hello')")
        # Create __main__.py so that check accepts the package the launcher runs
        (source_dir / "__main__.py").write_text("")

        init_result = runner.invoke(app, ["init", "-p", str(pyproject)])
        assert init_result.exit_code == 0

        check_result = runner.invoke(app, ["check", "-p", str(pyproject)])
        assert check_result.exit_code == 0
        assert "valid" in check_result.output.lower()

    def test_init_then_check_without_main_file(self, tmp_path: Path) -> None:
        """Test that init's config for a package without main.py passes check."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "workflow-test",
                "version": "0.1.0",
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        source_dir = tmp_path / "src" / "workflow_test"
        source_dir.mkdir(parents=True)
        (source_dir / "__init__.py").write_text("")
        (source_dir / "__main__.py").write_text("")

        init_result = runner.invoke(app, ["init", "-p", str(pyproject)])
        assert init_result.exit_code == 0, init_result.output

        check_result = runner.invoke(app, ["check", "-p", str(pyproject)])
        assert check_result.exit_code == 0, check_result.output
        assert "is valid" in check_result.output


class TestPydistManagerIntegration:
    """Integration tests for PydistManager without network."""

    def test_patch_and_verify_flow(self, tmp_path: Path) -> None:
        """Test the patch_pth_file and verification flow."""
        pydist_path = tmp_path / "pydist"
        pydist_path.mkdir()
        download_path = tmp_path / "downloads"
        download_path.mkdir()

        downloader = Downloader(download_path)
        manager = PydistManager(pydist_path, downloader)

        (pydist_path / "python.exe").write_bytes(b"fake exe")

        manager._verify_embedded_python()

        manager.patch_pth_file("3.13.0", "src/myapp")

        pth_file = pydist_path / "python313._pth"
        assert pth_file.exists()
        content = pth_file.read_text()
        assert "python313.zip" in content
        assert "src/myapp" in content


@pytest.mark.slow
@pytest.mark.requires_network
class TestNetworkIntegration:
    """Integration tests that require network access."""

    def test_download_embedded_python_metadata(self, tmp_path: Path) -> None:
        """Test downloading embedded Python distribution (just metadata check)."""
        download_path = tmp_path / "downloads"
        download_path.mkdir()
        pydist_path = tmp_path / "pydist"
        pydist_path.mkdir()

        downloader = Downloader(download_path)
        manager = PydistManager(pydist_path, downloader)

        archive_path = manager._download_embedded_python(
            "3.13.0", PythonArchitecture.AMD64
        )

        assert archive_path.exists()
        assert archive_path.suffix == ".zip"
        assert archive_path.stat().st_size > 0


@pytest.mark.slow
@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end tests for complete build process."""

    def test_complete_build_mocked(self, tmp_path: Path) -> None:
        """Test complete build process with mocked network."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "e2e-test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src/e2e_test_app",
                    "main_file": "main.py",
                    "install_as_package": True,
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "show_console_window": False,
                    "create_dist_zip_file": False,
                }
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src" / "e2e_test_app"
        source_dir.mkdir(parents=True)
        (source_dir / "__init__.py").write_text("")
        (source_dir / "__main__.py").write_text("")
        (source_dir / "main.py").write_text("print('E2E Test')")

        mock_builder = MagicMock()
        mock_builder_class = MagicMock(return_value=mock_builder)

        with patch("pyretort.builder.uv_builder.UVBuilder", mock_builder_class):
            result = runner.invoke(app, ["build", "-p", str(pyproject)])

            assert result.exit_code == 0
            mock_builder.build.assert_called_once()
