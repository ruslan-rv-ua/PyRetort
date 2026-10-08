"""Tests for pyretort.builder.pydist_manager module."""

import io
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pytest

from pyretort.builder.downloader import Downloader
from pyretort.builder.pydist_manager import PYTHON_URL, PydistManager
from pyretort.types import PythonArchitecture


@pytest.fixture
def downloader(download_dir: Path) -> Downloader:
    """Create a Downloader instance for testing."""
    return Downloader(download_dir)


@pytest.fixture
def pydist_manager(pydist_dir: Path, downloader: Downloader) -> PydistManager:
    """Create a PydistManager instance for testing."""
    return PydistManager(pydist_dir, downloader)


class TestPydistManagerInit:
    """Tests for PydistManager initialization."""

    def test_init_stores_paths(self, pydist_dir: Path, downloader: Downloader) -> None:
        """Test that paths are stored correctly."""
        manager = PydistManager(pydist_dir, downloader)
        assert manager._pydist_path == pydist_dir
        assert manager._downloader == downloader

    def test_python_executable_property(
        self, pydist_dir: Path, downloader: Downloader
    ) -> None:
        """Test python_executable property returns correct path."""
        manager = PydistManager(pydist_dir, downloader)
        assert manager.python_executable == pydist_dir / "python.exe"


class TestPydistManagerDownloadEmbeddedPython:
    """Tests for PydistManager._download_embedded_python method."""

    def test_download_constructs_correct_url(
        self, pydist_manager: PydistManager
    ) -> None:
        """Test that correct URL is constructed for download."""
        with patch.object(pydist_manager._downloader, "download") as mock_download:
            mock_download.return_value = Path("test.zip")

            pydist_manager._download_embedded_python("3.13.0", PythonArchitecture.AMD64)

            expected_url = f"{PYTHON_URL}/3.13.0/python-3.13.0-embed-amd64.zip"
            expected_filename = "python-3.13.0-embed-amd64.zip"
            mock_download.assert_called_once_with(expected_url, expected_filename)

    def test_download_url_with_win32(self, pydist_manager: PydistManager) -> None:
        """Test URL construction for win32 architecture."""
        with patch.object(pydist_manager._downloader, "download") as mock_download:
            mock_download.return_value = Path("test.zip")

            pydist_manager._download_embedded_python("3.11.5", PythonArchitecture.WIN32)

            expected_url = f"{PYTHON_URL}/3.11.5/python-3.11.5-embed-win32.zip"
            mock_download.assert_called_once_with(
                expected_url, "python-3.11.5-embed-win32.zip"
            )

    def test_download_url_with_arm64(self, pydist_manager: PydistManager) -> None:
        """Test URL construction for ARM64 architecture."""
        with patch.object(pydist_manager._downloader, "download") as mock_download:
            mock_download.return_value = Path("test.zip")

            pydist_manager._download_embedded_python("3.12.0", PythonArchitecture.ARM64)

            expected_url = f"{PYTHON_URL}/3.12.0/python-3.12.0-embed-arm64.zip"
            mock_download.assert_called_once_with(
                expected_url, "python-3.12.0-embed-arm64.zip"
            )


class TestPydistManagerExtractEmbeddedPython:
    """Tests for PydistManager._extract_embedded_python method."""

    def test_extract_creates_files(
        self, pydist_manager: PydistManager, tmp_path: Path
    ) -> None:
        """Test that extraction creates expected files."""
        archive = tmp_path / "test.zip"
        with ZipFile(archive, "w") as zf:
            zf.writestr("python.exe", b"fake executable")
            zf.writestr("python313.dll", b"fake dll")

        pydist_manager._extract_embedded_python(archive)

        assert (pydist_manager._pydist_path / "python.exe").exists()
        assert (pydist_manager._pydist_path / "python313.dll").exists()


class TestPydistManagerVerifyEmbeddedPython:
    """Tests for PydistManager._verify_embedded_python method."""

    def test_verify_passes_when_python_exists(
        self, pydist_manager: PydistManager
    ) -> None:
        """Test verification passes when python.exe exists."""
        python_exe = pydist_manager._pydist_path / "python.exe"
        python_exe.write_bytes(b"fake")

        pydist_manager._verify_embedded_python()

    def test_verify_raises_when_python_missing(
        self, pydist_manager: PydistManager
    ) -> None:
        """Test verification raises when python.exe is missing."""
        with pytest.raises(RuntimeError, match="python.exe not found"):
            pydist_manager._verify_embedded_python()


