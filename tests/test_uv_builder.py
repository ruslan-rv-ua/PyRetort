"""Tests for pyretort.builder.uv_builder with every external step mocked."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from pyretort.builder.uv_builder import UVBuilder
from pyretort.types import BuildConfig, PythonArchitecture


def make_config(project_dir: Path, source_subdir: str) -> BuildConfig:
    """Create a package-mode BuildConfig rooted at project_dir."""
    return BuildConfig(
        build_hash="abc123",
        project_dir_abs_path=project_dir,
        project_name="My App",
        project_version="0.1.0",
        project_source_subdir_rel_path=Path(source_subdir),
        python_version="3.13.0",
        python_architecture=PythonArchitecture.AMD64,
        build_backend="uv_build",
        create_dist_zip_file=False,
    )


class TestUVBuilderLauncher:
    """Tests for the launcher command UVBuilder passes to generate_exe."""

    def test_build_launcher_runs_main_module(self, tmp_path: Path) -> None:
        """Test that the launcher runs 'python -m <package dir>', not the slug."""
        config = make_config(tmp_path, "src/my_pkg")

        with (
            patch("pyretort.builder.uv_builder.PydistManager") as pydist_manager_class,
            patch("pyretort.builder.uv_builder.subprocess.run"),
            patch("pyretort.builder.uv_builder.generate_exe") as generate_exe,
        ):
            builder = UVBuilder(config)
            pydist_manager_class.return_value.python_executable = (
                builder.pydist_path / "python.exe"
            )

            builder.build()

        command = generate_exe.call_args.kwargs["command"]
        assert command.endswith(" -m my_pkg")
