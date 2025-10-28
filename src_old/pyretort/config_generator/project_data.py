from pathlib import Path

from slugify import slugify
from tomli import load as tomli_load

DEFAULT_PROJECT_NAME = "project"
PYPROJECT_FILENAME = "pyproject.toml"

# Candidate source folder names in priority order
DEFAULT_SOURCE_FOLDERS = [
    "app",
    "application",
    "main",
    "core",
]

SLUG_SEPARATOR = "_"
DEFAULT_MAIN_FILENAME = "main.py"

ICON_FILENAMES: tuple[str, ...] = ("icon.ico",)
ICON_SEARCH_DIRECTORIES: tuple[Path, ...] = (
    Path("."),
    Path("assets"),
    Path("resources"),
    Path("icons"),
    Path("src"),
    Path("src/assets"),
    Path("src/resources"),
    Path("src/icons"),
)
ICON_FILE_EXTENSIONS: frozenset[str] = frozenset({".ico"})


def find_project_name(project_root: Path) -> str:
    """Get the project name from pyproject.toml or derive it from the folder name.

    Args:
        project_root: Path to the project root directory.

    Returns:
        The project name as a string.
    """
    pyproject_path = project_root / PYPROJECT_FILENAME
    if pyproject_path.exists():
        project_name = _get_name_from_pyproject(pyproject_path)
        if project_name:
            return project_name
    return project_root.name


def _get_name_from_pyproject(pyproject_path: Path) -> str | None:
    """Extract the project name from a pyproject.toml file.

    Args:
        pyproject_path: Path to the pyproject.toml file.

    Returns:
        The project name if found, otherwise None.
    """
    with pyproject_path.open("rb") as f:
        pyproject_data = tomli_load(f)
    try:
        return pyproject_data["project"]["name"]
    except KeyError:
        pass
    try:
        return pyproject_data["tool"]["poetry"]["name"]
    except KeyError:
        return None


def find_project_version(project_root: Path) -> str | None:
    """Get the project version from pyproject.toml.

    Args:
        project_root: Path to the project root directory.

    Returns:
        The project version if found, otherwise None.
    """
    pyproject_path = project_root / PYPROJECT_FILENAME
    if not pyproject_path.exists():
        return None
    with pyproject_path.open("rb") as f:
        pyproject_data = tomli_load(f)
    try:
        return pyproject_data["project"]["version"]
    except KeyError:
        pass
    try:
        return pyproject_data["tool"]["poetry"]["version"]
    except KeyError:
        return None


def find_source_subdir(project_root: Path, project_name: str) -> Path:
    """Find the source subdirectory within the project.

    Args:
        project_root: Path to the project root directory.
        project_name: The project name (will be slugified for searching).

    Returns:
        Relative path from project_root to the source subdirectory, or Path('.') if not found.
    """
    project_name_slugified = slugify(project_name, separator=SLUG_SEPARATOR)

    # Combine the project slug and default candidates in priority order
    folder_names = [project_name_slugified] + DEFAULT_SOURCE_FOLDERS

    # Parent directories to search (priority order)
    search_paths = [project_root / "src", project_root]

    for parent in search_paths:
        if not parent.exists():
            continue
        for folder_name in folder_names:
            candidate = parent / folder_name
            if candidate.exists() and candidate.is_dir():
                return candidate.relative_to(project_root)

    return Path(".")


def find_main_file(project_source_path: Path, project_name: str) -> Path:
    """Find the main file of the project.

    Returns:
        Path to the main file relative to source path.
    """
    project_name_slugified = slugify(project_name, separator=SLUG_SEPARATOR)

    candidate_files = [
        "__main__.py",
        DEFAULT_MAIN_FILENAME,
        "app.py",
        f"{project_name_slugified}.py",
    ]

    for file_name in candidate_files:
        candidate = project_source_path / file_name
        if candidate.exists() and candidate.is_file():
            return candidate.relative_to(project_source_path)
    return Path(DEFAULT_MAIN_FILENAME)


def find_icon_path(project_root: Path) -> Path | None:
    """Find an icon file in the project root directory.

    Args:
        project_root: Path to the project root directory.
    Returns:
        relative path to the icon file if found, otherwise None.
    """
    for icon_name in ICON_FILENAMES:
        candidate = project_root / icon_name
        if candidate.exists() and candidate.is_file():
            return candidate.relative_to(project_root)

    for search_dir in ICON_SEARCH_DIRECTORIES:
        dir_path = project_root / search_dir
        if not dir_path.exists() or not dir_path.is_dir():
            continue

        for item in sorted(dir_path.iterdir()):
            if item.is_file() and item.suffix.lower() in ICON_FILE_EXTENSIONS:
                return item.relative_to(project_root)

    return None
