from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

from pyretort.builder.downloader import Downloader
from pyretort.types import BuildConfig

PYTHON_URL = "https://www.python.org/ftp/python"
GET_PIP_SCRIPT_URL = "https://bootstrap.pypa.io/get-pip.py"


class PydistManager:
    """Manage a embedded Python distribution"""

    def __init__(self, pydist_path: Path, config: BuildConfig) -> None:
        pydist_path.mkdir(parents=True, exist_ok=False)  # raise error if exists
        self._pydist_path = pydist_path
        self._config = config
        self._downloader = Downloader(
            download_dir_path=config.download_cache_dir_absolute
        )

    def install_embedded_python(self):
        """Download and extract embedded Python distribution."""
        archive_path = self._download_embedded_python()
        self._extract_embedded_python(archive_path)
        self._unzip_pythonzip_file()
        self._verify_embedded_python()

    def install_pip(self):
        """Downloads get-pip.py and runs it with the embedded Python."""
        downloaded_get_pip_path = self._downloader.download(
            GET_PIP_SCRIPT_URL, "get-pip.py"
        )
        target_get_pip_path = self._pydist_path / "get-pip.py"
        shutil.copy2(downloaded_get_pip_path, target_get_pip_path)
        self._run_pip_installation()
        self._patch_pth_file()
        self._verify_pip_installation()

    def install_requirements(self):
        """Install packages from a requirements.txt file into the embedded Python distribution."""
        if not self._config.requirements:
            return
        try:
            self._install_all_requirements_at_once()
        except subprocess.CalledProcessError:
            self._install_requirements_one_by_one()

    def cleanup(self):
        # TODO: remove setuptools/wheel/get-pip.py if needed
        raise NotImplementedError("Method not yet implemented")

    def _download_embedded_python(self) -> Path:
        version = self._config.python_version
        architecture = self._config.python_architecture
        filename = f"python-{version}-embed-{architecture}.zip"
        url = f"{PYTHON_URL}/{version}/{filename}"
        return self._downloader.download(url, filename)

    def _extract_embedded_python(self, archive_path: Path) -> None:
        with ZipFile(archive_path, "r") as zf:
            zf.extractall(path=self._pydist_path)

    def _unzip_pythonzip_file(self):
        """Extract pythonXX.zip to pythonXX.zip directory.

        The embedded Python comes with pythonXX.zip containing the standard library.
        We extract it to a directory so imports work properly after patching `_pth` file.
        """
        pythonzip_file = (
            self._pydist_path / f"python{self._config.python_brief_version}.zip"
        )
        temp_zip = pythonzip_file.with_suffix(".temp_zip")
        pythonzip_file.rename(temp_zip)
        extract_dir = (
            self._pydist_path / f"python{self._config.python_brief_version}.zip"
        )
        extract_dir.mkdir(exist_ok=True)
        with ZipFile(temp_zip, "r") as zf:
            zf.extractall(path=extract_dir)
        temp_zip.unlink()

    def _verify_embedded_python(self) -> None:
        python_executable = self._pydist_path / "python.exe"
        if not python_executable.exists():
            raise RuntimeError(
                "Embedded Python verification failed: python.exe not found."
            )

    def _run_pip_installation(self) -> None:
        """Run the get-pip.py script using the embedded Python interpreter."""
        cmd = [
            str(self._pydist_path / "python.exe"),
            str(self._pydist_path / "get-pip.py"),
            # or "get-pip.py",
            "setuptools",
            "wheel",
            "--no-warn-script-location",
        ]
        subprocess.run(
            cmd,
            cwd=self._pydist_path,
            capture_output=True,
            text=True,
            check=True,
        )

    def _patch_pth_file(self) -> None:
        """Patch the .pth file to include the Scripts directory in sys.path.

        The _pth file controls Python's import path. We need to:
        1. Add reference to pythonXX.zip
        2. Add relative path to source code
        3. Uncomment "import site" to enable site-packages
        """

        short_python_version = self._config.python_brief_version
        # relative_source_dir = self._config.pydist_dir_absolute.relative_to(
        #     self._config.pydist_dir_absolute
        # )
        # relative_source_dir = self._config.build_source_dir_absolute.relative_to(
        #     self._config.pydist_dir_absolute
        # )
        if self._config.pydist_dir_absolute == self._config.build_source_dir_absolute:
            relative_path_to_source = "."
        else:
            relative_path_to_source = ".."
        relative_path_to_source += f"\\{self._config.build_source_dir.name}"
        print(f"!!! Adding source directory to ._pth file: {relative_path_to_source}")

        pth_file = self._pydist_path / f"python{short_python_version}._pth"
        pythonzip_file = f"python{short_python_version}.zip"
        content = (
            f"{pythonzip_file}\n"
            f"{relative_path_to_source}\n"
            "\n"
            "# Uncomment to run site.main() automatically\n"
            "import site\n"
        )
        pth_file.write_text(content, encoding="utf-8")

    def _verify_pip_installation(self) -> None:
        scripts_dir = self._pydist_path / "Scripts"
        pip_executable = scripts_dir / "pip3.exe"
        if not pip_executable.exists():
            raise RuntimeError("pip installation failed: pip executable not found.")

    def _build_pip_install_command(
        self,
        requirements: list[str],
        extra_pip_args: list[str] | None,
    ) -> list[str]:
        pip_executable = self._pydist_path / "Scripts" / "pip3.exe"
        cmd = [
            str(pip_executable),
            "install",
            "--no-cache-dir",
            "--no-warn-script-location",
        ]
        cmd.extend(requirements)
        if extra_pip_args:
            cmd.extend(extra_pip_args)
        return cmd

    def _install_all_requirements_at_once(self) -> None:
        cmd = self._build_pip_install_command(
            requirements=self._config.requirements, extra_pip_args=None
        )  # TODO: pip args
        subprocess.run(
            cmd,
            cwd=self._pydist_path / "Scripts",
            capture_output=True,
            text=True,
            check=True,
        )

    def _install_requirements_one_by_one(self) -> None:
        for requirement in self._config.requirements:
            cmd = self._build_pip_install_command(
                requirements=[requirement], extra_pip_args=None
            )
            subprocess.run(
                cmd,
                cwd=self._pydist_path / "Scripts",
                capture_output=True,
                text=True,
                check=True,
            )
