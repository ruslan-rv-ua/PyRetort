from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BuildResult:
    """Where a build put its output.

    ``app_dir`` is the self-contained application folder build/<dist_name>/;
    ``archive`` is dist/<dist_name>.zip, or None when create_dist_zip_file is
    false.
    """

    app_dir: Path
    archive: Path | None
