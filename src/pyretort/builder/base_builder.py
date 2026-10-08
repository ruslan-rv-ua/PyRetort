from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from pyretort.constants import (
    BUILD_DIR_DEFAULT,
    DIST_DIR_DEFAULT,
    DOWNLOAD_DIR_DEFAULT,
)
from pyretort.types import BuildConfig

from .errors import BuildError


class BaseBuilder:
    """Paths of a build and the steps every builder shares: directories, archive.

    Constructing a builder only computes paths; nothing touches the disk
    until ``prepare_directories`` runs. ``log`` receives one progress message
    per build stage; the default discards them.
    """

    def __init__(
        self, config: BuildConfig, log: Callable[[str], None] = lambda _: None
    ) -> None:
        self.config = config
        self.log = log
        self.download_path = self.config.project_dir_abs_path / DOWNLOAD_DIR_DEFAULT
        self.build_path = self.config.project_dir_abs_path / BUILD_DIR_DEFAULT
        self.dist_path = self.config.project_dir_abs_path / DIST_DIR_DEFAULT
        self.app_path = self.build_path / self.config.dist_name
        self.source_dist_path = self.app_path / self.config.project_name_slug_dash
        self.archive_path = self.dist_path / f"{self.config.dist_name}.zip"

    def prepare_directories(self) -> None:
        """Create downloads/, build/ and dist/; start build/<dist_name>/ from scratch.

        Raise BuildError when a directory cannot be created or the previous
        build cannot be removed, e.g. because its application still runs.
        """
        try:
            self.download_path.mkdir(parents=True, exist_ok=True)
            self.build_path.mkdir(parents=True, exist_ok=True)
            self.dist_path.mkdir(parents=True, exist_ok=True)
            if self.app_path.exists():
                shutil.rmtree(self.app_path)
            self.app_path.mkdir(parents=True)
        except OSError as e:
            raise BuildError(
                f"Could not prepare the build directory {self.app_path}: {e}\n"
                "Close the application from the previous build and other "
                "programs that use its files, then run the build again."
            ) from e

    def create_archive(self) -> Path:
        """Pack build/<dist_name>/ into dist/<dist_name>.zip and return its path.

        Every entry starts with '<dist_name>/', so the archive unpacks into a
        single folder. An archive left by an earlier build is overwritten.
        Raise BuildError when the archive cannot be written, e.g. because
        another program holds it open.
        """
        try:
            # make_archive appends ".zip" to base_name itself.
            shutil.make_archive(
                base_name=str(self.archive_path.with_suffix("")),
                format="zip",
                root_dir=self.build_path,
                base_dir=self.config.dist_name,
            )
        except OSError as e:
            raise BuildError(
                f"Could not write the archive {self.archive_path}: {e}\n"
                "Close the programs that use the archive, then run the build again."
            ) from e
        return self.archive_path
