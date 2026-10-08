"""Tests for pyretort.builder.cache_manager module."""

from pathlib import Path

from pyretort.builder.cache_manager import CacheManager


class TestCacheManagerInit:
    """Tests for CacheManager initialization."""

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Test that init creates cache directory if it doesn't exist."""
        cache_path = tmp_path / "new_cache"
        assert not cache_path.exists()

        CacheManager(cache_path)

        assert cache_path.exists()
        assert cache_path.is_dir()

    def test_init_with_existing_directory(self, tmp_path: Path) -> None:
        """Test that init works with existing directory."""
        cache_path = tmp_path / "existing_cache"
        cache_path.mkdir()

        manager = CacheManager(cache_path)

        assert manager._cache_dir == cache_path

    def test_init_creates_nested_directories(self, tmp_path: Path) -> None:
        """Test that init creates nested directories."""
        cache_path = tmp_path / "deep" / "nested" / "cache"

        CacheManager(cache_path)

        assert cache_path.exists()


class TestCacheManagerContains:
    """Tests for CacheManager.__contains__ method."""

    def test_contains_existing_file(self, tmp_path: Path) -> None:
        """Test that existing file is detected."""
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        (cache_path / "existing.txt").write_text("content")

        manager = CacheManager(cache_path)

        assert "existing.txt" in manager

    def test_contains_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that nonexistent file is not detected."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)

        assert "nonexistent.txt" not in manager

    def test_contains_existing_directory(self, tmp_path: Path) -> None:
        """Test that existing directory is detected."""
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        (cache_path / "subdir").mkdir()

        manager = CacheManager(cache_path)

        assert "subdir" in manager

    def test_contains_with_path_object(self, tmp_path: Path) -> None:
        """Test that Path objects work with __contains__."""
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        (cache_path / "file.txt").write_text("content")

        manager = CacheManager(cache_path)

        assert Path("file.txt") in manager


class TestCacheManagerGetPath:
    """Tests for CacheManager.get_path method."""

    def test_get_path_returns_cache_dir(self, tmp_path: Path) -> None:
        """Test that get_path returns cache directory."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)

        assert manager.get_path() == cache_path


class TestCacheManagerCleanup:
    """Tests for CacheManager.cleanup method."""

    def test_cleanup_removes_files(self, tmp_path: Path) -> None:
        """Test that cleanup removes files from cache."""
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        (cache_path / "file1.txt").write_text("content1")
        (cache_path / "file2.txt").write_text("content2")

        manager = CacheManager(cache_path)
        manager.cleanup()

        assert cache_path.exists()
        assert list(cache_path.iterdir()) == []

    def test_cleanup_removes_directories(self, tmp_path: Path) -> None:
        """Test that cleanup removes subdirectories from cache."""
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        subdir = cache_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")

        manager = CacheManager(cache_path)
        manager.cleanup()

        assert cache_path.exists()
        assert not subdir.exists()

    def test_cleanup_empty_cache(self, tmp_path: Path) -> None:
        """Test cleanup on empty cache doesn't raise."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)

        manager.cleanup()

        assert cache_path.exists()

    def test_cleanup_nonexistent_cache(self, tmp_path: Path) -> None:
        """Test cleanup when cache directory was deleted externally."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)
        cache_path.rmdir()

        manager.cleanup()


class TestCacheManagerGetSize:
    """Tests for CacheManager.get_size method."""

    def test_get_size_empty_cache(self, tmp_path: Path) -> None:
        """Test that empty cache has size 0."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)

        assert manager.get_size() == 0

    def test_get_size_with_files(self, tmp_path: Path) -> None:
        """Test that size accounts for all files."""
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        (cache_path / "file1.txt").write_bytes(b"x" * 100)
        (cache_path / "file2.txt").write_bytes(b"y" * 200)

        manager = CacheManager(cache_path)

        assert manager.get_size() == 300

    def test_get_size_with_nested_files(self, tmp_path: Path) -> None:
        """Test that size includes files in subdirectories."""
        cache_path = tmp_path / "cache"
        cache_path.mkdir()
        (cache_path / "file.txt").write_bytes(b"x" * 50)
        subdir = cache_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_bytes(b"y" * 150)

        manager = CacheManager(cache_path)

        assert manager.get_size() == 200

    def test_get_size_nonexistent_cache(self, tmp_path: Path) -> None:
        """Test that nonexistent cache returns size 0."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)
        cache_path.rmdir()

        assert manager.get_size() == 0


class TestCacheManagerRemove:
    """Tests for CacheManager.remove method."""

    def test_remove_deletes_cache_directory(self, tmp_path: Path) -> None:
        """Test that remove deletes the cache directory entirely."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)
        (cache_path / "file.txt").write_text("content")

        manager.remove()

        assert not cache_path.exists()

    def test_remove_deletes_nested_content(self, tmp_path: Path) -> None:
        """Test that remove deletes nested content."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)
        subdir = cache_path / "deep" / "nested"
        subdir.mkdir(parents=True)
        (subdir / "file.txt").write_text("content")

        manager.remove()

        assert not cache_path.exists()

    def test_remove_nonexistent_is_noop(self, tmp_path: Path) -> None:
        """Test that remove on nonexistent cache doesn't raise."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)
        cache_path.rmdir()

        manager.remove()

    def test_remove_empty_cache(self, tmp_path: Path) -> None:
        """Test that remove works on empty cache."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)

        manager.remove()

        assert not cache_path.exists()


class TestCacheManagerCombined:
    """Combined scenarios for CacheManager."""

    def test_cleanup_then_use(self, tmp_path: Path) -> None:
        """Test that cache is still usable after cleanup."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)
        (cache_path / "old_file.txt").write_text("old")

        manager.cleanup()
        (cache_path / "new_file.txt").write_text("new")

        assert "new_file.txt" in manager
        assert "old_file.txt" not in manager

    def test_multiple_cleanups(self, tmp_path: Path) -> None:
        """Test that multiple cleanups work correctly."""
        cache_path = tmp_path / "cache"
        manager = CacheManager(cache_path)

        for i in range(3):
            (cache_path / f"file{i}.txt").write_text(f"content{i}")
            manager.cleanup()
            assert list(cache_path.iterdir()) == []
