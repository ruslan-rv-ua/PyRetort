"""End-to-end test: build a tiny project for real and run the generated exe.

Unlike the mocked build tests this one downloads the embedded Python, lets
uv install the project into it and runs the launcher, so it catches what the
mocks cannot see: the ._pth format, uv against an embedded Python and the
launcher template. It is slow and needs the network, so it runs only with
``uv run pytest -m e2e``; AGENTS.md describes the download cache.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyretort.cli import app

runner = CliRunner()

PYTHON_VERSION = "3.13.9"
EMBEDDED_PYTHON_ZIP = f"python-{PYTHON_VERSION}-embed-amd64.zip"
# A directory that already holds EMBEDDED_PYTHON_ZIP; skips the 11 MB download.
DOWNLOAD_DIR_ENV = "PYRETORT_E2E_DOWNLOAD_DIR"

PYPROJECT = f"""\
[project]
name = "hello-app"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[build-system]
requires = ["uv_build>=0.9.4,<0.10.0"]
build-backend = "uv_build"

[tool.pyretort]
project_source_subdir = "src/hello_app"
install_as_package = true
python_version = "{PYTHON_VERSION}"
python_architecture = "amd64"
show_console_window = false
create_dist_zip_file = true
"""

# The launcher runs Python hidden, so the application reports through a file
# next to the launcher: build/<dist_name>/e2e_marker.txt.
HELLO_APP_INIT = """\
import sys
from pathlib import Path


def main() -> None:
    marker = Path(sys.executable).resolve().parent.parent / "e2e_marker.txt"
    marker.write_text(sys.version, encoding="utf-8")
"""

HELLO_APP_MAIN = """\
from hello_app import main

main()
"""


@pytest.fixture
def hello_project(tmp_path: Path) -> Path:
    """Create the hello-app project in tmp_path and return its pyproject.toml.

    When PYRETORT_E2E_DOWNLOAD_DIR names a directory that holds the embedded
    Python archive, the archive is copied into the project's downloads/, so
    the build finds it there instead of downloading it.
    """
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(PYPROJECT, encoding="utf-8")
    package = tmp_path / "src" / "hello_app"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(HELLO_APP_INIT, encoding="utf-8")
    (package / "__main__.py").write_text(HELLO_APP_MAIN, encoding="utf-8")

    cache_dir = os.environ.get(DOWNLOAD_DIR_ENV)
    if cache_dir is not None:
        cached_archive = Path(cache_dir) / EMBEDDED_PYTHON_ZIP
        if cached_archive.is_file():
            downloads = tmp_path / "downloads"
            downloads.mkdir()
            shutil.copyfile(cached_archive, downloads / EMBEDDED_PYTHON_ZIP)
    return pyproject


def run_launcher(exe: Path, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    """Run the launcher from cwd and wait until the application has finished."""
    cwd.mkdir(exist_ok=True)
    return subprocess.run([str(exe)], capture_output=True, cwd=cwd, timeout=120)


@pytest.mark.slow
@pytest.mark.e2e
@pytest.mark.requires_network
@pytest.mark.windows
class TestEndToEndBuild:
    """Tests that build hello-app for real and run the generated launcher."""

    def test_build_produces_runnable_launcher(self, hello_project: Path) -> None:
        """Test that the built exe runs the application with the embedded Python."""
        project = hello_project.parent

        result = runner.invoke(app, ["build", "-p", str(hello_project)])

        assert result.exit_code == 0, result.output
        assert "Build complete" in result.output
        app_dir = project / "build" / "hello-app-0.1.0-amd64"
        exe = app_dir / "hello-app.exe"
        assert exe.is_file()
        assert (app_dir / "hello-app" / "python.exe").is_file()

        completed = run_launcher(exe, project / "elsewhere")

        assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
        marker = app_dir / "e2e_marker.txt"
        assert marker.is_file()
        assert "3.13.9" in marker.read_text(encoding="utf-8")
        assert (project / "dist" / "hello-app-0.1.0-amd64.zip").is_file()

    def test_second_build_in_same_project_succeeds(self, hello_project: Path) -> None:
        """Test that a rebuild after a run succeeds and starts the folder afresh."""
        project = hello_project.parent
        first = runner.invoke(app, ["build", "-p", str(hello_project)])
        assert first.exit_code == 0, first.output
        app_dir = project / "build" / "hello-app-0.1.0-amd64"
        run_launcher(app_dir / "hello-app.exe", project / "elsewhere")
        marker = app_dir / "e2e_marker.txt"
        assert marker.is_file()

        second = runner.invoke(app, ["build", "-p", str(hello_project)])

        assert second.exit_code == 0, second.output
        assert "Build complete" in second.output
        assert not marker.exists()
        assert (app_dir / "hello-app.exe").is_file()
