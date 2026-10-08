from __future__ import annotations

import tomllib
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from packaging.version import InvalidVersion, Version
from pydantic import BaseModel, computed_field, field_validator
from slugify import slugify

MIN_PYTHON_VERSION = "3.11"


class PythonArchitecture(StrEnum):
    AMD64 = "amd64"
    WIN32 = "win32"
    ARM64 = "arm64"


def derive_main_module(source_subdir: Path, project_name: str) -> str:
    """Return the module the launcher runs with ``python -m``.

    The package directory named by ``source_subdir`` (``src/simple_rss`` ->
    ``simple_rss``), or the underscore slug of the project name when the
    sources live in the project root (``.``).
    """
    if source_subdir != Path("."):
        return source_subdir.name
    return slugify(project_name, separator="_")


def missing_dunder_main(
    project_dir: Path, source_subdir: Path, main_module: str
) -> Path | None:
    """Return the ``__main__.py`` that ``python -m <main_module>`` needs, if absent.

    A package directory (``source_subdir`` other than ``.``) must contain
    ``__main__.py``. When the sources live in the project root, either
    ``<main_module>/__main__.py`` or a single module ``<main_module>.py`` will do.
    Returns None when an entry point exists.
    """
    if source_subdir != Path("."):
        dunder_main = project_dir / source_subdir / "__main__.py"
        return None if dunder_main.is_file() else dunder_main

    dunder_main = project_dir / main_module / "__main__.py"
    if dunder_main.is_file() or (project_dir / f"{main_module}.py").is_file():
        return None
    return dunder_main


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

    # PEP 517 build backend declared in [build-system]; informational only,
    # the build runs 'uv pip install', which handles any backend
    build_backend: str

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
        except InvalidVersion as e:
            raise ValueError(f"Invalid Python version format: {v}") from e

        if current_version < min_version:
            raise ValueError(f"Python version must be >= {MIN_PYTHON_VERSION}, got {v}")

        return v

    @field_validator("python_architecture", mode="before")
    @classmethod
    def validate_architecture(cls, v: str) -> PythonArchitecture:
        """Validate python_architecture value."""
        if v is None:
            raise ValueError(
                "python_architecture is required. "
                f"Valid values: {', '.join(a.value for a in PythonArchitecture)}"
            )
        try:
            return PythonArchitecture(v.lower())
        except ValueError:
            valid = [a.value for a in PythonArchitecture]
            raise ValueError(
                f"Invalid python_architecture: '{v}'. Valid values: {', '.join(valid)}"
            ) from None

    @field_validator("project_source_subdir_rel_path")
    @classmethod
    def validate_source_subdir(cls, v: Path) -> Path:
        """Validate that the source subdirectory is relative."""
        if v.is_absolute():
            raise ValueError(f"Source subdirectory must be relative: {v}")
        return v

    @field_validator("main_file_rel_path")
    @classmethod
    def validate_main_file(cls, v: Path | None) -> Path | None:
        """Validate that the main file is relative."""
        if v is None:
            return v

        if v.is_absolute():
            raise ValueError(f"Main file must be relative: {v}")

        return v

    @field_validator("icon_file_rel_path")
    @classmethod
    def validate_icon_file(cls, v: Path | None) -> Path | None:
        """Validate that the icon file is relative."""
        if v is None:
            return v

        if v.is_absolute():
            raise ValueError(f"Icon file must be relative: {v}")

        return v

    @computed_field  # type: ignore[prop-decorator]  # mypy: unsupported on @property
    @property
    def python_version_short(self) -> str:
        """Convert version '3.11.9' -> '311', '3.0.1' -> '30'."""
        parts = self.python_version.split(".")
        if len(parts) < 2:
            return ""
        major, minor = parts[0], parts[1]
        return f"{major}{minor}"

    @computed_field  # type: ignore[prop-decorator]  # mypy: unsupported on @property
    @property
    def project_name_slug_underscore(self) -> str:
        """Slugify project name with underscores (lowercase)."""
        return slugify(self.project_name, separator="_")

    @computed_field  # type: ignore[prop-decorator]  # mypy: unsupported on @property
    @property
    def project_name_slug_dash(self) -> str:
        """Slugify project name with hyphens (lowercase)."""
        return slugify(self.project_name, separator="-")

    @computed_field  # type: ignore[prop-decorator]  # mypy: unsupported on @property
    @property
    def dist_name(self) -> str:
        """Distribution name: 'my-app-0.1.0-amd64'."""
        return f"{self.project_name_slug_dash}-{self.project_version}-{self.python_architecture}"

    @computed_field  # type: ignore[prop-decorator]  # mypy: unsupported on @property
    @property
    def main_module(self) -> str:
        """Module the launcher runs with 'python -m': 'src/simple_rss' -> 'simple_rss'."""
        return derive_main_module(
            self.project_source_subdir_rel_path, self.project_name
        )

    @classmethod
    def from_pyproject_toml(cls, pyproject_path: Path | str) -> BuildConfig:
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

        # Validate [project] section
        project = data.get("project")
        if not project:
            raise ValueError("Missing [project] section in pyproject.toml")

        if "name" not in project:
            raise ValueError("Missing 'name' field in [project] section")

        if "version" not in project:
            raise ValueError("Missing 'version' field in [project] section")

        # Validate [tool.pyretort] section
        tool_pyretort = data.get("tool", {}).get("pyretort")
        if not tool_pyretort:
            raise ValueError(
                "Missing [tool.pyretort] section in pyproject.toml. "
                "Run 'pyretort init' to create it."
            )

        # Validate required fields in [tool.pyretort]
        required_pyretort_fields = [
            "python_version",
            "python_architecture",
            "project_source_subdir",
            "create_dist_zip_file",
        ]
        for field in required_pyretort_fields:
            if field not in tool_pyretort:
                raise ValueError(f"Missing '{field}' in [tool.pyretort] section")

        # Validate [build-system] section
        build_system = data.get("build-system", {})
        if not build_system:
            raise ValueError("Missing [build-system] section in pyproject.toml")

        if "build-backend" not in build_system:
            raise ValueError("Missing 'build-backend' field in [build-system] section")

        # Determine project directory (parent of pyproject.toml)
        project_dir = pyproject_path.parent.absolute()

        # Extract dependencies from project configuration
        dependencies = project.get("dependencies", [])

        # Get python version and architecture for hash calculation
        python_version = tool_pyretort.get("python_version")
        python_architecture_str = tool_pyretort.get("python_architecture")
        try:
            python_architecture = PythonArchitecture(python_architecture_str)
        except ValueError as e:
            valid = [a.value for a in PythonArchitecture]
            raise ValueError(
                f"Invalid python_architecture: '{python_architecture_str}'. "
                f"Valid values: {', '.join(valid)}"
            ) from e

        # Calculate build_hash based on python version, architecture, and dependencies
        hash_data = f"{python_version}|{python_architecture.value}|{'|'.join(sorted(dependencies))}"
        build_hash = sha256(hash_data.encode()).hexdigest()

        # Validate source subdirectory
        source_subdir = Path(tool_pyretort.get("project_source_subdir"))
        if source_subdir.is_absolute():
            raise ValueError(f"Source subdirectory must be relative: {source_subdir}")
        full_source_path = project_dir / source_subdir
        if not full_source_path.exists():
            raise ValueError(f"Source subdirectory does not exist: {full_source_path}")
        if not full_source_path.is_dir():
            raise ValueError(f"Source path is not a directory: {full_source_path}")

        # Validate main file exists if specified
        main_file_rel_path = None
        if "main_file" in tool_pyretort:
            main_file_rel_path = Path(tool_pyretort["main_file"])
            if main_file_rel_path.is_absolute():
                raise ValueError(f"Main file must be relative: {main_file_rel_path}")
            full_main_path = full_source_path / main_file_rel_path
            if not full_main_path.exists():
                raise ValueError(f"Main file does not exist: {full_main_path}")
            if not full_main_path.is_file():
                raise ValueError(f"Main path is not a file: {full_main_path}")

        # Validate icon file exists if specified
        icon_file_rel_path = None
        if "icon_file_rel_path" in tool_pyretort:
            icon_file_rel_path = Path(tool_pyretort["icon_file_rel_path"])
            if icon_file_rel_path.is_absolute():
                raise ValueError(f"Icon file must be relative: {icon_file_rel_path}")
            full_icon_path = project_dir / icon_file_rel_path
            if not full_icon_path.exists():
                raise ValueError(f"Icon file does not exist: {full_icon_path}")
            if not full_icon_path.is_file():
                raise ValueError(f"Icon path is not a file: {full_icon_path}")

        # Validate build backend: any PEP 517 backend works with 'uv pip install',
        # but an empty value would make uv fall back to legacy setuptools
        build_backend = build_system.get("build-backend")
        if not isinstance(build_backend, str) or not build_backend.strip():
            raise ValueError(
                "'build-backend' in [build-system] must be a non-empty string"
            )

        # Validate boolean fields
        install_as_package = tool_pyretort.get("install_as_package")
        if install_as_package is not None and not isinstance(install_as_package, bool):
            raise ValueError(
                f"'install_as_package' must be a boolean, got {type(install_as_package).__name__}"
            )

        show_console_window = tool_pyretort.get("show_console_window")
        if show_console_window is not None and not isinstance(
            show_console_window, bool
        ):
            raise ValueError(
                f"'show_console_window' must be a boolean, got {type(show_console_window).__name__}"
            )

        create_dist_zip_file = tool_pyretort.get("create_dist_zip_file")
        if not isinstance(create_dist_zip_file, bool):
            raise ValueError(
                f"'create_dist_zip_file' must be a boolean, got {type(create_dist_zip_file).__name__}"
            )

        # Validate the entry point: the launcher runs 'python -m <main_module>'
        if install_as_package is not False:
            main_module = derive_main_module(source_subdir, project["name"])
            dunder_main = missing_dunder_main(project_dir, source_subdir, main_module)
            if dunder_main is not None:
                raise ValueError(
                    f"Package mode requires '{dunder_main}': the launcher runs "
                    f"'python -m {main_module}'. Point project_source_subdir at the "
                    "package directory or add __main__.py."
                )

        # Extract configuration with defaults
        config_data = {
            "build_hash": build_hash,
            "project_dir_abs_path": project_dir,
            "project_name": project.get("name"),
            "project_version": project.get("version"),
            "project_source_subdir_rel_path": source_subdir,
            "main_file_rel_path": main_file_rel_path,
            "install_as_package": install_as_package,
            "python_version": python_version,
            "python_architecture": python_architecture,
            "build_backend": build_backend,
            "icon_file_rel_path": icon_file_rel_path,
            "show_console_window": show_console_window,
            "create_dist_zip_file": create_dist_zip_file,
        }

        return cls(**config_data)
