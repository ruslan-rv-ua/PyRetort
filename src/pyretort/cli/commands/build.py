from __future__ import annotations

import tomllib

import typer

from pyretort.builder.errors import BuildError
from pyretort.cli._options import PyprojectOption, resolve_pyproject
from pyretort.cli._output import echo
from pyretort.types import BuildConfig


def build_command(ctx: typer.Context, pyproject_toml: PyprojectOption = None) -> None:
    """Build a distributable package based on configuration."""
    pyproject_toml = resolve_pyproject(pyproject_toml)
    if not pyproject_toml.is_file():
        echo(ctx, f"Configuration file not found: {pyproject_toml}", err=True)
        raise typer.Exit(1)

    try:
        config = BuildConfig.from_pyproject_toml(pyproject_toml)
    except tomllib.TOMLDecodeError as e:
        echo(ctx, f"Invalid TOML syntax in {pyproject_toml}: {e}", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        echo(ctx, f"Invalid configuration: {e}", err=True)
        raise typer.Exit(1) from None

    # Imported here so that the CLI starts (and the platform check runs) before
    # pywin32 is loaded, and so that tests can patch UVBuilder in its module.
    from pyretort.builder.uv_builder import UVBuilder

    try:
        UVBuilder(config, log=lambda message: echo(ctx, message)).build()
    except BuildError as e:
        echo(ctx, str(e), err=True)
        raise typer.Exit(1) from None
