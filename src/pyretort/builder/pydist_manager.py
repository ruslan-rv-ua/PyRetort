import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

from pyretort.builder.downloader import Downloader
from pyretort.builder.utils import make_short_python_version
from pyretort.types import PythonArchitecture

PYTHON_URL = "https://www.python.org/ftp/python"
GET_PIP_SCRIPT_URL = "https://bootstrap.pypa.io/get-pip.py"


class PydistManager:
    """Manage a embedded Python distribution"""

    def __init__(self, pydist_path: Path, downloader: Downloader) -> None:
        self._pydist_path = pydist_path
        self._downloader = downloader

    @property
    def python_executable(self) -> Path:
        return self._pydist_path / "python.exe"

    def install_embedded_python(
        self, version: str, architecture: PythonArchitecture
    ) -> None:
        """Download and extract embedded Python distribution."""
        archive_path = self._download_embedded_python(version, architecture)
        self._extract_embedded_python(archive_path)
        self._unzip_pythonzip_file(version=version)
        self._verify_embedded_python()

    def patch_pth_file(self, version: str, relative_path_to_source: Path | str) -> None:
        """Patch the .pth file to include the Scripts directory in sys.path."""

        short_version = make_short_python_version(version)
        pth_file = self._pydist_path / f"python{short_version}._pth"
        pythonzip_file = f"python{short_version}.zip"
        content = (
            f"{pythonzip_file}\n"
            f"{relative_path_to_source}\n"
            "\n"
            "# Uncomment to run site.main() automatically\n"
            "import site\n"
        )
        pth_file.write_text(content, encoding="utf-8")

    def install_pip(self):
        """Downloads get-pip.py and runs it with the embedded Python."""
        downloaded_get_pip_path = self._downloader.download(
            GET_PIP_SCRIPT_URL, "get-pip.py"
        )
        target_get_pip_path = self._pydist_path / "get-pip.py"
        shutil.copy2(downloaded_get_pip_path, target_get_pip_path)
        self._run_pip_installation()
        self.patch_pth_file()
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

    def _download_embedded_python(
        self, version: str, architecture: PythonArchitecture
    ) -> Path:
        filename = f"python-{version}-embed-{architecture}.zip"
        url = f"{PYTHON_URL}/{version}/{filename}"
        return self._downloader.download(url, filename)

    def _extract_embedded_python(self, archive_path: Path) -> None:
        with ZipFile(archive_path, "r") as zf:
            zf.extractall(path=self._pydist_path)

    def _unzip_pythonzip_file(self, version: str) -> None:
        """Extract pythonXX.zip to pythonXX.zip directory."""
        short_version = make_short_python_version(version)
        pythonzip_file = self._pydist_path / f"python{short_version}.zip"
        temp_zip = pythonzip_file.with_suffix(".temp_zip")
        pythonzip_file.rename(temp_zip)
        extract_dir = self._pydist_path / f"python{short_version}.zip"
        extract_dir.mkdir(exist_ok=True)
        with ZipFile(temp_zip, "r") as zf:
            zf.extractall(path=extract_dir)
        temp_zip.unlink()

    def _verify_embedded_python(self) -> None:
        if not self.python_executable.exists():
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
