"""Minimal console script for the PyRetort hello-script example."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

from helper import GREETING


def main() -> None:
    """Print the greeting and a table with the Python, the script and the arguments."""
    console = Console(markup=False)
    console.print(GREETING)
    table = Table(box=box.SQUARE, show_header=False)
    table.add_row("Python", platform.python_version())
    table.add_row("Script", str(Path(__file__).resolve()))
    table.add_row("Arguments", str(sys.argv[1:]))
    console.print(table)


if __name__ == "__main__":
    main()
