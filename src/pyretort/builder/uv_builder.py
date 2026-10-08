from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from fnmatch import fnmatch
from pathlib import Path

import httpx

from pyretort.constants import DEFAULT_BLACKLIST, PROJECT_ROOT_EXCLUDES

from .base_builder import BaseBuilder
from .downloader import Downloader
from .errors import BuildError
from .exe_generator import generate_exe
from .pydist_manager import PydistManager
from .result import BuildResult

UV_INSTALL_URL = "https://docs.astral.sh/uv/getting-started/installation/"

# The standalone build copies the sources into this subfolder of the embedded
# Python: build/<dist_name>/<name>/app/.
SOURCES_DIR_NAME = "app"


def _source_ignore(project_root: Path) -> Callable[[str, list[str]], set[str]]:
    """Return the copytree ignore callback of the standalone source copy.

    DEFAULT_BLACKLIST applies at every depth, PROJECT_ROOT_EXCLUDES only to
    the entries of the project root itself. Names match case-insensitively,
    like shutil.ignore_patterns.
    """
    root = project_root.resolve()

    def ignore(directory: str, names: list[str]) -> set[str]:
        patterns = list(DEFAULT_BLACKLIST)
        if Path(directory).resolve() == root:
            patterns += PROJECT_ROOT_EXCLUDES
        return {
            name
            for name in names
            if any(fnmatch(name, pattern) for pattern in patterns)
        }

    return ignore


def _copy_error_text(error: OSError) -> str:
    """Return the text of a copy error.

    shutil.copytree finishes the copy and then raises shutil.Error with one
    (source, target, reason) entry per file that failed; the reason alone
    does not always name the file.
    """
    if isinstance(error, shutil.Error) and isinstance(error.args[0], list):
        return "\n".join(f"{source}: {reason}" for source, _, reason in error.args[0])
    return str(error)


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
        main_file = self.config.main_file_rel_path
        if main_file is None:
            raise BuildError(
                "Standalone mode (install_as_package = false) requires 'main_file' "
                "in [tool.pyretort]"
            )
        pydist_manager = self._install_embedded_python()
        # A ._pth file puts Python into isolated mode, which keeps the script's
        # folder off sys.path; list it, as sys.path[0] would be otherwise.
        script_dir = Path(SOURCES_DIR_NAME) / main_file.parent
        pydist_manager.patch_pth_file(
            version=self.config.python_version, extra_paths=[str(script_dir)]
        )
        sources_path = self.source_dist_path / SOURCES_DIR_NAME
        self._copy_sources(sources_path)
        self.log("Installing dependencies with uv")
        # With -r pyproject.toml uv installs only [project].dependencies:
        # neither the project itself nor its dependency groups.
        self._uv_pip_install(
            pydist_manager.python_executable,
            "-r",
            str(self.config.project_dir_abs_path / "pyproject.toml"),
        )
        python_exe = self._launcher_path(pydist_manager.python_executable)
        script = self._launcher_path(sources_path / main_file)
        self._generate_launcher(f'"{python_exe}" "{script}"')

    def _copy_sources(self, target: Path) -> None:
        """Copy project_source_subdir into target without development files.

        Raise BuildError when a file cannot be copied, e.g. because another
        program holds it open.
        """
        source = (
            self.config.project_dir_abs_path
            / self.config.project_source_subdir_rel_path
        )
        self.log(f"Copying sources to {target}")
        try:
            shutil.copytree(
                source, target, ignore=_source_ignore(self.config.project_dir_abs_path)
            )
        except OSError as e:
            raise BuildError(
                f"Could not copy the sources to {target}: {_copy_error_text(e)}\n"
                "Close the programs that use the files, then run the build again."
            ) from e

    def _build_as_package(self) -> None:
        pydist_manager = self._install_embedded_python()
        pydist_manager.patch_pth_file(version=self.config.python_version)
        self.log("Installing project with uv")
        self._uv_pip_install(
            pydist_manager.python_executable, str(self.config.project_dir_abs_path)
        )
        python_exe = self._launcher_path(pydist_manager.python_executable)
        self._generate_launcher(f'"{python_exe}" -m {self.config.main_module}')

    def _launcher_path(self, path: Path) -> str:
        """Return a path inside build/<dist_name>/ as the launcher command names it.

        The launcher replaces {EXE_DIR} with its own directory at run time.
        """
        return f"{{EXE_DIR}}\\{path.relative_to(self.app_path)}"

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
