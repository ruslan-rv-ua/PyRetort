"""Minimal console application for the PyRetort hello-cli example."""

from __future__ import annotations

import platform
import sys


def main() -> None:
    """Print a greeting, the running Python and the command-line arguments."""
    print("Hello from hello-cli!")
    print(f"Python {platform.python_version()} at {sys.executable}")
    print(f"Arguments: {sys.argv[1:]}")
