from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

import typer
from typing_extensions import Annotated

from pyretort.cli._output import echo
from pyretort.constants import (
    BUILD_DIR_DEFAULT,
    DIST_DIR_DEFAULT,
    DOWNLOAD_DIR_DEFAULT,
)

VALID_TARGETS = ["cache", "build", "all"]


def complete_cleanup_targets(incomplete: str) -> list[str]:
    """Provide completion for cleanup targets."""
    return [target for target in VALID_TARGETS if target.startswith(incomplete.lower())]


def cleanup_command(
    ctx: typer.Context,
    targets: Annotated[
        List[str],
        typer.Argument(
            help="The artifacts to clean. Can be 'cache', 'build', or 'all'.",
            autocompletion=complete_cleanup_targets,
        ),
    ],
) -> None:
    """Remove build artifacts that PyRetort produced."""
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
    do_cache = "cache" in lower_targets
    do_build = "build" in lower_targets
    do_all = "all" in lower_targets

    if do_all:
        do_cache = True
        do_build = True

    if do_cache:
        _cleanup_cache(ctx)

    if do_build:
        _cleanup_build(ctx)

    if do_all:
        _cleanup_config(ctx)

    echo(ctx, "Cleanup complete.")


def _cleanup_dir(ctx: typer.Context, dir_path: str, description: str) -> None:
    """Remove a directory if it exists."""
    path = Path(dir_path)
    if path.exists():
        try:
            shutil.rmtree(path)
            echo(ctx, f"Removed {description}: {path}")
        except OSError as e:
            echo(ctx, f"Error removing {description} '{path}': {e}", err=True)
    else:
        echo(ctx, f"{description} not found: {path}")


def _cleanup_file(ctx: typer.Context, file_path: str, description: str) -> None:
    """Remove a file if it exists."""
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
            echo(ctx, f"Removed {description}: {path}")
        except OSError as e:
            echo(ctx, f"Error removing {description} '{path}': {e}", err=True)
    else:
        echo(ctx, f"{description} not found: {path}")


def _cleanup_cache(ctx: typer.Context) -> None:
    """Clean up the cache directory."""
    _cleanup_dir(ctx, DOWNLOAD_DIR_DEFAULT, "cache directory")


def _cleanup_build(ctx: typer.Context) -> None:
    """Clean up the build and dist directories."""
    _cleanup_dir(ctx, BUILD_DIR_DEFAULT, "build directory")
    _cleanup_dir(ctx, DIST_DIR_DEFAULT, "dist directory")
