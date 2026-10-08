"""Tests for pyretort.builder.uv_builder with every external step mocked."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock
from zipfile import ZipFile

import httpx
import pytest
import win32con
import win32file

from pyretort.builder.errors import BuildError
from pyretort.builder.uv_builder import UVBuilder
from pyretort.types import BuildConfig, PythonArchitecture
from tests.conftest import BuildExternals, failing_pydist_manager

EMBED_URL = "https://www.python.org/ftp/python/3.12.12/python-3.12.12-embed-amd64.zip"
EMBED_REQUEST = httpx.Request("GET", EMBED_URL)
MISSING = httpx.HTTPStatusError(
    "Client error '404 Not Found'",
    request=EMBED_REQUEST,
    response=httpx.Response(404, request=EMBED_REQUEST),
)
OFFLINE = httpx.ConnectError(
    "[WinError 10061] No connection could be made", request=EMBED_REQUEST
)


def make_config(
    project_dir: Path,
    source_subdir: str,
    icon_file: str | None = None,
    python_version: str = "3.13.0",
    architecture: PythonArchitecture = PythonArchitecture.AMD64,
    create_dist_zip_file: bool = False,
    install_as_package: bool = True,
    main_file: str | None = None,
) -> BuildConfig:
    """Create a BuildConfig rooted at project_dir, in package mode by default."""
    return BuildConfig(
        project_dir_abs_path=project_dir,
        project_name="My App",
        project_version="0.1.0",
        project_source_subdir_rel_path=Path(source_subdir),
        main_file_rel_path=None if main_file is None else Path(main_file),
        install_as_package=install_as_package,
        python_version=python_version,
        python_architecture=architecture,
        build_backend="uv_build" if install_as_package else None,
        icon_file_rel_path=None if icon_file is None else Path(icon_file),
        create_dist_zip_file=create_dist_zip_file,
    )


def make_standalone_config(
    project_dir: Path, main_file: str = "main.py", source_subdir: str = "."
) -> BuildConfig:
    """Create a standalone-mode BuildConfig rooted at project_dir."""
    return make_config(
        project_dir, source_subdir, install_as_package=False, main_file=main_file
    )


def touch(root: Path, *relative_paths: str) -> None:
    """Create empty files under root, together with their directories."""
    for relative_path in relative_paths:
        file = root / relative_path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"")


# Where the standalone build of make_standalone_config puts the sources,
# relative to the project directory.
STANDALONE_APP_DIR = Path("build") / "my-app-0.1.0-amd64" / "my-app" / "app"


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


@pytest.mark.usefixtures("externals", "generate_exe")
class TestUVBuilderStandalone:
    """Tests for the standalone build: copied sources, dependencies, launcher."""

    def test_standalone_build_copies_sources_into_app_dir(self, tmp_path: Path) -> None:
        """Test that scripts, binaries, icons and a nested dist/ land in <name>/app/."""
        files = [
            "main.py",
            "lib/native.dll",
            "lib/ext.pyd",
            "icons/app.png",
            "ui/dist/index.html",
        ]
        touch(tmp_path, *files)
        config = make_standalone_config(tmp_path)

        UVBuilder(config).build()

        app_dir = tmp_path / STANDALONE_APP_DIR
        for file in files:
            assert (app_dir / file).is_file(), file

    def test_standalone_build_skips_junk_at_any_depth(self, tmp_path: Path) -> None:
        """Test that caches, virtual environments and tests are left out everywhere."""
        junk = ["__pycache__", "pkg/__pycache__", ".venv", "tests", "pkg/tests"]
        touch(tmp_path, "main.py", "pkg/mod.py", *(f"{d}/file.py" for d in junk))
        config = make_standalone_config(tmp_path)

        UVBuilder(config).build()

        app_dir = tmp_path / STANDALONE_APP_DIR
        assert (app_dir / "pkg" / "mod.py").is_file()
        for directory in junk:
            assert not (app_dir / directory).exists(), directory

    def test_standalone_build_skips_pyretort_dirs_in_project_root(
        self, tmp_path: Path
    ) -> None:
        """Test that build/, dist/, downloads/ and venv/ of the project are left out."""
        excluded = ["build", "dist", "downloads", "venv"]
        touch(tmp_path, "main.py", *(f"{d}/leftover.txt" for d in excluded))
        config = make_standalone_config(tmp_path)

        UVBuilder(config).build()

        app_dir = tmp_path / STANDALONE_APP_DIR
        assert (app_dir / "main.py").is_file()
        for directory in excluded:
            assert not (app_dir / directory).exists(), directory

    def test_standalone_build_installs_only_dependencies(
        self, tmp_path: Path, externals: BuildExternals
    ) -> None:
        """Test that uv installs from pyproject.toml with -r, not the project itself."""
        touch(tmp_path, "main.py")
        config = make_standalone_config(tmp_path)

        UVBuilder(config).build()

        python_exe = tmp_path / "build" / "my-app-0.1.0-amd64" / "my-app" / "python.exe"
        externals.run.assert_called_once()
        assert externals.run.call_args.args[0] == [
            "uv",
            "pip",
            "install",
            "--python",
            str(python_exe),
            "-r",
            str(tmp_path / "pyproject.toml"),
        ]

    @pytest.mark.parametrize(
        ("main_file", "expected_line"),
        [("main.py", "app"), ("scripts/run.py", "app\\scripts")],
    )
    def test_standalone_build_adds_main_file_dir_to_pth(
        self, tmp_path: Path, main_file: str, expected_line: str
    ) -> None:
        """Test that ._pth lists the script's folder, which isolated mode drops."""
        touch(tmp_path, main_file)
        config = make_standalone_config(tmp_path, main_file=main_file)

        UVBuilder(config).build()

        pth = tmp_path / "build" / "my-app-0.1.0-amd64" / "my-app" / "python313._pth"
        assert expected_line in pth.read_text(encoding="utf-8").splitlines()

    def test_standalone_launcher_runs_main_file_as_script(
        self, tmp_path: Path, generate_exe: MagicMock
    ) -> None:
        """Test that the launcher runs the copied main_file with the embedded Python."""
        touch(tmp_path, "main.py")
        config = make_standalone_config(tmp_path)

        UVBuilder(config).build()

        command = generate_exe.call_args.kwargs["command"]
        assert (
            command
            == '"{EXE_DIR}\\my-app\\python.exe" "{EXE_DIR}\\my-app\\app\\main.py"'
        )

    def test_standalone_build_reports_copy_failure(self, tmp_path: Path) -> None:
        """Test that a source file another program holds open fails with BuildError."""
        touch(tmp_path, "main.py")
        config = make_standalone_config(tmp_path)
        # A handle without any sharing stops the file from being read.
        handle = win32file.CreateFile(
            str(tmp_path / "main.py"),
            win32con.GENERIC_READ,
            0,
            None,
            win32con.OPEN_EXISTING,
            0,
            None,
        )
        try:
            with pytest.raises(
                BuildError, match="Could not copy the sources"
            ) as exc_info:
                UVBuilder(config).build()
        finally:
            handle.Close()

        assert str(tmp_path / STANDALONE_APP_DIR) in str(exc_info.value)
        assert "main.py" in str(exc_info.value)


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

    def test_build_reports_missing_embedded_python(
        self, tmp_path: Path, externals: BuildExternals
    ) -> None:
        """Test that a version python.org has no embeddable package for fails clearly."""
        config = make_config(tmp_path, "src/my_pkg", python_version="3.12.12")
        externals.pydist_manager_class.side_effect = failing_pydist_manager(MISSING)

        with pytest.raises(BuildError) as exc_info:
            UVBuilder(config).build()

        assert (
            "python.org has no Windows embeddable package for Python 3.12.12 (amd64)"
            in str(exc_info.value)
        )
        assert EMBED_URL in str(exc_info.value)

    def test_build_reports_failed_download(
        self, tmp_path: Path, externals: BuildExternals
    ) -> None:
        """Test that a download cut off by the network fails with BuildError."""
        config = make_config(tmp_path, "src/my_pkg", python_version="3.12.12")
        externals.pydist_manager_class.side_effect = failing_pydist_manager(OFFLINE)

        with pytest.raises(
            BuildError,
            match=r"Could not download the embedded Python 3\.12\.12 \(amd64\)",
        ) as exc_info:
            UVBuilder(config).build()

        assert "WinError 10061" in str(exc_info.value)

    def test_build_turns_long_command_into_build_error(self, tmp_path: Path) -> None:
        """Test that a module name pushing the launcher command over the limit fails."""
        config = make_config(tmp_path, "src/" + "m" * 1100)

        with pytest.raises(BuildError, match="the limit is 1023"):
            UVBuilder(config).build()

    @pytest.mark.usefixtures("generate_exe")
    def test_build_reports_locked_build_dir(self, tmp_path: Path) -> None:
        """Test that a file of the previous build held open fails with BuildError."""
        config = make_config(tmp_path, "src/my_pkg")
        app_dir = tmp_path / "build" / "my-app-0.1.0-amd64"
        app_dir.mkdir(parents=True)
        (app_dir / "stale.txt").write_text("left over from an earlier build")

        with (
            open(app_dir / "stale.txt", "rb"),
            pytest.raises(
                BuildError, match="Could not prepare the build directory"
            ) as exc_info,
        ):
            UVBuilder(config).build()

        assert str(app_dir) in str(exc_info.value)
        assert "WinError 32" in str(exc_info.value)

    @pytest.mark.usefixtures("generate_exe")
    def test_build_reports_locked_archive(self, tmp_path: Path) -> None:
        """Test that an archive another program holds open fails with BuildError."""
        config = make_config(tmp_path, "src/my_pkg", create_dist_zip_file=True)
        archive = tmp_path / "dist" / "my-app-0.1.0-amd64.zip"
        archive.parent.mkdir()
        archive.write_bytes(b"opened in another program")
        # Python's open() shares write access; only a handle without
        # FILE_SHARE_WRITE stops the archive from being overwritten.
        handle = win32file.CreateFile(
            str(archive),
            win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ,
            None,
            win32con.OPEN_EXISTING,
            0,
            None,
        )
        try:
            with pytest.raises(
                BuildError, match="Could not write the archive"
            ) as exc_info:
                UVBuilder(config).build()
        finally:
            handle.Close()

        assert str(archive) in str(exc_info.value)
