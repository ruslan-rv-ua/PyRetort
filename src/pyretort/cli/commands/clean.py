from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer

from pyretort.cli._output import echo
from pyretort.constants import (
    BUILD_DIR_DEFAULT,
    DIST_DIR_DEFAULT,
    DOWNLOAD_DIR_DEFAULT,
)

VALID_TARGETS = ["cache", "build", "all"]


def cleanup_command(
    ctx: typer.Context,
    targets: Annotated[
        list[str] | None,
        typer.Argument(
            help=(
                "What to remove: 'cache' (downloads/), 'build' (build/ and dist/) "
                "or 'all'. Defaults to 'all'."
            ),
        ),
    ] = None,
    pyproject_toml: Annotated[
        Path | None,
        typer.Option(
            "--pyproject-toml",
            "-p",
            help=(
                "Path to the pyproject.toml of the project to clean. "
                "Defaults to pyproject.toml in the current directory."
            ),
        ),
    ] = None,
) -> None:
    """Remove build artifacts that PyRetort produced.

    Artifact directories are looked up next to pyproject.toml, not in the
    current directory.
    """
    if pyproject_toml is None:
        pyproject_toml = Path.cwd() / "pyproject.toml"
    pyproject_toml = pyproject_toml.resolve()
    if not pyproject_toml.is_file():
        echo(ctx, f"Configuration file not found: {pyproject_toml}", err=True)
        raise typer.Exit(1)
    project_dir = pyproject_toml.parent

    if not targets:
        targets = ["all"]

    invalid_targets = [
        target for target in targets if target.lower() not in VALID_TARGETS
    ]
    if invalid_targets:
        echo(
            ctx,
            f"Invalid cleanup targets: {', '.join(invalid_targets)}. "
            f"Valid targets are: {', '.join(VALID_TARGETS)}.",
            err=True,
        )
        raise typer.Exit(1)

    lower_targets = {target.lower() for target in targets}
    do_cache = "cache" in lower_targets or "all" in lower_targets
    do_build = "build" in lower_targets or "all" in lower_targets

    if do_cache:
        _cleanup_cache(ctx, project_dir)

    if do_build:
        _cleanup_build(ctx, project_dir)

    echo(ctx, "Cleanup complete.")


def _cleanup_dir(ctx: typer.Context, path: Path, description: str) -> None:
    """Remove a directory if it exists."""
    if path.exists():
        try:
            shutil.rmtree(path)
            echo(ctx, f"Removed {description}: {path}")
        except OSError as e:
            echo(ctx, f"Error removing {description} '{path}': {e}", err=True)
    else:
        echo(ctx, f"{description} not found: {path}")


def _cleanup_cache(ctx: typer.Context, project_dir: Path) -> None:
    """Clean up the cache directory."""
    _cleanup_dir(ctx, project_dir / DOWNLOAD_DIR_DEFAULT, "cache directory")


def _cleanup_build(ctx: typer.Context, project_dir: Path) -> None:
    """Clean up the build and dist directories."""
    _cleanup_dir(ctx, project_dir / BUILD_DIR_DEFAULT, "build directory")
    _cleanup_dir(ctx, project_dir / DIST_DIR_DEFAULT, "dist directory")
