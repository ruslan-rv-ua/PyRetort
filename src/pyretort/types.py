from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import InvalidName, canonicalize_name
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel, computed_field, field_validator, model_validator
from slugify import slugify

from pyretort.constants import INSTALL_AS_PACKAGE_DEFAULT, SHOW_CONSOLE_DEFAULT

MIN_PYTHON_VERSION = "3.11"

STANDALONE_MAIN_FILE_REQUIRED = (
    "Standalone mode (install_as_package = false) requires 'main_file' "
    "in [tool.pyretort]"
)


class PythonArchitecture(StrEnum):
    AMD64 = "amd64"
    WIN32 = "win32"
    ARM64 = "arm64"


@dataclass(frozen=True)
class LauncherEntryPoint:
    """What the generated launcher runs: ``python -m <module>``.

    ``dunder_main`` is the ``__main__.py`` that makes the module runnable;
    ``single_module`` is the ``<module>.py`` alternative, accepted only when
    the sources live in the project root.
    """

    module: str
    dunder_main: Path
    single_module: Path | None = None

    def exists(self) -> bool:
        """Return True if ``python -m <module>`` would find an entry point."""
        if self.dunder_main.is_file():
            return True
        return self.single_module is not None and self.single_module.is_file()


def launcher_entry_point(
    project_dir: Path, source_subdir: Path, project_name: str
) -> LauncherEntryPoint:
    """Derive the launcher entry point from the source layout.

    A source subdirectory other than ``.`` names the package directory
    (``src/simple_rss`` -> ``python -m simple_rss``); for sources in the project
    root the module is the underscore slug of the project name.
    """
    if source_subdir != Path("."):
        module = source_subdir.name
        return LauncherEntryPoint(module, project_dir / source_subdir / "__main__.py")

    module = slugify(project_name, separator="_")
    return LauncherEntryPoint(
        module,
        project_dir / module / "__main__.py",
        single_module=project_dir / f"{module}.py",
    )


def _check_project_name_and_version(project: dict[str, Any]) -> None:
    """Raise ValueError unless uv accepts [project].name and version.

    uv checks them only when it installs the project, after the build has
    removed the previous build and downloaded the embedded Python.
    """
    for field in ("name", "version"):
        value = project[field]
        if not isinstance(value, str):
            raise ValueError(
                f"'{field}' in [project] must be a string, got {type(value).__name__}"
            )

    name = project["name"]
    try:
        canonicalize_name(name, validate=True)
    except InvalidName:
        # PyRetort names the exe and the folders after this slug, so the
        # suggested name builds the same files
        slug = slugify(name, separator="-")
        hint = f"; try '{slug}'" if slug else ""
        raise ValueError(
            f"Invalid name in [project]: '{name}'. A name may contain only ASCII "
            "letters, digits, '-', '_' and '.' and must start and end with a "
            f"letter or digit{hint}."
        ) from None

    version = project["version"]
    try:
        Version(version)
    except InvalidVersion:
        raise ValueError(
            f"Invalid version in [project]: '{version}'. "
            "Use a PEP 440 version such as '1.0.0' or '1.0b1'."
        ) from None


def _check_requires_python(requires_python: object, python_version: object) -> None:
    """Raise ValueError unless python_version satisfies [project].requires-python.

    A python_version that is no version at all is left to the model validator.
    """
    try:
        specifier = SpecifierSet(str(requires_python))
    except InvalidSpecifier:
        raise ValueError(
            f"Invalid requires-python in [project]: '{requires_python}'"
        ) from None
    try:
        version = Version(str(python_version))
    except InvalidVersion:
        return
    if not specifier.contains(version, prereleases=True):
        raise ValueError(
            f"python_version {python_version} does not satisfy requires-python "
            f"'{requires_python}' in [project]"
        )


def _read_build_backend(data: dict[str, Any]) -> str:
    """Return the build backend from [build-system], which package mode needs.

    Any PEP 517 backend works with 'uv pip install', but an empty value would
    make uv fall back to legacy setuptools.
    """
    build_system = data.get("build-system", {})
    if not build_system:
        raise ValueError("Missing [build-system] section in pyproject.toml")

    if "build-backend" not in build_system:
        raise ValueError("Missing 'build-backend' field in [build-system] section")

    build_backend = build_system["build-backend"]
    if not isinstance(build_backend, str) or not build_backend.strip():
        raise ValueError("'build-backend' in [build-system] must be a non-empty string")
    return build_backend


