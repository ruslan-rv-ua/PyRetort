from __future__ import annotations

import hashlib

from pyretort.types import PythonArchitecture


def calculate_environment_hash(
    python_version: str,
    python_architecture: PythonArchitecture,
    requirements: list[str],
) -> str:
    data = (
        f"{python_version}|{python_architecture.value}|{'|'.join(sorted(requirements))}"
    )
    return hashlib.sha256(data.encode()).hexdigest()


def make_folder_name_from_hash(env_hash: str) -> str:
    """Create a folder name based on the environment hash.

    Args:
        env_hash: The hash string representing the environment.

    Returns:
        A string suitable for use as a folder name.
    """
    return f"python_{env_hash[:16]}"
