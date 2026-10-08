from __future__ import annotations

import shutil
import subprocess

from .base_builder import BaseBuilder
from .downloader import Downloader
from .errors import BuildError
from .exe_generator import generate_exe
from .pydist_manager import PydistManager

UV_INSTALL_URL = "https://docs.astral.sh/uv/getting-started/installation/"


class UVBuilder(BaseBuilder):
    def build(self) -> None:
        """Build the distribution; raise BuildError for every expected failure."""
        if shutil.which("uv") is None:
            raise BuildError(f"uv was not found in PATH. Install uv: {UV_INSTALL_URL}")
        self._create_directories()
        if self.config.install_as_package:
            self._build_as_package()
        else:
            self._build_as_standalone()

    def _build_as_standalone(self) -> None:
        # Implementation for building installing dependencies, then copy source files
        raise NotImplementedError("Standalone build not implemented yet.")

    def _build_as_package(self) -> None:
        downloader = Downloader(self.download_path)
        pydist_manager = PydistManager(self.source_dist_path, downloader=downloader)
        pydist_manager.install_embedded_python(
            version=self.config.python_version,
            architecture=self.config.python_architecture,
        )
        pydist_manager.patch_pth_file(
            version=self.config.python_version, relative_path_to_source="."
        )
        command = [
            "uv",
            "pip",
            "install",
            "--python",
            str(pydist_manager.python_executable),
            str(self.config.project_dir_abs_path),
        ]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise BuildError(
                f"uv pip install failed with exit code {e.returncode}:\n{e.stderr}"
            ) from e
        python_exe_relative = pydist_manager.python_executable.relative_to(
            self.app_path
        )
        main_module = self.config.main_module
        command_str = f'"{{EXE_DIR}}\\{python_exe_relative}" -m {main_module}'
        exe_file_name = f"{self.config.project_name_slug_dash}.exe"
        generate_exe(
            target=self.app_path / exe_file_name,
            command=command_str,
            icon_file=self.config.icon_file_rel_path,
            show_console=self.config.show_console_window,
        )
