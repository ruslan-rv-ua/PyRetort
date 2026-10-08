from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import httpx

from .base_builder import BaseBuilder
from .downloader import Downloader
from .errors import BuildError
from .exe_generator import generate_exe
from .pydist_manager import PydistManager
from .result import BuildResult

UV_INSTALL_URL = "https://docs.astral.sh/uv/getting-started/installation/"


class UVBuilder(BaseBuilder):
    """Build build/<dist_name>/: embedded Python, the project via uv, a launcher.

    With create_dist_zip_file the folder is also packed into dist/<dist_name>.zip.
    """

    def build(self) -> BuildResult:
        """Build the distribution and return where it went.

        Raise BuildError for every expected failure.
        """
        if shutil.which("uv") is None:
            raise BuildError(f"uv was not found in PATH. Install uv: {UV_INSTALL_URL}")
        self.log(f"Preparing build directory {self.app_path}")
        self.prepare_directories()
        if self.config.install_as_package:
            self._build_as_package()
        else:
            self._build_as_standalone()
        archive: Path | None = None
        if self.config.create_dist_zip_file:
            archive = self.create_archive()
            self.log(f"Created archive {archive}")
        self.log(f"Build complete: {self.app_path}")
        return BuildResult(app_dir=self.app_path, archive=archive)

    def _build_as_standalone(self) -> None:
        # Implementation for building installing dependencies, then copy source files
        raise NotImplementedError("Standalone build not implemented yet.")

    def _build_as_package(self) -> None:
        pydist_manager = self._install_embedded_python()
        pydist_manager.patch_pth_file(
            version=self.config.python_version, relative_path_to_source="."
        )
        self.log("Installing project with uv")
        self._uv_pip_install(
            pydist_manager.python_executable, str(self.config.project_dir_abs_path)
        )
        python_exe_relative = pydist_manager.python_executable.relative_to(
            self.app_path
        )
        main_module = self.config.main_module
        self._generate_launcher(
            f'"{{EXE_DIR}}\\{python_exe_relative}" -m {main_module}'
        )

    def _install_embedded_python(self) -> PydistManager:
        """Download and unpack the embedded Python into build/<dist_name>/<name>/.

        Return the manager of that Python. Raise BuildError when python.org has
        no embeddable package for the version or the download fails.
        """
        downloader = Downloader(self.download_path)
        pydist_manager = PydistManager(self.source_dist_path, downloader=downloader)
        version = self.config.python_version
        architecture = self.config.python_architecture
        self.log(f"Installing embedded Python {version} ({architecture})")
        try:
            pydist_manager.install_embedded_python(
                version=version, architecture=architecture
            )
        except httpx.HTTPError as e:
            if (
                isinstance(e, httpx.HTTPStatusError)
                and e.response.status_code == httpx.codes.NOT_FOUND
            ):
                raise BuildError(
                    "python.org has no Windows embeddable package for Python "
                    f"{version} ({architecture}): {e.request.url}\n"
                    "Security-only releases ship no Windows binaries; "
                    "set python_version to a release that has one."
                ) from e
            raise BuildError(
                f"Could not download the embedded Python {version} "
                f"({architecture}): {e}\n"
                "Check the internet connection and run the build again."
            ) from e
        return pydist_manager

    def _uv_pip_install(self, python_executable: Path, *args: str) -> None:
        """Run 'uv pip install --python <python_executable> <args>'.

        Raise BuildError with uv's exit code and stderr when it fails.
        """
        command = ["uv", "pip", "install", "--python", str(python_executable), *args]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise BuildError(
                f"uv pip install failed with exit code {e.returncode}:\n{e.stderr}"
            ) from e

    def _generate_launcher(self, command: str) -> None:
        """Write build/<dist_name>/<name>.exe, the launcher that runs command.

        Raise BuildError when the command is longer than the launcher can hold.
        """
        exe_path = self.app_path / f"{self.config.project_name_slug_dash}.exe"
        self.log(f"Generating launcher {exe_path}")
        try:
            generate_exe(
                target=exe_path,
                command=command,
                icon_file=self.config.icon_file_abs_path,
                show_console=self.config.show_console_window,
                architecture=self.config.python_architecture,
            )
        except ValueError as e:
            raise BuildError(str(e)) from e
