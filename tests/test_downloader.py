"""Tests for pyretort.builder.downloader module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from pyretort.builder.downloader import Downloader


class TestDownloaderInit:
    """Tests for Downloader initialization."""

    def test_init_with_existing_directory(self, download_dir: Path) -> None:
        """Test initialization with existing directory."""
        downloader = Downloader(download_dir)
        assert downloader._download_dir_path == download_dir

    def test_init_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised for non-existent directory."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            Downloader(nonexistent)

    def test_init_with_file_instead_of_directory(self, tmp_path: Path) -> None:
        """Test that NotADirectoryError is raised when path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        with pytest.raises(NotADirectoryError, match="is not a directory"):
            Downloader(file_path)


class TestDownloaderDownload:
    """Tests for Downloader.download method."""

    def test_download_returns_cached_file(self, download_dir: Path) -> None:
        """Test that existing files are returned from cache."""
        cached_file = download_dir / "cached.txt"
        cached_file.write_text("cached content")

        downloader = Downloader(download_dir)
        result = downloader.download("http://example.com/file.txt", "cached.txt")

        assert result == cached_file
        assert result.read_text() == "cached content"

    def test_download_creates_new_file(self, download_dir: Path) -> None:
        """Test that new files are downloaded correctly."""
        downloader = Downloader(download_dir)

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b"test content"]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("httpx.stream", return_value=mock_response):
            result = downloader.download("http://example.com/new.txt", "new.txt")

        assert result == download_dir / "new.txt"
        assert result.exists()
        assert result.read_bytes() == b"test content"

    def test_download_uses_streaming(self, download_dir: Path) -> None:
        """Test that downloads use streaming mode."""
        downloader = Downloader(download_dir)

        with patch("httpx.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2"]
            mock_response.raise_for_status = MagicMock()
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_stream.return_value = mock_response

            downloader.download("http://example.com/file.txt", "streamed.txt")

            mock_stream.assert_called_once_with(
                "GET",
                "http://example.com/file.txt",
                timeout=10.0,
                follow_redirects=True,
            )


class TestDownloaderDownloadFile:
    """Tests for Downloader._download_file method."""

    def test_download_file_writes_chunks(self, download_dir: Path) -> None:
        """Test that file is written in chunks."""
        downloader = Downloader(download_dir)
        target = download_dir / "chunked.txt"

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("httpx.stream", return_value=mock_response):
            downloader._download_file("http://example.com/file.txt", target)

        assert target.read_bytes() == b"chunk1chunk2chunk3"

    def test_download_file_cleans_up_on_error(self, download_dir: Path) -> None:
        """Test that partial files are deleted on HTTP error."""
        downloader = Downloader(download_dir)
        target = download_dir / "failed.txt"

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("httpx.stream", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                downloader._download_file("http://example.com/404.txt", target)

        assert not target.exists()

    def test_download_file_cleans_up_partial_on_error(self, download_dir: Path) -> None:
        """Test that partial files are deleted when download fails mid-stream."""
        downloader = Downloader(download_dir)
        target = download_dir / "partial.txt"

        def failing_iter(chunk_size: int = 8192):
            yield b"some data"
            raise httpx.HTTPError("Connection lost")

        mock_response = MagicMock()
        mock_response.iter_bytes.side_effect = failing_iter
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("httpx.stream", return_value=mock_response):
            with pytest.raises(httpx.HTTPError):
                downloader._download_file("http://example.com/failing.txt", target)

        assert not target.exists()

    def test_download_file_custom_chunk_size(self, download_dir: Path) -> None:
        """Test that custom chunk size is passed to iter_bytes."""
        downloader = Downloader(download_dir)
        target = download_dir / "custom_chunk.txt"

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b"data"]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("httpx.stream", return_value=mock_response):
            downloader._download_file(
                "http://example.com/file.txt", target, chunk_size=4096
            )

        mock_response.iter_bytes.assert_called_with(chunk_size=4096)


class TestDownloaderCaching:
    """Tests for Downloader caching behavior."""

    def test_cached_file_not_redownloaded(self, download_dir: Path) -> None:
        """Test that cached files are not downloaded again."""
        cached = download_dir / "already_cached.txt"
        cached.write_text("original content")

        downloader = Downloader(download_dir)

        with patch("httpx.stream") as mock_stream:
            result = downloader.download(
                "http://example.com/already_cached.txt", "already_cached.txt"
            )

            mock_stream.assert_not_called()

        assert result.read_text() == "original content"

    def test_different_filename_downloads_separately(self, download_dir: Path) -> None:
        """Test that files with different names are downloaded separately."""
        existing = download_dir / "file1.txt"
        existing.write_text("file1 content")

        downloader = Downloader(download_dir)

        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b"file2 content"]
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("httpx.stream", return_value=mock_response):
            result = downloader.download("http://example.com/file2.txt", "file2.txt")

        assert result == download_dir / "file2.txt"
        assert result.read_bytes() == b"file2 content"
        assert existing.read_text() == "file1 content"


@pytest.mark.slow
@pytest.mark.requires_network
class TestDownloaderIntegration:
    """Integration tests for Downloader with real network calls."""

    def test_download_real_file(self, download_dir: Path) -> None:
        """Test downloading a real file from the internet."""
        downloader = Downloader(download_dir)

        result = downloader.download(
            "https://www.python.org/static/favicon.ico", "favicon.ico"
        )

        assert result.exists()
        assert result.stat().st_size > 0
