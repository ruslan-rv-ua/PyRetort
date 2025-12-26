from __future__ import annotations

from pathlib import Path

import typer

from pyretort.cli._output import echo
from pyretort.types import BuildConfig


def check_command(
    ctx: typer.Context,
    pyproject_toml: Path = typer.Option(
        Path.cwd() / "pyproject.toml",
        "--pyproject-toml",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a pyproject.toml file to validate.",
    ),
) -> None:
    """Validate configuration file structure and referenced paths."""

    pyproject_toml = pyproject_toml.resolve()

    try:
        BuildConfig.from_pyproject_toml(pyproject_toml)
    except (FileNotFoundError, ValueError) as exc:
        echo(ctx, f"Configuration validation failed: {exc}", err=True)
        raise typer.Exit(1)

    echo(ctx, f"Configuration at {pyproject_toml} is valid.")
