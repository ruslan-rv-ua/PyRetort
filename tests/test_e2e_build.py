"""End-to-end tests: build tiny projects for real and run the generated exe.

Unlike the mocked build tests these download the embedded Python, let uv
install into it and run the launcher, so they catch what the mocks cannot
see: the ._pth format, uv against an embedded Python and the launcher
template. hello-app is built in package mode, once with uv_build and once
with setuptools, hello-script in standalone mode. They are slow and need the
network, so they run only with ``uv run pytest -m e2e``; AGENTS.md describes
the download cache.
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

# The same project with a backend uv does not run itself: uv builds the wheels
# of uv_build without Python, but runs setuptools, like any other PEP 517
# backend, in a temporary venv of the embedded Python. setuptools finds the
# package in src/ on its own.
SETUPTOOLS_PYPROJECT = f"""\
[project]
name = "hello-app"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[build-system]
requires = ["setuptools>=80"]
build-backend = "setuptools.build_meta"

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

# A script project as 'uv init --no-package' creates it: no package, no
# [build-system].
SCRIPT_PYPROJECT = f"""\
[project]
name = "hello-script"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["six"]

[tool.pyretort]
project_source_subdir = "."
main_file = "main.py"
install_as_package = false
python_version = "{PYTHON_VERSION}"
python_architecture = "amd64"
show_console_window = false
create_dist_zip_file = true
"""

# The script imports a module next to itself, which only the ._pth entry for
# its folder makes possible, and a dependency uv installed into site-packages.
SCRIPT_MAIN = """\
import sys
from pathlib import Path

import six

import helper

marker = Path(sys.executable).resolve().parent.parent / "e2e_marker.txt"
marker.write_text(f"{helper.VALUE} six {six.__version__}", encoding="utf-8")
"""

SCRIPT_HELPER = 'VALUE = "helper imported"\n'


def copy_cached_python(project: Path) -> None:
    """Copy the embedded Python archive from the cache into project/downloads/.

    When PYRETORT_E2E_DOWNLOAD_DIR names a directory that holds the archive,
    the build finds it in downloads/ instead of downloading it.
    """
    cache_dir = os.environ.get(DOWNLOAD_DIR_ENV)
    if cache_dir is None:
        return
    cached_archive = Path(cache_dir) / EMBEDDED_PYTHON_ZIP
    if cached_archive.is_file():
        downloads = project / "downloads"
        downloads.mkdir()
        shutil.copyfile(cached_archive, downloads / EMBEDDED_PYTHON_ZIP)


def write_hello_app(project: Path, pyproject_text: str) -> Path:
    """Create the hello-app package in project with the given pyproject.toml.

    Return the path of the pyproject.toml.
    """
    pyproject = project / "pyproject.toml"
    pyproject.write_text(pyproject_text, encoding="utf-8")
    package = project / "src" / "hello_app"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(HELLO_APP_INIT, encoding="utf-8")
    (package / "__main__.py").write_text(HELLO_APP_MAIN, encoding="utf-8")
    copy_cached_python(project)
    return pyproject


@pytest.fixture
def hello_project(tmp_path: Path) -> Path:
    """Create the hello-app project in tmp_path and return its pyproject.toml."""
    return write_hello_app(tmp_path, PYPROJECT)


@pytest.fixture
def setuptools_project(tmp_path: Path) -> Path:
    """Create hello-app with the setuptools backend; return its pyproject.toml."""
    return write_hello_app(tmp_path, SETUPTOOLS_PYPROJECT)


@pytest.fixture
def script_project(tmp_path: Path) -> Path:
    """Create the hello-script project in tmp_path and return its pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(SCRIPT_PYPROJECT, encoding="utf-8")
    (tmp_path / "main.py").write_text(SCRIPT_MAIN, encoding="utf-8")
    (tmp_path / "helper.py").write_text(SCRIPT_HELPER, encoding="utf-8")
    copy_cached_python(tmp_path)
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

    def test_build_with_setuptools_backend_produces_runnable_launcher(
        self, setuptools_project: Path
    ) -> None:
        """Test that uv builds the project with setuptools in a venv of the embedded Python.

        That venv needs python3XX.zip, the standard library, as a file.
        """
        project = setuptools_project.parent

        result = runner.invoke(app, ["build", "-p", str(setuptools_project)])

        assert result.exit_code == 0, result.output
        assert "Build complete" in result.output
        app_dir = project / "build" / "hello-app-0.1.0-amd64"
        exe = app_dir / "hello-app.exe"
        assert exe.is_file()
        assert (app_dir / "hello-app" / "python313.zip").is_file()

        completed = run_launcher(exe, project / "elsewhere")

        assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
        marker = app_dir / "e2e_marker.txt"
        assert marker.is_file()
        assert "3.13.9" in marker.read_text(encoding="utf-8")

    def test_standalone_build_produces_runnable_launcher(
        self, script_project: Path
    ) -> None:
        """Test that the built exe runs main.py with its neighbour and its dependency."""
        project = script_project.parent

        result = runner.invoke(app, ["build", "-p", str(script_project)])

        assert result.exit_code == 0, result.output
        assert "Build complete" in result.output
        app_dir = project / "build" / "hello-script-0.1.0-amd64"
        exe = app_dir / "hello-script.exe"
        assert exe.is_file()
        sources = app_dir / "hello-script" / "app"
        assert (sources / "main.py").is_file()
        assert (sources / "helper.py").is_file()
        assert not (sources / "build").exists()

        completed = run_launcher(exe, project / "elsewhere")

        assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
        marker = app_dir / "e2e_marker.txt"
        assert marker.is_file()
        assert marker.read_text(encoding="utf-8").startswith("helper imported six ")
        assert (project / "dist" / "hello-script-0.1.0-amd64.zip").is_file()
