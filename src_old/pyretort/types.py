from enum import StrEnum
from pathlib import Path

import tomli
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel, computed_field, field_validator


class PythonArchitecture(StrEnum):
    AMD64 = "amd64"
    WIN32 = "win32"
    ARM64 = "arm64"


class BuildConfig(BaseModel):
    # where the root of the project to be built is located
    project_dir: Path

    # requirements for project to be built
    # will be installed into embedded Python
    requirements: list[str]

    # relative to the subdirectory within the project_dir that contains the source code
    project_source_subdir: Path

    # main entry file relative to project_source_subdir (optional)
    main_file: Path | None

    # whether to run the project as a package
    run_as_package: bool

    # python version to use for the build
    # format: "major.minor.micro" e.g. "3.11.4"
    # 3.11+
    python_version: str

    # python architecture to use for the build
    python_architecture: PythonArchitecture

    # pydist directory, relative to build_output_dir
    pydist_dir: Path
    # build source directory, relative to build_output_dir
    build_source_dir: Path

    # exe file name e.g. "myapp.exe"
    exe_file_name: str

    # icon file path relative to project_dir (optional)
    icon_path: Path | None

    # show or hide console window when running the built application
    show_console: bool

    # distribution zip file name e.g. "myapp-1.3.7.zip"
    dist_zip_file_name: str | None = None

    # download cache directory, relative to project_dir
    download_cache_dir: Path
    # build output directory, relative to project_dir
    build_output_dir: Path
    # distribution output directory, relative to project_dir
    dist_output_dir: Path

    @classmethod
    def from_toml(cls, toml_path: Path) -> "BuildConfig":
        """Load BuildConfig from a flat TOML.

        Args:
            toml_path: Path to the TOML configuration file

        Returns:
            BuildConfig instance loaded from the file

        Raises:
            FileNotFoundError: If the TOML file doesn't exist
            ValueError: If the TOML file is invalid or missing required fields
        """
        if not toml_path.exists():
            raise FileNotFoundError(f"TOML configuration file not found: {toml_path}")

        if not toml_path.is_file():
            raise ValueError(f"Path is not a file: {toml_path}")

        with open(toml_path, "rb") as f:
            config_data = tomli.load(f)

        # Convert project_dir to absolute path if it's relative to the TOML file
        if "project_dir" in config_data:
            project_dir = Path(config_data["project_dir"])
            if not project_dir.is_absolute():
                # Resolve relative to the TOML file's directory
                config_data["project_dir"] = toml_path.parent / project_dir
        else:
            # Default to the directory containing the TOML file
            config_data["project_dir"] = toml_path.parent

        # Set defaults for optional fields if not provided
        config_data.setdefault("main_file", None)
        config_data.setdefault("icon_path", None)

        # Set defaults for directory fields from constants
        from pyretort.constants import (
            BUILD_OUTPUT_DIR_DEFAULT,
            DIST_OUTPUT_DIR_DEFAULT,
            DOWNLOAD_CACHE_DIR_DEFAULT,
        )

        config_data.setdefault("download_cache_dir", Path(DOWNLOAD_CACHE_DIR_DEFAULT))
        config_data.setdefault("build_output_dir", Path(BUILD_OUTPUT_DIR_DEFAULT))
        config_data.setdefault("dist_output_dir", Path(DIST_OUTPUT_DIR_DEFAULT))

        return cls(**config_data)

    @field_validator("project_source_subdir")
    @classmethod
    def validate_source_subdir(cls, v: Path, info) -> Path:
        """Validate that the source subdirectory is a relative path, exists and is a directory."""
        if v.is_absolute():
            raise ValueError(
                f"Source subdirectory must be a relative path, not absolute: {v}"
            )

        # Get the project_dir from the validation context
        project_dir = info.data.get("project_dir")
        if project_dir is None:
            raise ValueError(
                "project_dir must be provided before validating project_source_subdir"
            )

        # Check if the path exists relative to project_dir
        full_path = project_dir / v
        if not full_path.exists():
            raise ValueError(
                f"Source subdirectory does not exist: {v} (relative to {project_dir})"
            )
        if not full_path.is_dir():
            raise ValueError(
                f"Source path is not a directory: {v} (relative to {project_dir})"
            )

        return v

    @field_validator("main_file")
    @classmethod
    def validate_main_file(cls, v: Path | None, info) -> Path | None:
        """Validate that the main file exists if provided."""
        if v is None:
            return v

        if v.is_absolute():
            raise ValueError(f"Main file must be a relative path, not absolute: {v}")

        # Build path from input fields
        project_dir = info.data.get("project_dir")
        project_source_subdir = info.data.get("project_source_subdir")

        if project_dir is None or project_source_subdir is None:
            raise ValueError(
                "project_dir and project_source_subdir must be provided before validating main_file"
            )

        project_source_dir = project_dir / project_source_subdir

        # Check if the file exists relative to project_source_dir
        full_path = project_source_dir / v
        if not full_path.exists():
            raise ValueError(
                f"Main file does not exist: {v} (relative to {project_source_dir})"
            )
        if not full_path.is_file():
            raise ValueError(
                f"Main path is not a file: {v} (relative to {project_source_dir})"
            )

        return v

    @field_validator("icon_path")
    @classmethod
    def validate_icon_path(cls, v: Path | None, info) -> Path | None:
        """Validate that the icon file exists if provided."""
        if v is None:
            return v

        if v.is_absolute():
            raise ValueError(f"Icon path must be a relative path, not absolute: {v}")

        # Get the project_dir from the validation context
        project_dir = info.data.get("project_dir")
        if project_dir is None:
            raise ValueError("project_dir must be provided before validating icon_path")

        # Check if the path exists relative to project_dir
        full_path = project_dir / v
        if not full_path.exists():
            raise ValueError(
                f"Icon file does not exist: {v} (relative to {project_dir})"
            )
        if not full_path.is_file():
            raise ValueError(
                f"Icon path is not a file: {v} (relative to {project_dir})"
            )

        return v

    @field_validator("python_version")
    @classmethod
    def validate_python_version(cls, v: str) -> str:
        """Validate that the Python version is in the correct format and is 3.11+."""
        try:
            # Parse the version using packaging library
            version = Version(v)

            # First, ensure the version is in strict major.minor.micro format
            # Check if the original string matches the parsed version's base_version
            # and doesn't contain additional components
            if v != version.base_version or len(version.release) != 3:
                raise ValueError(
                    f"Python version must be in format 'major.minor.micro' (e.g., '3.11.4'), got: {v}"
                )

            # Then check if the version is 3.11+
            min_version = Version("3.11.0")
            if version < min_version:
                raise ValueError(f"Python version must be 3.11 or higher, got: {v}")

            return v
        except InvalidVersion:
            raise ValueError(
                f"Python version must be in format 'major.minor.micro' (e.g., '3.11.4'), got: {v}"
            )

    @field_validator(
        "download_cache_dir",
        "build_output_dir",
        "dist_output_dir",
        "pydist_dir",
        "build_source_dir",
    )
    @classmethod
    def validate_relative_dir(cls, v: Path) -> Path:
        """Validate that the path is a relative directory path."""
        if v.is_absolute():
            raise ValueError(f"Directory must be a relative path, not absolute: {v}")

        return v

    # computed field for the full path to the source code directory
    @computed_field
    @property
    def project_source_dir(self) -> Path:
        """Full path to the source code directory."""
        return self.project_dir / self.project_source_subdir

    # computed field for the absolute path to the main file
    @computed_field
    @property
    def main_file_absolute(self) -> Path | None:
        """Absolute path to the main file if it exists."""
        if self.main_file is None:
            return None
        return self.project_source_dir / self.main_file

    @computed_field
    @property
    def download_cache_dir_absolute(self) -> Path:
        """Absolute path to the download cache directory."""
        return self.project_dir / self.download_cache_dir

    @computed_field
    @property
    def build_output_dir_absolute(self) -> Path:
        """Absolute path to the build output directory."""
        return self.project_dir / self.build_output_dir

    @computed_field
    @property
    def dist_output_dir_absolute(self) -> Path:
        """Absolute path to the distribution output directory."""
        return self.project_dir / self.dist_output_dir

    @computed_field
    @property
    def icon_path_absolute(self) -> Path | None:
        """Absolute path to the icon file if it exists."""
        if self.icon_path is None:
            return None
        return self.project_dir / self.icon_path

    @computed_field
    @property
    def pydist_dir_absolute(self) -> Path:
        """Absolute path to the pydist directory."""
        return self.build_output_dir_absolute / self.pydist_dir

    @computed_field
    @property
    def build_source_dir_absolute(self) -> Path:
        """Absolute path to the build source directory."""
        return self.build_output_dir_absolute / self.build_source_dir

    @computed_field
    @property
    def python_brief_version(self) -> str:
        """Short Python version (major.minor) extracted from python_version.

        Examples:
            '3.0.0' -> '30'
            '3.11.9' -> '311'
        """
        version = Version(self.python_version)
        return f"{version.major}{version.minor}"
