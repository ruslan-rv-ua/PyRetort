from __future__ import annotations

from importlib import metadata

import typer

from pyretort.cli._output import echo


def version_command(ctx: typer.Context) -> None:
    """Display the installed PyRetort version."""

    try:
        current_version = metadata.version("pyretort")
    except metadata.PackageNotFoundError:
        current_version = "unknown"

    echo(ctx, f"PyRetort {current_version}")
