from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

PyprojectOption = Annotated[
    Path | None,
    typer.Option(
        "--pyproject-toml",
        "-p",
        help=(
            "Path to the pyproject.toml of the project. "
            "Defaults to pyproject.toml in the current directory."
        ),
    ),
]
"""The ``-p`` option every command shares; None means "look in cwd at call time"."""


def resolve_pyproject(path: Path | None) -> Path:
    """Return the absolute pyproject.toml path, defaulting to the current directory.

    The default is computed when the command runs, not when the module is
    imported. Whether the file exists is for the command to check.
    """
    return (path or Path.cwd() / "pyproject.toml").resolve()
