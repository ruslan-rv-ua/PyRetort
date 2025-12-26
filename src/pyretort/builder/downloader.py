from __future__ import annotations

"""Downloader class for downloading files from a given URL to a local file path."""

from pathlib import Path

import httpx


class Downloader:
    """Class for downloading files from a given URL to a local file path."""

    def __init__(self, download_dir_path: Path) -> None:
        """Initialize the Downloader object.

        Args:
            download_dir_path: The path to the directory
                where downloaded files will be saved.

        Raises:
            FileNotFoundError: If the download directory does not exist.
            NotADirectoryError: If the path is not a directory.
        """
        if not download_dir_path.exists():
            msg = f"Download directory {download_dir_path} does not exist."
            raise FileNotFoundError(msg)
        if not download_dir_path.is_dir():
            msg = f"{download_dir_path} is not a directory."
            raise NotADirectoryError(msg)
        self._download_dir_path = download_dir_path

    def download(self, url: str, file: str) -> Path:
        """Download a file from a given URL and save it to a local file path.

        It will check if the file is already downloaded and cached. If so, it will
        return the cached file path. Otherwise, it will download the file and save it.

        Args:
            url: The URL of the file to download.
            file: The name of the file to save the downloaded file to.

        Returns:
            The local file path of the downloaded file.
        """
        file_path = self._download_dir_path / file
        if file_path.exists() and file_path.is_file():
            return file_path
        self._download_file(url, file_path)
        return file_path

    def _download_file(
        self,
        url: str,
        local_file_path: Path,
        chunk_size: int = 8192,
    ) -> None:
        """Download a file from a given URL and save it to a local file path.

        Args:
            url: The URL of the file to download.
            local_file_path: The local file path to save the downloaded file to.
            chunk_size: The size of each chunk to download. Defaults to 8192.

        Raises:
            httpx.HTTPError: If an error occurs during download.
        """
        try:
            with httpx.stream("GET", url, timeout=10.0, follow_redirects=True) as resp:
                resp.raise_for_status()
                with open(local_file_path, "wb") as file_handle:
                    for chunk in resp.iter_bytes(chunk_size=chunk_size):
                        file_handle.write(chunk)
        except httpx.HTTPError:
            if local_file_path.exists():
                local_file_path.unlink()
            raise
