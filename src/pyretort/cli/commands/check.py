from __future__ import annotations

import typer

from pyretort.cli._options import PyprojectOption, resolve_pyproject
from pyretort.cli._output import echo
from pyretort.types import BuildConfig


def check_command(ctx: typer.Context, pyproject_toml: PyprojectOption = None) -> None:
    """Validate configuration file structure and referenced paths."""

    pyproject_toml = resolve_pyproject(pyproject_toml)
    if not pyproject_toml.is_file():
        echo(ctx, f"Configuration file not found: {pyproject_toml}", err=True)
        raise typer.Exit(1)

    try:
        BuildConfig.from_pyproject_toml(pyproject_toml)
    except ValueError as exc:
        echo(ctx, f"Configuration validation failed: {exc}", err=True)
        raise typer.Exit(1) from None

    echo(ctx, f"Configuration at {pyproject_toml} is valid.")
