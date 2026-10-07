"""Tests for pyretort.cli.commands.clean (the ``cleanup`` command)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyretort.cli import app

runner = CliRunner()

ARTIFACT_DIRS = ("downloads", "build", "dist")


@pytest.fixture
def bare_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a project without artifacts and run from another directory."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("", encoding="utf-8")

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    return project_dir


@pytest.fixture
def project(bare_project: Path) -> Path:
    """Add every artifact directory, each holding one file, to the project."""
    for name in ARTIFACT_DIRS:
        (bare_project / name).mkdir()
        (bare_project / name / "artifact.txt").write_text("artifact", encoding="utf-8")

    return bare_project


def remaining_artifact_dirs(project_dir: Path) -> set[str]:
    """Return the names of artifact directories that still exist in the project."""
    return {name for name in ARTIFACT_DIRS if (project_dir / name).exists()}


class TestCleanupCommand:
    """Tests for the cleanup command."""

    def test_cleanup_cache_removes_only_downloads_dir(self, project: Path) -> None:
        """Test that 'cache' removes only downloads/ of the given project."""
        result = runner.invoke(
            app, ["cleanup", "cache", "-p", str(project / "pyproject.toml")]
        )

        assert result.exit_code == 0, result.output
        assert remaining_artifact_dirs(project) == {"build", "dist"}

    def test_cleanup_build_removes_build_and_dist_dirs(self, project: Path) -> None:
        """Test that 'build' removes build/ and dist/ but keeps downloads/."""
        result = runner.invoke(
            app, ["cleanup", "build", "-p", str(project / "pyproject.toml")]
        )

        assert result.exit_code == 0, result.output
        assert remaining_artifact_dirs(project) == {"downloads"}

    def test_cleanup_all_removes_every_artifact_dir(self, project: Path) -> None:
        """Test that 'all' removes downloads/, build/ and dist/."""
        result = runner.invoke(
            app, ["cleanup", "all", "-p", str(project / "pyproject.toml")]
        )

        assert result.exit_code == 0, result.output
        assert remaining_artifact_dirs(project) == set()

    def test_cleanup_without_targets_removes_everything(self, project: Path) -> None:
        """Test that cleanup without targets behaves like 'all'."""
        result = runner.invoke(app, ["cleanup", "-p", str(project / "pyproject.toml")])

        assert result.exit_code == 0, result.output
        assert remaining_artifact_dirs(project) == set()

    def test_cleanup_targets_are_case_insensitive(self, project: Path) -> None:
        """Test that targets are matched regardless of letter case."""
        result = runner.invoke(
            app, ["cleanup", "CACHE", "-p", str(project / "pyproject.toml")]
        )

        assert result.exit_code == 0, result.output
        assert remaining_artifact_dirs(project) == {"build", "dist"}

    def test_cleanup_rejects_unknown_target(self, project: Path) -> None:
        """Test that an unknown target aborts cleanup before anything is removed."""
        result = runner.invoke(
            app, ["cleanup", "cache", "nope", "-p", str(project / "pyproject.toml")]
        )

        assert result.exit_code == 1
        assert "Invalid cleanup targets" in result.stderr
        assert "cache, build, all" in result.stderr
        assert remaining_artifact_dirs(project) == {"downloads", "build", "dist"}

    def test_cleanup_reports_missing_dirs_without_failing(
        self, bare_project: Path
    ) -> None:
        """Test that absent artifact directories are reported, not treated as errors."""
        result = runner.invoke(
            app, ["cleanup", "-p", str(bare_project / "pyproject.toml")]
        )

        assert result.exit_code == 0, result.output
        assert "not found" in result.output

    def test_cleanup_quiet_prints_nothing(self, project: Path) -> None:
        """Test that quiet mode suppresses all output but still cleans up."""
        result = runner.invoke(
            app, ["-q", "cleanup", "all", "-p", str(project / "pyproject.toml")]
        )

        assert result.exit_code == 0, result.output
        assert result.output == ""
        assert remaining_artifact_dirs(project) == set()

    def test_cleanup_fails_when_pyproject_missing(self, project: Path) -> None:
        """Test that cleanup removes nothing when the pyproject.toml does not exist."""
        result = runner.invoke(app, ["cleanup", "-p", str(project / "nope.toml")])

        assert result.exit_code == 1
        assert "Configuration file not found" in result.stderr
        assert remaining_artifact_dirs(project) == {"downloads", "build", "dist"}

    def test_cleanup_defaults_to_pyproject_in_current_directory(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that without -p the pyproject.toml in the current directory is used."""
        monkeypatch.chdir(project)

        result = runner.invoke(app, ["cleanup"])

        assert result.exit_code == 0, result.output
        assert remaining_artifact_dirs(project) == set()
