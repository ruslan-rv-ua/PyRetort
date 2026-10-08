"""Shared pytest fixtures for PyRetort tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import tomli_w

from pyretort.types import BuildConfig, PythonArchitecture


@pytest.fixture
def sample_build_config() -> BuildConfig:
    """Create a sample BuildConfig for testing."""
    return BuildConfig(
        build_hash="abc123def456",
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
def cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory path (not created yet)."""
    return tmp_path / "cache"


@pytest.fixture
def pydist_dir(tmp_path: Path) -> Path:
    """Create a temporary pydist directory."""
    pd_dir = tmp_path / "pydist"
    pd_dir.mkdir()
    return pd_dir
