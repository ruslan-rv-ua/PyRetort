from pathlib import Path

import typer

from pyretort.types import BuildBackend, BuildConfig


def build_command(
    ctx: typer.Context,
    pyproject_toml: Path = typer.Option(
        Path.cwd() / "pyproject.toml",
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
    except Exception as e:
        typer.echo(f"Error loading configuration from {pyproject_toml}: {e}", err=True)
        raise typer.Exit(1)

    match config.build_backend:
        case BuildBackend.UV:
            from pyretort.builder.uv_builder import UVBuilder

            builder = UVBuilder(config)
        case other:
            typer.echo(f"Unsupported build tool: {other}", err=True)
            raise typer.Exit(1)

    builder.build()
