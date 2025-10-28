from __future__ import annotations

import shutil
from pathlib import Path

import typer

from pyretort.builder.build_manager import BuildManager
from pyretort.builder.cache_manager import CacheManager
from pyretort.builder.hash_utils import (
    calculate_environment_hash,
    make_folder_name_from_hash,
)
from pyretort.builder.pydist_manager import PydistManager
from pyretort.constants import CONFIG_FILE_NAME
from pyretort.types import BuildConfig


def build_command(
    ctx: typer.Context,
    config: Path = typer.Option(
        Path.cwd() / CONFIG_FILE_NAME,
        "--config",
        "-c",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a pyretort TOML configuration file.",
    ),
) -> None:
    """Build a distributable package based on configuration."""
    try:
        conf = BuildConfig.from_toml(config)
    except Exception as e:
        typer.echo(f"Error loading configuration from {config}: {e}", err=True)
        raise typer.Exit(1)
    cache = CacheManager(conf.download_cache_dir_absolute)

    # TODO: clear build folder if it exists

    # Calculate hash of Python version, architecture and requirements
    env_hash = calculate_environment_hash(
        python_version=conf.python_version,
        python_architecture=conf.python_architecture,
        requirements=conf.requirements,
    )
    folder_name = make_folder_name_from_hash(env_hash)
    cached_pydist_dir = cache.get_path() / folder_name
    if cached_pydist_dir.exists():
        typer.echo("Using cached python distribution with requirements installed.")
    else:
        typer.echo("Creating new python distribution")
        try:
            # TODO: echo progress info
            pydist_manager = PydistManager(pydist_path=cached_pydist_dir, config=conf)
            pydist_manager.install_embedded_python()
            pydist_manager.install_pip()
            pydist_manager.install_requirements()
        except Exception as e:
            typer.echo(f"Error initializing PydistManager: {e}", err=True)
            # remove cached_pydist_dir with all its contents
            shutil.rmtree(cached_pydist_dir, ignore_errors=True)
            raise typer.Exit(1)
    builder = BuildManager(conf)
    builder.copy_python_interpreter(copy_from=cached_pydist_dir)
    builder.copy_source_files()
    builder.make_executable()
    # step 7. create distributable package (zip, installer, etc)
    pass
