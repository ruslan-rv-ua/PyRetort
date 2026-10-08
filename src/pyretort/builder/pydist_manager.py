from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from zipfile import ZipFile

from pyretort.builder.downloader import Downloader
from pyretort.builder.utils import make_short_python_version
from pyretort.types import PythonArchitecture

PYTHON_URL = "https://www.python.org/ftp/python"


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

    def patch_pth_file(self, version: str, extra_paths: Sequence[str] = ()) -> None:
        """Write python3XX._pth, the module search path of the embedded Python.

        The file lists python3XX.zip (the standard library, unpacked into a
        directory of that name), '.' (the Python directory itself, which holds
        the .pyd modules of the standard library), then ``extra_paths`` and
        finally ``import site``, which adds Lib\\site-packages. Every path is
        relative to the directory of the file.
        """

        short_version = make_short_python_version(version)
        pth_file = self._pydist_path / f"python{short_version}._pth"
        entries = [f"python{short_version}.zip", ".", *extra_paths]
        content = (
            "\n".join(entries) + "\n"
            "\n"
            "# Uncomment to run site.main() automatically\n"
            "import site\n"
        )
        pth_file.write_text(content, encoding="utf-8")

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
