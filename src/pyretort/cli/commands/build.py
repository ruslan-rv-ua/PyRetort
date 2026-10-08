from __future__ import annotations

import tomllib
from pathlib import Path

import typer

from pyretort.builder.errors import BuildError
from pyretort.cli._output import echo
from pyretort.types import BuildConfig


def build_command(
    ctx: typer.Context,
    pyproject_toml: Path = typer.Option(
        Path.cwd() / "pyproject.toml",  # noqa: B008  # import-time cwd, task 05
        "--pyproject-toml",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a pyproject.toml file.",
    ),
) -> None:
    """Build a distributable package based on configuration."""
    try:
        config = BuildConfig.from_pyproject_toml(pyproject_toml)
    except FileNotFoundError:
        echo(ctx, f"Configuration file not found: {pyproject_toml}", err=True)
        raise typer.Exit(1) from None
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