class TestPydistManagerPatchPthFile:
    """Tests for PydistManager.patch_pth_file method."""

    def test_patch_creates_pth_file(self, pydist_manager: PydistManager) -> None:
        """Test that without extra paths the file lists the zip, '.' and import site."""
        pydist_manager.patch_pth_file("3.13.0")

        pth_file = pydist_manager._pydist_path / "python313._pth"
        assert pth_file.exists()

        lines = pth_file.read_text(encoding="utf-8").splitlines()
        entries = [line for line in lines if line and not line.startswith("#")]
        assert entries == ["python313.zip", ".", "import site"]

    def test_patch_uses_correct_version_short(
        self, pydist_manager: PydistManager
    ) -> None:
        """Test that short version is used in filename."""
        pydist_manager.patch_pth_file("3.11.9")

        pth_file = pydist_manager._pydist_path / "python311._pth"
        assert pth_file.exists()

        content = pth_file.read_text(encoding="utf-8")
        assert "python311.zip" in content

    def test_patch_writes_extra_paths_after_dot(
        self, pydist_manager: PydistManager
    ) -> None:
        """Test that extra paths follow python3XX.zip and '.' and precede import site."""
        pydist_manager.patch_pth_file("3.13.0", extra_paths=["app", "app\\scripts"])

        pth_file = pydist_manager._pydist_path / "python313._pth"
        lines = pth_file.read_text(encoding="utf-8").splitlines()
        entries = [line for line in lines if line and not line.startswith("#")]
        assert entries == ["python313.zip", ".", "app", "app\\scripts", "import site"]


class TestPydistManagerInstallEmbeddedPython:
    """Tests for PydistManager.install_embedded_python method."""

    def test_install_calls_all_steps(
        self, pydist_manager: PydistManager, tmp_path: Path
    ) -> None:
        """Test that install calls all required methods in order."""
        archive = tmp_path / "python-3.13.0-embed-amd64.zip"
        with ZipFile(archive, "w") as zf:
            zf.writestr("python.exe", b"fake")
            zf.writestr("python313.zip", b"PK")

        with (
            patch.object(
                pydist_manager, "_download_embedded_python", return_value=archive
            ) as mock_download,
            patch.object(pydist_manager, "_extract_embedded_python") as mock_extract,
            patch.object(pydist_manager, "_verify_embedded_python") as mock_verify,
        ):
            pydist_manager.install_embedded_python("3.13.0", PythonArchitecture.AMD64)

            mock_download.assert_called_once_with("3.13.0", PythonArchitecture.AMD64)
            mock_extract.assert_called_once_with(archive)
            mock_verify.assert_called_once()

    def test_install_keeps_stdlib_zip_as_file(
        self, pydist_manager: PydistManager, download_dir: Path, pydist_dir: Path
    ) -> None:
        """Test that python3XX.zip stays the file from the archive, byte for byte.

        uv copies that file into the temporary venv in which it builds the
        project and the dependencies without a wheel; a directory of that
        name makes the copy fail.
        """
        stdlib_buffer = io.BytesIO()
        with ZipFile(stdlib_buffer, "w") as stdlib_zip:
            stdlib_zip.writestr("os.py", b"# os module")
        stdlib_bytes = stdlib_buffer.getvalue()
        with ZipFile(download_dir / "python-3.13.0-embed-amd64.zip", "w") as zf:
            zf.writestr("python.exe", b"fake executable")
            zf.writestr("python313.zip", stdlib_bytes)

        pydist_manager.install_embedded_python("3.13.0", PythonArchitecture.AMD64)

        stdlib_zip_path = pydist_dir / "python313.zip"
        assert stdlib_zip_path.is_file()
        assert stdlib_zip_path.read_bytes() == stdlib_bytes


@pytest.mark.slow
@pytest.mark.requires_network
class TestPydistManagerIntegration:
    """Integration tests for PydistManager with real downloads."""

    def test_install_real_python(self, pydist_dir: Path, download_dir: Path) -> None:
        """Test installing real embedded Python distribution."""
        downloader = Downloader(download_dir)
        manager = PydistManager(pydist_dir, downloader)

        manager.install_embedded_python("3.13.0", PythonArchitecture.AMD64)

        assert manager.python_executable.exists()
        assert (pydist_dir / "python313.zip").is_file()
