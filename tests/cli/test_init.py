"""Tests for pyretort.cli.commands.init command."""

import tomllib
from pathlib import Path

import tomli_w
from typer.testing import CliRunner

from pyretort.cli import app

runner = CliRunner()


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_pyretort_section(self, tmp_path: Path) -> None:
        """Test that init creates [tool.pyretort] section."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src" / "test_app").mkdir(parents=True)

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 0
        assert "updated successfully" in result.output.lower()

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        assert "pyretort" in updated_data.get("tool", {})

    def test_init_includes_python_version(self, tmp_path: Path) -> None:
        """Test that init includes Python version."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        pyretort_config = updated_data["tool"]["pyretort"]

        assert "python_version" in pyretort_config
        assert pyretort_config["python_version"].count(".") == 2

    def test_init_includes_python_architecture(self, tmp_path: Path) -> None:
        """Test that init includes Python architecture."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        pyretort_config = updated_data["tool"]["pyretort"]

        assert "python_architecture" in pyretort_config
        assert pyretort_config["python_architecture"] in ["amd64", "win32", "arm64"]

    def test_init_includes_project_source_subdir(self, tmp_path: Path) -> None:
        """Test that init includes project_source_subdir."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "my-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src" / "my_app").mkdir(parents=True)

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        pyretort_config = updated_data["tool"]["pyretort"]

        assert "project_source_subdir" in pyretort_config

    def test_init_finds_main_file(self, tmp_path: Path) -> None:
        """Test that init finds existing main.py file."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "main.py").write_text("print('hello')")

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        pyretort_config = updated_data["tool"]["pyretort"]

        assert pyretort_config.get("main_file") == "main.py"

    def test_init_nonexistent_file(self, tmp_path: Path) -> None:
        """Test init command with non-existent pyproject.toml."""
        nonexistent = tmp_path / "nonexistent.toml"

        result = runner.invoke(app, ["init", "-p", str(nonexistent)])

        assert result.exit_code != 0

    def test_init_preserves_existing_config(self, tmp_path: Path) -> None:
        """Test that init preserves existing project configuration."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "description": "A test application",
                "dependencies": ["httpx>=0.27.0"],
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

        assert updated_data["project"]["name"] == "test-app"
        assert updated_data["project"]["description"] == "A test application"
        assert "httpx>=0.27.0" in updated_data["project"]["dependencies"]

    def test_init_quiet_mode(self, tmp_path: Path) -> None:
        """Test init command in quiet mode - only print statements should show."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        result = runner.invoke(app, ["--quiet", "init", "-p", str(pyproject)])

        assert result.exit_code == 0
        # Note: init command has print() statements that aren't affected by quiet mode
        # The echo() calls are suppressed, but print() is not
        assert "updated successfully" not in result.output.lower()


class TestInitCommandSourceDiscovery:
    """Tests for source directory discovery in init command."""

    def test_init_discovers_src_layout(self, tmp_path: Path) -> None:
        """Test that init discovers src/ layout."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "my-project", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "src" / "my_project").mkdir(parents=True)
        (tmp_path / "src" / "my_project" / "__init__.py").write_text("")

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        source_subdir = updated_data["tool"]["pyretort"]["project_source_subdir"]

        assert "src" in source_subdir or source_subdir == "."

    def test_init_discovers_flat_layout(self, tmp_path: Path) -> None:
        """Test that init discovers flat layout."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "my-project", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "my_project").mkdir()
        (tmp_path / "my_project" / "__init__.py").write_text("")

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

        assert "project_source_subdir" in updated_data["tool"]["pyretort"]

    def test_init_finds_app_py(self, tmp_path: Path) -> None:
        """Test that init finds app.py as main file."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "app.py").write_text("print('app')")

        runner.invoke(app, ["init", "-p", str(pyproject)])

        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        main_file = updated_data["tool"]["pyretort"].get("main_file")

        assert main_file == "app.py"