class BuildConfig(BaseModel):
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

    install_as_package: bool = INSTALL_AS_PACKAGE_DEFAULT

    # python version to use for the build
    # format: "major.minor.micro" e.g. "3.11.4"
    # 3.11+
    python_version: str

    # python architecture to use for the build
    python_architecture: PythonArchitecture

    # PEP 517 build backend declared in [build-system]; informational only,
    # the build runs 'uv pip install', which handles any backend. None in
    # standalone mode, which copies the sources instead of building them
    build_backend: str | None = None

    # icon file path relative to project_dir (optional)
    icon_file_rel_path: Path | None = None

    # show or hide console window when running the built application
    show_console_window: bool = SHOW_CONSOLE_DEFAULT

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

    @model_validator(mode="after")
    def validate_main_file_in_standalone_mode(self) -> BuildConfig:
        """Require the main file in standalone mode: the launcher runs it."""
        if not self.install_as_package and self.main_file_rel_path is None:
            raise ValueError(STANDALONE_MAIN_FILE_REQUIRED)
        return self

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
    def icon_file_abs_path(self) -> Path | None:
        """Icon file resolved against the project directory, None without an icon."""
        if self.icon_file_rel_path is None:
            return None
        return self.project_dir_abs_path / self.icon_file_rel_path

    @computed_field  # type: ignore[prop-decorator]  # mypy: unsupported on @property
    @property
    def main_module(self) -> str:
        """Module the launcher runs with 'python -m': 'src/simple_rss' -> 'simple_rss'."""
        return launcher_entry_point(
            self.project_dir_abs_path,
            self.project_source_subdir_rel_path,
            self.project_name,
        ).module

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

        _check_project_name_and_version(project)

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

        # The mode decides whether [build-system] is needed, so it comes first
        install_as_package = tool_pyretort.get("install_as_package")
        if install_as_package is not None and not isinstance(install_as_package, bool):
            raise ValueError(
                f"'install_as_package' must be a boolean, got {type(install_as_package).__name__}"
            )
        standalone = install_as_package is False

        # Package mode builds the project with uv, which needs a PEP 517
        # backend; standalone mode copies the sources and never builds them
        build_backend = None if standalone else _read_build_backend(data)

        # Determine project directory (parent of pyproject.toml)
        project_dir = pyproject_path.parent.absolute()

        # Get python version and architecture
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

        # Validate source subdirectory
        source_subdir = Path(tool_pyretort.get("project_source_subdir"))
        if source_subdir.is_absolute():
            raise ValueError(f"Source subdirectory must be relative: {source_subdir}")
        full_source_path = project_dir / source_subdir
        if not full_source_path.exists():
            raise ValueError(f"Source subdirectory does not exist: {full_source_path}")
        if not full_source_path.is_dir():
            raise ValueError(f"Source path is not a directory: {full_source_path}")

        # Validate main file: standalone mode runs it, so there it is required
        # and must exist, while package mode ignores it
        main_file_rel_path = None
        if standalone and "main_file" not in tool_pyretort:
            raise ValueError(STANDALONE_MAIN_FILE_REQUIRED)
        if "main_file" in tool_pyretort:
            main_file_rel_path = Path(tool_pyretort["main_file"])
            if main_file_rel_path.is_absolute():
                raise ValueError(f"Main file must be relative: {main_file_rel_path}")
            if standalone:
                full_main_path = full_source_path / main_file_rel_path
                # The build copies the source subdirectory, so the file must be in it
                if not full_main_path.resolve().is_relative_to(
                    full_source_path.resolve()
                ):
                    raise ValueError(
                        "Main file must be inside the source subdirectory: "
                        f"{tool_pyretort['main_file']}"
                    )
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

        # Validate boolean fields
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

        if standalone:
            # 'uv pip install -r pyproject.toml' reads the static dependency
            # list; a list the backend would compute is silently empty
            if "dependencies" in project.get("dynamic", []):
                raise ValueError(
                    "Standalone mode installs [project].dependencies; "
                    "'dependencies' in [project].dynamic is not supported"
                )
            # With '-r' uv does not compare requires-python with the
            # interpreter, so the mismatch would surface only at run time
            if "requires-python" in project:
                _check_requires_python(project["requires-python"], python_version)

        # Validate the entry point: in package mode the launcher runs
        # 'python -m <module>', in standalone mode it runs main_file as a script
        if not standalone:
            entry_point = launcher_entry_point(
                project_dir, source_subdir, project["name"]
            )
            if not entry_point.exists():
                raise ValueError(
                    f"Package mode requires '{entry_point.dunder_main}': the "
                    f"launcher runs 'python -m {entry_point.module}'. Point "
                    "project_source_subdir at the package directory or add "
                    "__main__.py."
                )

        # Extract configuration; absent optional booleans keep the model defaults
        config_data = {
            "project_dir_abs_path": project_dir,
            "project_name": project.get("name"),
            "project_version": project.get("version"),
            "project_source_subdir_rel_path": source_subdir,
            "main_file_rel_path": main_file_rel_path,
            "python_version": python_version,
            "python_architecture": python_architecture,
            "build_backend": build_backend,
            "icon_file_rel_path": icon_file_rel_path,
            "create_dist_zip_file": create_dist_zip_file,
        }
        if install_as_package is not None:
            config_data["install_as_package"] = install_as_package
        if show_console_window is not None:
            config_data["show_console_window"] = show_console_window

        return cls(**config_data)
