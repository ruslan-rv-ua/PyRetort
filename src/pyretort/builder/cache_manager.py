from __future__ import annotations

import os
import shutil
from pathlib import Path


class CacheManager:
    """Manage operations on a cache directory."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def __contains__(self, item: str | Path) -> bool:
        """Check if an item exists in the cache directory."""
        return (self._cache_dir / item).exists()

    def get_path(self) -> Path:
        """Return the cache directory path."""

        return self._cache_dir

    def cleanup(self) -> None:
        """Remove all contents from the cache directory."""

        if not self._cache_dir.exists():
            return

        for entry in self._cache_dir.iterdir():
            try:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(entry)
                else:
                    entry.unlink(missing_ok=True)
            except FileNotFoundError:
                continue

    def get_size(self) -> int:
        """Return the total size of the cache directory in bytes."""

        if not self._cache_dir.exists():
            return 0

        total_size = 0

        for root, _, files in os.walk(self._cache_dir, followlinks=False):
            root_path = Path(root)
            for file_name in files:
                file_path = root_path / file_name
                try:
                    total_size += file_path.stat(follow_symlinks=False).st_size
                except FileNotFoundError:
                    continue

        return total_size

    def remove(self) -> None:
        """Delete the cache directory itself (and everything under it).

        If the directory does not exist this is a no-op. Any unexpected
        OSErrors (permissions, etc.) are propagated to the caller.
        """

        if not self._cache_dir.exists():
            return
        shutil.rmtree(self._cache_dir)
