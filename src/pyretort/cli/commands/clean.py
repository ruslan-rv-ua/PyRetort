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

    succeeded: list[bool] = []
    if do_cache:
        succeeded.append(_cleanup_cache(ctx, project_dir))

    if do_build:
        succeeded.append(_cleanup_build(ctx, project_dir))

    if not all(succeeded):
        echo(
            ctx,
            "Cleanup incomplete: some directories could not be removed.",
            err=True,
        )
        raise typer.Exit(1)

    echo(ctx, "Cleanup complete.")


def _cleanup_dir(ctx: typer.Context, path: Path, description: str) -> bool:
    """Remove a directory if it exists; return False if removing it failed."""
    if path.exists():
        try:
            shutil.rmtree(path)
            echo(ctx, f"Removed {description}: {path}")
        except OSError as e:
            echo(ctx, f"Error removing {description} '{path}': {e}", err=True)
            return False
    else:
        echo(ctx, f"{description} not found: {path}")
    return True


def _cleanup_cache(ctx: typer.Context, project_dir: Path) -> bool:
    """Clean up the cache directory; return False if that failed."""
    return _cleanup_dir(ctx, project_dir / DOWNLOAD_DIR_DEFAULT, "cache directory")


def _cleanup_build(ctx: typer.Context, project_dir: Path) -> bool:
    """Clean up the build and dist directories; return False if either failed.

    Both directories are attempted even if the first one fails.
    """
    build_ok = _cleanup_dir(ctx, project_dir / BUILD_DIR_DEFAULT, "build directory")
    dist_ok = _cleanup_dir(ctx, project_dir / DIST_DIR_DEFAULT, "dist directory")
    return build_ok and dist_ok
