"""Tests for pyretort.builder.uv_builder with every external step mocked."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock
from zipfile import ZipFile

import pytest

from pyretort.builder.errors import BuildError
from pyretort.builder.uv_builder import UVBuilder
from pyretort.types import BuildConfig, PythonArchitecture
from tests.conftest import BuildExternals


def make_config(
    project_dir: Path,
    source_subdir: str,
    icon_file: str | None = None,
    python_version: str = "3.13.0",
    architecture: PythonArchitecture = PythonArchitecture.AMD64,
    create_dist_zip_file: bool = False,
) -> BuildConfig:
    """Create a package-mode BuildConfig rooted at project_dir."""
    return BuildConfig(
        build_hash="abc123",
        project_dir_abs_path=project_dir,
        project_name="My App",
        project_version="0.1.0",
        project_source_subdir_rel_path=Path(source_subdir),
        python_version=python_version,
        python_architecture=architecture,
        build_backend="uv_build",
        icon_file_rel_path=None if icon_file is None else Path(icon_file),
        create_dist_zip_file=create_dist_zip_file,
    )


@pytest.mark.usefixtures("externals")
class TestUVBuilderLauncher:
    """Tests for the launcher command UVBuilder passes to generate_exe."""

    def test_build_launcher_runs_main_module(
        self, tmp_path: Path, generate_exe: MagicMock
    ) -> None:
        """Test that the launcher runs 'python -m <package dir>', not the slug."""
        config = make_config(tmp_path, "src/my_pkg")

        UVBuilder(config).build()

        command = generate_exe.call_args.kwargs["command"]
        assert command.endswith(" -m my_pkg")

    def test_build_passes_absolute_icon_path_from_project_dir(
        self, tmp_path: Path, generate_exe: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that the icon is looked up in the project, not the current directory."""
        project_dir = tmp_path / "project"
        (project_dir / "assets").mkdir(parents=True)
        (project_dir / "assets" / "app.ico").write_bytes(b"")
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        config = make_config(project_dir, "src/my_pkg", icon_file="assets/app.ico")

        UVBuilder(config).build()

        icon_file = generate_exe.call_args.kwargs["icon_file"]
        assert icon_file == project_dir / "assets" / "app.ico"

    def test_build_uses_launcher_for_python_architecture(
        self, tmp_path: Path, generate_exe: MagicMock
    ) -> None:
        """Test that the launcher has the architecture of the embedded Python."""
        config = make_config(
            tmp_path, "src/my_pkg", architecture=PythonArchitecture.WIN32
        )

        UVBuilder(config).build()

        architecture = generate_exe.call_args.kwargs["architecture"]
        assert architecture == PythonArchitecture.WIN32


@pytest.mark.usefixtures("externals", "generate_exe")
class TestUVBuilderProgress:
    """Tests for the progress messages UVBuilder reports through log."""

    def test_build_logs_progress_messages(self, tmp_path: Path) -> None:
        """Test that each build stage is reported and the last message names the result."""
        config = make_config(tmp_path, "src/my_pkg", python_version="3.13.9")
        messages: list[str] = []

        UVBuilder(config, log=messages.append).build()

        assert "Installing embedded Python 3.13.9 (amd64)" in messages
        assert (
            messages[-1]
            == f"Build complete: {tmp_path / 'build' / 'my-app-0.1.0-amd64'}"
        )


@pytest.mark.usefixtures("externals")
class TestUVBuilderDirectories:
    """Tests for the directories UVBuilder prepares before building."""

    def test_builder_init_does_not_touch_filesystem(self, tmp_path: Path) -> None:
        """Test that constructing a builder creates no directories."""
        config = make_config(tmp_path, "src/my_pkg")

        UVBuilder(config)

        assert not (tmp_path / "build").exists()
        assert not (tmp_path / "downloads").exists()
        assert not (tmp_path / "dist").exists()

    @pytest.mark.usefixtures("generate_exe")
    def test_build_recreates_app_dir_from_scratch(self, tmp_path: Path) -> None:
        """Test that leftovers of a previous build are removed from build/<dist_name>."""
        config = make_config(tmp_path, "src/my_pkg")
        app_dir = tmp_path / "build" / "my-app-0.1.0-amd64"
        app_dir.mkdir(parents=True)
        stale_file = app_dir / "stale.txt"
        stale_file.write_text("left over from an earlier build")

        UVBuilder(config).build()

        assert app_dir.is_dir()
        assert not stale_file.exists()


