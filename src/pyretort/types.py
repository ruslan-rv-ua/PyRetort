import tomllib
from enum import StrEnum
from pathlib import Path

from packaging.version import Version
from pydantic import BaseModel, computed_field, field_validator

MIN_PYTHON_VERSION = "3.11"


class PythonArchitecture(StrEnum):
    AMD64 = "amd64"
    WIN32 = "win32"
    ARM64 = "arm64"


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

    install_as_package: bool = True

    # python version to use for the build
    # format: "major.minor.micro" e.g. "3.11.4"
    # 3.11+
    python_version: str

    # python architecture to use for the build
    python_architecture: PythonArchitecture

    # pydist directory, relative to build_output_dir
    pydist_rel_subdir_path: Path

    # build source directory, relative to build_output_dir
    build_source_rel_subdir_path: Path

    # exe file name e.g. "myapp.exe"
    exe_file_name: str

    # icon file path relative to project_dir (optional)
    icon_file_rel_path: Path | None = None

    # show or hide console window when running the built application
    show_console_window: bool = False

    # distribution zip file name e.g. "myapp-1.3.7.zip"
    # if None, zip file will not be created
    dist_zip_file_name: str

    # download cache directory, relative to project_dir
    download_cache_rel_dir_path: Path
    # build output directory, relative to project_dir
    build_output_rel_dir_path: Path
    # distribution output directory, relative to project_dir
    dist_output_rel_dir_path: Path

    @computed_field
    @property
    def download_cache_abs_dir_path(self) -> Path:
        """Absolute path to download cache directory."""
        return self.project_dir_abs_path / self.download_cache_rel_dir_path

    @computed_field
    @property
    def build_output_abs_dir_path(self) -> Path:
        """Absolute path to build output directory."""
        return self.project_dir_abs_path / self.build_output_rel_dir_path

    @computed_field
    @property
    def dist_output_abs_dir_path(self) -> Path:
        """Absolute path to distribution output directory."""
        return self.project_dir_abs_path / self.dist_output_rel_dir_path

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
    def project_name_slug_underscore(self) -> str:
        """Slugify project name with underscores (lowercase)."""
        return self.project_name.lower().replace(" ", "_").replace("-", "_")

    @computed_field
    @property
    def project_name_slug_dash(self) -> str:
        """Slugify project name with hyphens (lowercase)."""
        return self.project_name.lower().replace(" ", "-").replace("_", "-")

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

        # Determine project directory (parent of pyproject.toml)
        project_dir = pyproject_path.parent.absolute()

        # Extract configuration with defaults
        config_data = {
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
            "python_version": tool_pyretort.get("python_version"),
            "python_architecture": PythonArchitecture(
                tool_pyretort.get("python_architecture")
            ),
            "pydist_rel_subdir_path": Path(tool_pyretort.get("pydist_dir")),
            "build_source_rel_subdir_path": Path(tool_pyretort.get("build_source_dir")),
            "exe_file_name": tool_pyretort.get("exe_file_name"),
            "icon_file_rel_path": (
                Path(tool_pyretort["icon_file_rel_path"])
                if "icon_file_rel_path" in tool_pyretort
                else None
            ),
            "show_console_window": tool_pyretort.get("show_console_window"),
            "dist_zip_file_name": tool_pyretort.get("dist_zip_file_name"),
            "download_cache_rel_dir_path": Path(
                tool_pyretort.get("download_cache_dir")
            ),
            "build_output_rel_dir_path": Path(tool_pyretort.get("build_output_dir")),
            "dist_output_rel_dir_path": Path(tool_pyretort.get("dist_output_dir")),
        }

        return cls(**config_data)
