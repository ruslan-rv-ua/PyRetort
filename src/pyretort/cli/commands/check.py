from __future__ import annotations

from pathlib import Path

import typer

from pyretort.cli._output import echo
from pyretort.constants import CONFIG_FILE_NAME
from pyretort.types import BuildConfig


def check_command(
    ctx: typer.Context,
    config: Path = typer.Option(
        Path(CONFIG_FILE_NAME),
        "--config",
        "-c",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a pyretort TOML configuration file.",
    ),
) -> None:
    """Validate configuration file structure and referenced paths."""

    config_path = config.resolve()

    try:
        BuildConfig.from_toml(config_path)
    except (FileNotFoundError, ValueError) as exc:
        echo(ctx, f"Configuration validation failed: {exc}", err=True)
        raise typer.Exit(1)

    echo(ctx, f"Configuration at {config_path} is valid.")
