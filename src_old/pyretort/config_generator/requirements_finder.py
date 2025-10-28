from pathlib import Path

from depscanner import DependencyScanner
from dparse import parse
from dparse.dependencies import Dependency

IGNORED_DIRECTORIES = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    ".tox",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    "htmlcov",
]


def find_requirements(project_root: Path) -> list[str]:
    """
    Find requirements for the project.

    Searches for dependency files in priority order and extracts dependencies from the first found file.
    If no dependency files are found, infers dependencies from the source code.

    Args:
        project_root (Path): The root directory of the project.

    Returns:
        list[str]: A list of dependency names.
    """

    dependency_files = _find_dependency_files(project_root)
    if dependency_files:
        return _extract_dependencies_from_file(dependency_files[0])
    return _infer_dependencies_from_code(project_root)


def _find_dependency_files(directory: Path) -> list[Path]:
    """Search for dependency files in the specified directory.

    Searches for dependency files in the specified directory in priority order:
    1. pyproject.toml
    2. Pipfile
    3. setup.cfg
    4. setup.py
    5. conda.yml
    6. requirements.txt

    Args:
        directory (Path): The directory to search for dependency files.
    Returns:
        list[Path]: A list of found dependency file paths in priority order.
    """
    dependency_files = [
        "pyproject.toml",
        "Pipfile",
        "setup.cfg",
        "setup.py",
        "conda.yml",
        "requirements.txt",
    ]

    found_files = []
    for file_name in dependency_files:
        file_path = directory / file_name
        if file_path.exists():
            found_files.append(file_path)

    return found_files


def _extract_dependencies_from_file(file_path: Path) -> list[str]:
    """
    Extract dependencies from a dependency file.

    Args:
        file_path (Path): The path to the dependency file.

    Returns:
        list[str]: A list of dependency names.
    """
    content = file_path.read_text(encoding="utf-8")
    parsed = parse(content, path=str(file_path))
    dependencies = []
    for dep in parsed.dependencies:
        if isinstance(dep, Dependency):
            dependencies.append(dep.name)
    return dependencies


def _infer_dependencies_from_code(project_root: Path) -> list[str]:
    """
    Infer dependencies from the project's source code using dependency scanner.

    Args:
        project_root (Path): The root directory of the project.

    Returns:
        list[str]: A list of dependencies with versions if available.
    """
    deps_scanner = DependencyScanner(
        ignore_dirs=IGNORED_DIRECTORIES,
        follow_symlinks=False,
        prefer_local_versions=True,
        version_timeout=5.0,
    )
    result = deps_scanner.scan(project_root)
    dependencies = [
        f"{package.name}=={package.version}" if package.version else package.name
        for package in result.packages
    ]
    return dependencies
