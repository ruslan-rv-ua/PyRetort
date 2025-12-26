from __future__ import annotations

import subprocess

from .base_builder import BaseBuilder
from .downloader import Downloader
from .exe_generator import generate_exe
from .pydist_manager import PydistManager


class UVBuilder(BaseBuilder):
    def build(self) -> None:
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
        subprocess.run(
            command,
            # cwd=self.pydist_path,
            capture_output=True,
            text=True,
            check=True,
        )
        python_exe_relative = pydist_manager.python_executable.relative_to(
            self.app_path
        )
        package_name = self.config.project_name_slug_underscore
        command_str = f'"{{EXE_DIR}}\\{python_exe_relative}" -m {package_name}'
        exe_file_name = f"{self.config.project_name_slug_dash}.exe"
        generate_exe(
            target=self.app_path / exe_file_name,
            command=command_str,
            icon_file=self.config.icon_file_rel_path,
            show_console=self.config.show_console_window,
        )
