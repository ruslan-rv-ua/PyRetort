"""Shared pytest fixtures for PyRetort tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import tomli_w

from pyretort.builder.downloader import Downloader
from pyretort.builder.pydist_manager import PydistManager
from pyretort.types import BuildConfig, PythonArchitecture


def fake_pydist_manager(pydist_path: Path, downloader: Downloader) -> MagicMock:
    """Stand in for PydistManager: same python.exe location, no download.

    Installing the embedded Python leaves an empty python.exe stub, so the
    build directory has the layout of a real build. patch_pth_file is the
    real one, so a test can read the ._pth file the build wrote.
    """
    manager = MagicMock(spec=PydistManager)
    manager.python_executable = pydist_path / "python.exe"

    def install_embedded_python(*_: object, **__: object) -> None:
        pydist_path.mkdir(parents=True, exist_ok=True)
        manager.python_executable.write_bytes(b"")

    manager.install_embedded_python.side_effect = install_embedded_python
    manager.patch_pth_file.side_effect = PydistManager(
        pydist_path, downloader
    ).patch_pth_file
    return manager


def failing_pydist_manager(error: Exception) -> Callable[..., MagicMock]:
    """Return a PydistManager stand-in whose embedded Python install raises error."""

    def make(pydist_path: Path, downloader: Downloader) -> MagicMock:
        manager = fake_pydist_manager(pydist_path, downloader)
        manager.install_embedded_python.side_effect = error
        return manager

    return make


@dataclass
class BuildExternals:
    """The mocks that replace what a build needs from outside the project."""

    pydist_manager_class: MagicMock
    run: MagicMock
    which: MagicMock


@pytest.fixture
def externals() -> Iterator[BuildExternals]:
    """Replace the Python download, the uv call and the uv lookup in PATH."""
    with (
        patch(
            "pyretort.builder.uv_builder.PydistManager",
            side_effect=fake_pydist_manager,
        ) as pydist_manager_class,
        patch("subprocess.run") as run,
        patch("shutil.which", return_value="C:\\tools\\uv.exe") as which,
    ):
        yield BuildExternals(pydist_manager_class, run, which)


@pytest.fixture
def generate_exe() -> Iterator[MagicMock]:
    """Replace the launcher generator with one that writes an empty stub exe."""

    def write_stub(target: Path, **_: object) -> None:
        target.write_bytes(b"")

    with patch(
        "pyretort.builder.uv_builder.generate_exe", side_effect=write_stub
    ) as mock:
        yield mock


@pytest.fixture
def sample_build_config() -> BuildConfig:
    """Create a sample BuildConfig for testing."""
    return BuildConfig(
        project_dir_abs_path=Path("c:/test/project"),
        project_name="test-project",
        project_version="1.0.0",
        project_source_subdir_rel_path=Path("src/test_project"),
        python_version="3.11.0",
        python_architecture=PythonArchitecture.AMD64,
        build_backend="uv_build",
        create_dist_zip_file=False,
    )


@pytest.fixture
def valid_pyproject_data() -> dict[str, Any]:
    """Return valid pyproject.toml data as dictionary."""
    return {
        "project": {
            "name": "test-app",
            "version": "0.1.0",
            "dependencies": ["httpx>=0.27.0"],
        },
        "build-system": {
            "requires": ["uv_build"],
            "build-backend": "uv_build",
        },
        "tool": {
            "pyretort": {
                "project_source_subdir": "src/test_app",
                "main_file": "main.py",
                "install_as_package": True,
                "python_version": "3.13.0",
                "python_architecture": "amd64",
                "show_console_window": False,
                "create_dist_zip_file": True,
            }
        },
    }


@pytest.fixture
def valid_pyproject_toml(tmp_path: Path, valid_pyproject_data: dict[str, Any]) -> Path:
    """Create a valid pyproject.toml file in tmp_path."""
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_bytes(tomli_w.dumps(valid_pyproject_data).encode())

    source_dir = tmp_path / "src" / "test_app"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "main.py").write_text("print('hello')")
    (source_dir / "__init__.py").write_text("")
    (source_dir / "__main__.py").write_text("")

    return pyproject_path


@pytest.fixture
def invalid_pyproject_missing_fields(tmp_path: Path) -> Path:
    """Create an invalid pyproject.toml missing required fields."""
    data = {
        "project": {
            "name": "test-app",
        },
    }
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_bytes(tomli_w.dumps(data).encode())
    return pyproject_path


@pytest.fixture
def invalid_pyproject_old_python(tmp_path: Path) -> Path:
    """Create a pyproject.toml with Python version < 3.11."""
    data = {
        "project": {
            "name": "test-app",
            "version": "0.1.0",
            "dependencies": [],
        },
        "build-system": {
            "requires": ["uv_build"],
            "build-backend": "uv_build",
        },
        "tool": {
            "pyretort": {
                "project_source_subdir": "src/test_app",
                "python_version": "3.10.0",
                "python_architecture": "amd64",
                "install_as_package": True,
                "show_console_window": False,
                "create_dist_zip_file": True,
            }
        },
    }
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_bytes(tomli_w.dumps(data).encode())

    source_dir = tmp_path / "src" / "test_app"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "__init__.py").write_text("")
    (source_dir / "__main__.py").write_text("")

    return pyproject_path


@pytest.fixture
def download_dir(tmp_path: Path) -> Path:
    """Create a temporary download directory."""
    dl_dir = tmp_path / "downloads"
    dl_dir.mkdir()
    return dl_dir


@pytest.fixture
def pydist_dir(tmp_path: Path) -> Path:
    """Create a temporary pydist directory."""
    pd_dir = tmp_path / "pydist"
    pd_dir.mkdir()
    return pd_dir
