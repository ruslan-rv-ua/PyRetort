import tomllib
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from packaging.version import Version
from pydantic import BaseModel, computed_field, field_validator
from slugify import slugify

MIN_PYTHON_VERSION = "3.11"


class PythonArchitecture(StrEnum):
    AMD64 = "amd64"
    WIN32 = "win32"
    ARM64 = "arm64"


class BuildBackend(StrEnum):
    """All possible values for [build-system].build-backend in pyproject.toml"""

    # setuptools
    SETUPTOOLS = "setuptools.build_meta"
    SETUPTOOLS_SCM = "setuptools.build_meta"  # with setuptools-scm plugin

    # hatchling
    HATCHLING = "hatchling.build"

    # uv
    UV = "uv"

    # poetry
    POETRY_CORE = "poetry.core.masonry.api"

    # flit
    FLIT_CORE = "flit_core.buildapi"

    # PDM
    PDM_BACKEND = "pdm.backend"
    PDM_PEP517 = "pdm.pep517.api"  # legacy PDM backend

    # meson-python
    MESON_PYTHON = "mesonpy"

    # scikit-build-core
    SCIKIT_BUILD_CORE = "scikit_build_core.build"

    # maturin (for Rust extensions)
    MATURIN = "maturin"

    # trampolim (for Java/JVM integration)
    TRAMPOLIM = "trampolim"

    # py-build-cmake
    PY_BUILD_CMAKE = "py_build_cmake.build"

    # enscons (SCons-based)
    ENSCONS = "enscons.api"

    # whey
    WHEY = "whey"

    # flit (legacy)
    FLIT = "flit.buildapi"

    # jupyter-packaging
    JUPYTER_PACKAGING = "jupyter_packaging.build_api"


class BuildConfig(BaseModel):
    # build hash based on python version, architecture, dependencies
    build_hash: str

    # where the root of the project to be built is located
    project_dir_abs_path: Path

    # project name
    project_name: str

    # project version
    project_version: str

    # source subdirectory inside project_dir
    project_source_subdir_rel_path: Path

    # main entry file relative to project_source_subdir_rel_path (optional)
    main_file_rel_path: Path | None = None

    install_as_package: bool = True

    # python version to use for the build
    # format: "major.minor.micro" e.g. "3.11.4"
    # 3.11+
    python_version: str

    # python architecture to use for the build
    python_architecture: PythonArchitecture

    # build backend to use for building the project
    build_backend: BuildBackend

    # icon file path relative to project_dir (optional)
    icon_file_rel_path: Path | None = None

    # show or hide console window when running the built application
    show_console_window: bool = False

    create_dist_zip_file: bool

    @field_validator("python_version")
    @classmethod
    def validate_python_version(cls, v: str) -> str:
        try:
            current_version = Version(v)
            min_version = Version(MIN_PYTHON_VERSION)
        except Exception as e:
            raise ValueError(f"Invalid Python version format: {v}") from e

        if current_version < min_version:
            raise ValueError(f"Python version must be >= {MIN_PYTHON_VERSION}, got {v}")

        return v

    @computed_field
    @property
    def python_version_short(self) -> str:
        """Convert version '3.11.9' -> '311', '3.0.1' -> '30'."""
        parts = self.python_version.split(".")
        if len(parts) < 2:
            return ""
        major, minor = parts[0], parts[1]
        return f"{major}{minor}"

    @computed_field
    @property
    def project_name_slug_underscore(self) -> str:
        """Slugify project name with underscores (lowercase)."""
        return slugify(self.project_name, separator="_")

    @computed_field
    @property
    def project_name_slug_dash(self) -> str:
        """Slugify project name with hyphens (lowercase)."""
        return slugify(self.project_name, separator="-")

    @computed_field
    @property
    def dist_name(self) -> str:
        """Distribution name: 'my-app-0.1.0-amd64'."""
        return f"{self.project_name_slug_dash}-{self.project_version}-{self.python_architecture}"

    @classmethod
    def from_pyproject_toml(cls, pyproject_path: Path | str) -> "BuildConfig":
        """
        Create BuildConfig from pyproject.toml file.

        Args:
            pyproject_path: Path to pyproject.toml file

        Returns:
            BuildConfig instance

        Raises:
            FileNotFoundError: If pyproject.toml doesn't exist
            ValueError: If required fields are missing or invalid
        """
        pyproject_path = Path(pyproject_path).resolve()
        if not pyproject_path.exists():
            raise FileNotFoundError(f"File not found: {pyproject_path}")

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Get project metadata
        project = data.get("project", {})
        tool_pyretort = data.get("tool", {}).get("pyretort", {})
        build_system = data.get("build-system", {})

        # Determine project directory (parent of pyproject.toml)
        project_dir = pyproject_path.parent.absolute()

        # Extract dependencies from project configuration
        dependencies = project.get("dependencies", [])

        # Get python version and architecture for hash calculation
        python_version = tool_pyretort.get("python_version")
        python_architecture = PythonArchitecture(
            tool_pyretort.get("python_architecture")
        )

        # Calculate build_hash based on python version, architecture, and dependencies
        hash_data = f"{python_version}|{python_architecture.value}|{'|'.join(sorted(dependencies))}"
        build_hash = sha256(hash_data.encode()).hexdigest()

        # Extract configuration with defaults
        config_data = {
            "build_hash": build_hash,
            "project_dir_abs_path": project_dir,
            "project_name": project.get("name"),
            "project_version": project.get("version"),
            "project_source_subdir_rel_path": Path(
                tool_pyretort.get("project_source_subdir")
            ),
            "main_file_rel_path": (
                Path(tool_pyretort["main_file"])
                if "main_file" in tool_pyretort
                else None
            ),
            "install_as_package": tool_pyretort.get("install_as_package"),
            "python_version": python_version,
            "python_architecture": python_architecture,
            "build_backend": BuildBackend(build_system.get("build-backend")),
            "icon_file_rel_path": (
                Path(tool_pyretort["icon_file_rel_path"])
                if "icon_file_rel_path" in tool_pyretort
                else None
            ),
            "show_console_window": tool_pyretort.get("show_console_window"),
            "create_dist_zip_file": tool_pyretort.get("create_dist_zip_file"),
        }

        return cls(**config_data)
