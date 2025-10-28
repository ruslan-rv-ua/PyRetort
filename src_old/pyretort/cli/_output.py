from __future__ import annotations

import typer


def echo(ctx: typer.Context, message: str, *, err: bool = False) -> None:
    """Write a message unless the CLI runs in quiet mode."""

    ctx_data = ctx.obj or {}
    if ctx_data.get("quiet"):
        return

    typer.echo(message, err=err)
