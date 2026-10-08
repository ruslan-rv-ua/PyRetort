from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import tomlkit
import typer
from slugify import slugify

from pyretort.cli._output import echo
from pyretort.constants import (
    INSTALL_AS_PACKAGE_DEFAULT,
    SHOW_CONSOLE_DEFAULT,
)
from pyretort.types import PythonArchitecture


def init_command(
    ctx: typer.Context,
    pyproject_toml_path: Path = typer.Option(
        Path.cwd() / "pyproject.toml",
        "--pyproject-toml",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        help="Path to the pyproject.toml file of the target project.",
    ),
) -> None:
    """Initialize a PyRetort configuration file for a Python project."""

    pyproject_toml_path = pyproject_toml_path.resolve()

    _update_pyproject_toml(pyproject_toml_path)

    echo(ctx, f"pyproject.toml updated successfully at: {pyproject_toml_path}")
    echo(ctx, "Next steps:")
    echo(
        ctx,
        "  1. Review and customize the [tool.pyretort] section in pyproject.toml as needed.",
    )
    echo(ctx, "  2. Run 'pyretort build' to create the distributable package.")


def _update_pyproject_toml(pyproject_toml_path: Path) -> None:
    """Update the pyproject.toml file to include PyRetort configuration."""

    project_path = pyproject_toml_path.parent.resolve()

    pyproject_data = tomlkit.parse(pyproject_toml_path.read_text(encoding="utf-8"))

    if "tool" not in pyproject_data:
        pyproject_data["tool"] = tomlkit.table()

    tool_section = pyproject_data.get("tool")
    if tool_section is None:
        tool_section = tomlkit.table()
        pyproject_data["tool"] = tool_section

    pyretort_config: dict[str, Any] = tomlkit.table()

    project_name = str(pyproject_data.get("project", {}).get("name", ""))
    source_subdir = _find_project_source_subdir(project_path, project_name)

    pyretort_config.add(
        tomlkit.comment(
            "Path to the project source directory relative to the project root"
        )
    )
    pyretort_config["project_source_subdir"] = source_subdir

    pyretort_config.add(
        tomlkit.comment(
            "Name of the main Python file to execute (e.g., main.py, app.py)"
        )
    )
    main_file = _find_main_file(project_path / source_subdir)
    if main_file is None:
        pyretort_config.add(
            tomlkit.comment("TODO: Update this to point to your main application file")
        )
        pyretort_config["main_file"] = "main.py"
    else:
        pyretort_config["main_file"] = main_file
    pyretort_config.add(
        tomlkit.comment(
            "Whether to install the project as a Python package during build"
        )
    )
    pyretort_config["install_as_package"] = INSTALL_AS_PACKAGE_DEFAULT

    pyretort_config.add(
        tomlkit.comment("Python version to use for the bundled distribution")
    )
    pyretort_config["python_version"] = _find_python_version()

    pyretort_config.add(
        tomlkit.comment("Python architecture to use (amd64, win32, arm64)")
    )
    pyretort_config["python_architecture"] = _find_python_architecture()

    pyretort_config.add(
        tomlkit.comment(
            "Whether to show the console window when running the application"
        )
    )
    pyretort_config["show_console_window"] = SHOW_CONSOLE_DEFAULT

    pyretort_config.add(
        tomlkit.comment("Whether to create a ZIP archive of the distribution")
    )
    pyretort_config["create_dist_zip_file"] = True

    tool_section["pyretort"] = pyretort_config

    pyproject_toml_path.write_text(tomlkit.dumps(pyproject_data), encoding="utf-8")


def _find_project_source_subdir(project_path: Path, project_name: str) -> str:
    """Attempt to find the main source subdirectory of the project."""
    common_dirs = [".", "src", "source", "app", "lib"]
    slugified_name = slugify(project_name, separator="_")
    for dir_name in common_dirs:
        candidate = project_path / dir_name / slugified_name
        if candidate.is_dir():
            return candidate.relative_to(project_path).as_posix()
    return "."  # Default to project root if no common source dir found


def _find_main_file(source_dir: Path) -> str | None:
    """Attempt to find the main Python file in the source directory."""
    common_main_files = ["main.py", "app.py", "run.py"]
    for file_name in common_main_files:
        candidate = source_dir / file_name
        if candidate.is_file():
            return file_name
    return None


def _find_python_version() -> str:
    """Get the current Python version as a string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _find_python_architecture() -> PythonArchitecture:
    """Get the current Python architecture (32-bit or 64-bit)."""
    return PythonArchitecture.AMD64 if sys.maxsize > 2**32 else PythonArchitecture.WIN32
