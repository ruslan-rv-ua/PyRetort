from __future__ import annotations

import sys

import typer

from pyretort.cli._output import echo
from pyretort.cli.commands.build import build_command
from pyretort.cli.commands.check import check_command
from pyretort.cli.commands.init import init_command
from pyretort.cli.commands.version import version_command

# from pyretort.cli.commands.clean import cleanup_command

app = typer.Typer(
    name="pyretort",
    help="PyRetort - Package Python projects into standalone Windows applications.",
    add_completion=False,
)


def _ensure_windows_platform(ctx: typer.Context) -> None:
    """Abort when running on non-Windows platforms."""

    if sys.platform != "win32":
        echo(ctx, "PyRetort currently supports Windows only.", err=True)
        echo(ctx, f"Detected platform: {sys.platform}", err=True)
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def cli_entry(
    ctx: typer.Context,
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all CLI output.",
    ),
) -> None:
    """Main CLI callback that enforces platform requirements."""

    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet

    _ensure_windows_platform(ctx)

    if ctx.invoked_subcommand is None:
        echo(ctx, ctx.get_help())
        raise typer.Exit()


app.command(name="version")(version_command)
app.command(name="init")(init_command)
app.command(name="check")(check_command)
app.command(name="build")(build_command)
# app.command(name="cleanup")(cleanup_command)
