from __future__ import annotations

import shutil

from pyretort.constants import (
    BUILD_DIR_DEFAULT,
    DIST_DIR_DEFAULT,
    DOWNLOAD_DIR_DEFAULT,
)
from pyretort.types import BuildConfig


class BaseBuilder:
    """Paths of a build and the directory setup every builder shares.

    Constructing a builder only computes paths; nothing touches the disk
    until ``prepare_directories`` runs.
    """

    def __init__(self, config: BuildConfig) -> None:
        self.config = config
        self.download_path = self.config.project_dir_abs_path / DOWNLOAD_DIR_DEFAULT
        self.build_path = self.config.project_dir_abs_path / BUILD_DIR_DEFAULT
        self.dist_path = self.config.project_dir_abs_path / DIST_DIR_DEFAULT
        self.app_path = self.build_path / self.config.dist_name
        self.source_dist_path = self.app_path / self.config.project_name_slug_dash

    def prepare_directories(self) -> None:
        """Create downloads/, build/ and dist/; start build/<dist_name>/ from scratch."""
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.build_path.mkdir(parents=True, exist_ok=True)
        self.dist_path.mkdir(parents=True, exist_ok=True)
        if self.app_path.exists():
            shutil.rmtree(self.app_path)
        self.app_path.mkdir(parents=True)