@pytest.mark.usefixtures("externals", "generate_exe")
class TestUVBuilderArchive:
    """Tests for the ZIP archive of the build that UVBuilder writes to dist/."""

    def test_build_creates_zip_with_dist_name_prefix(self, tmp_path: Path) -> None:
        """Test that the archive unpacks into one <dist_name>/ with exe and Python."""
        config = make_config(tmp_path, "src/my_pkg", create_dist_zip_file=True)

        UVBuilder(config).build()

        archive = tmp_path / "dist" / "my-app-0.1.0-amd64.zip"
        assert archive.is_file()
        with ZipFile(archive) as zf:
            names = zf.namelist()
        assert all(name.startswith("my-app-0.1.0-amd64/") for name in names)
        assert "my-app-0.1.0-amd64/my-app.exe" in names
        assert "my-app-0.1.0-amd64/my-app/python.exe" in names

    def test_build_skips_zip_when_disabled(self, tmp_path: Path) -> None:
        """Test that create_dist_zip_file = false puts no archive into dist/."""
        config = make_config(tmp_path, "src/my_pkg", create_dist_zip_file=False)

        result = UVBuilder(config).build()

        assert list((tmp_path / "dist").glob("*.zip")) == []
        assert result.archive is None

    def test_build_overwrites_stale_zip(self, tmp_path: Path) -> None:
        """Test that an archive left by an earlier build is replaced, not added to."""
        config = make_config(tmp_path, "src/my_pkg", create_dist_zip_file=True)
        archive = tmp_path / "dist" / "my-app-0.1.0-amd64.zip"
        archive.parent.mkdir()
        with ZipFile(archive, "w") as zf:
            zf.writestr(
                "my-app-0.1.0-amd64/stale.txt", "left over from an earlier build"
            )

        UVBuilder(config).build()

        with ZipFile(archive) as zf:
            names = zf.namelist()
        assert "my-app-0.1.0-amd64/stale.txt" not in names
        assert "my-app-0.1.0-amd64/my-app.exe" in names

    def test_build_returns_result_paths(self, tmp_path: Path) -> None:
        """Test that the result names the application folder and the archive."""
        config = make_config(tmp_path, "src/my_pkg", create_dist_zip_file=True)

        result = UVBuilder(config).build()

        assert result.app_dir == tmp_path / "build" / "my-app-0.1.0-amd64"
        assert result.archive == tmp_path / "dist" / "my-app-0.1.0-amd64.zip"


@pytest.mark.usefixtures("externals")
class TestUVBuilderFailures:
    """Tests for the build failures UVBuilder reports as BuildError."""

    def test_build_fails_clearly_when_uv_is_missing(
        self, tmp_path: Path, externals: BuildExternals
    ) -> None:
        """Test that a missing uv aborts the build before anything is created."""
        config = make_config(tmp_path, "src/my_pkg")
        externals.which.return_value = None

        with pytest.raises(BuildError, match="uv was not found"):
            UVBuilder(config).build()

        assert not (tmp_path / "build").exists()

    def test_build_reports_uv_stderr_on_failure(
        self, tmp_path: Path, externals: BuildExternals
    ) -> None:
        """Test that a failed uv install surfaces uv's exit code and stderr."""
        config = make_config(tmp_path, "src/my_pkg")
        externals.run.side_effect = subprocess.CalledProcessError(
            1, ["uv", "pip", "install"], stderr="No solution found"
        )

        with pytest.raises(BuildError) as exc_info:
            UVBuilder(config).build()

        assert "exit code 1" in str(exc_info.value)
        assert "No solution found" in str(exc_info.value)

    def test_build_turns_long_command_into_build_error(self, tmp_path: Path) -> None:
        """Test that a module name pushing the launcher command over the limit fails."""
        config = make_config(tmp_path, "src/" + "m" * 1100)

        with pytest.raises(BuildError, match="the limit is 1023"):
            UVBuilder(config).build()
