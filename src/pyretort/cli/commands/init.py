from __future__ import annotations

import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, cast

import tomlkit
import typer
from slugify import slugify
from tomlkit.items import Table

from pyretort.cli._output import echo
from pyretort.constants import (
    INSTALL_AS_PACKAGE_DEFAULT,
    SHOW_CONSOLE_DEFAULT,
)
from pyretort.types import PythonArchitecture, derive_main_module, missing_dunder_main


def init_command(
    ctx: typer.Context,
    pyproject_toml_path: Path = typer.Option(
        Path.cwd() / "pyproject.toml",  # noqa: B008  # import-time cwd, task 05
        "--pyproject-toml",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        help="Path to the pyproject.toml file of the target project.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite an existing [tool.pyretort] section.",
    ),
) -> None:
    """Initialize a PyRetort configuration file for a Python project."""

    pyproject_toml_path = pyproject_toml_path.resolve()
    project_path = pyproject_toml_path.parent

    pyproject_data = tomlkit.parse(pyproject_toml_path.read_text(encoding="utf-8"))
    if _has_pyretort_section(pyproject_data) and not force:
        echo(
            ctx,
            "pyproject.toml already contains [tool.pyretort]; use --force to overwrite",
            err=True,
        )
        raise typer.Exit(1)

    project_name = str(pyproject_data.get("project", {}).get("name", ""))
    source_subdir = _find_project_source_subdir(project_path, project_name)
    _set_pyretort_section(
        pyproject_data, _build_pyretort_section(project_path, source_subdir)
    )
    pyproject_toml_path.write_text(tomlkit.dumps(pyproject_data), encoding="utf-8")

    echo(ctx, f"pyproject.toml updated successfully at: {pyproject_toml_path}")
    echo(ctx, "Next steps:")
    echo(
        ctx,
        "  1. Review and customize the [tool.pyretort] section in pyproject.toml as needed.",
    )
    echo(ctx, "  2. Run 'pyretort build' to create the distributable package.")

    main_module = derive_main_module(Path(source_subdir), project_name)
    dunder_main = missing_dunder_main(project_path, Path(source_subdir), main_module)
    if dunder_main is not None:
        echo(
            ctx,
            f"warning: {dunder_main} not found; "
            "'pyretort build' will fail until it exists",
        )


def _has_pyretort_section(pyproject_data: tomlkit.TOMLDocument) -> bool:
    """Return True if the document already has a [tool.pyretort] section."""
    tool_section = cast(MutableMapping[str, Any], pyproject_data.get("tool", {}))
    return "pyretort" in tool_section


def _set_pyretort_section(
    pyproject_data: tomlkit.TOMLDocument, pyretort_config: Table
) -> None:
    """Store the section as [tool.pyretort], replacing any existing one."""
    if "tool" not in pyproject_data:
        pyproject_data["tool"] = tomlkit.table()

    # A Table, or an OutOfOrderTableProxy when [tool.*] tables are scattered.
    tool_section = cast(MutableMapping[str, Any], pyproject_data["tool"])
    tool_section["pyretort"] = pyretort_config


def _build_pyretort_section(project_path: Path, source_subdir: str) -> Table:
    """Build the commented [tool.pyretort] section for the project."""

    pyretort_config: Table = tomlkit.table()

    pyretort_config.add(
        tomlkit.comment(
            "Path to the project source directory relative to the project root"
        )
    )
    pyretort_config.add(
        tomlkit.comment(
            "The launcher runs 'python -m <last path component>' "
            '(the project name slug when ".")'
        )
    )
    pyretort_config["project_source_subdir"] = source_subdir

    pyretort_config.add(
        tomlkit.comment(
            "Name of the main Python file to execute (e.g., main.py, app.py)"
        )
    )
    pyretort_config.add(
        tomlkit.comment("Used only when install_as_package = false; ignored otherwise")
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
    pyretort_config.add(
        tomlkit.comment("Must be true: standalone mode (false) is not supported yet")
    )
    pyretort_config["install_as_package"] = INSTALL_AS_PACKAGE_DEFAULT

    pyretort_config.add(
        tomlkit.comment("Python version to use for the bundled distribution")
    )
    pyretort_config["python_version"] = _find_python_version()

    pyretort_config.add(
        tomlkit.comment(f"Python architecture to use ({', '.join(PythonArchitecture)})")
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

    return pyretort_config


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
