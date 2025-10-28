from __future__ import annotations

from pathlib import Path

import typer

from pyretort.cli._output import echo
from pyretort.config_generator import generate_config_file, gether_project_data
from pyretort.constants import CONFIG_FILE_NAME


def init_command(
    ctx: typer.Context,
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-p",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        help="Project directory that should built.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration file if present.",
    ),
    comments: bool = typer.Option(
        False,
        "--comments",
        "-c",
        help="Generate configuration with explanatory comments.",
    ),
) -> None:
    """Generate a starter configuration in the chosen project directory."""

    project_dir = project_dir.resolve()
    if not project_dir.exists() or not project_dir.is_dir():
        echo(ctx, f"Project directory not found: {project_dir}", err=True)
        raise typer.Exit(1)

    config_path = project_dir / CONFIG_FILE_NAME
    if config_path.exists() and not force:
        echo(
            ctx,
            f"{CONFIG_FILE_NAME} already exists in {project_dir}. Use --force to overwrite.",
            err=True,
        )
        raise typer.Exit(1)

    project_data = gether_project_data(project_dir)

    generate_config_file(
        project_root=project_dir, project_data=project_data, with_comments=comments
    )
    echo(ctx, f"Pyretort configuration created at {config_path}")
    echo(ctx, "Next steps:")
    echo(ctx, f"  1. Review and customize {CONFIG_FILE_NAME} as needed.")
    echo(ctx, "  2. Run 'pyretort build' to create the distributable package.")
