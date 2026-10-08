"""Tests for pyretort.cli.commands.init command."""

import tomllib
from pathlib import Path

import pytest
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

        assert result.exit_code == 1
        assert f"Configuration file not found: {nonexistent}" in result.stderr

    def test_init_defaults_to_pyproject_in_current_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that without -p the pyproject.toml in the current directory is used."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0, result.output
        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        assert "pyretort" in updated_data["tool"]

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
        """Test init command in quiet mode prints nothing."""
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
        assert result.output == ""

    def test_init_architecture_comment_lists_valid_values(self, tmp_path: Path) -> None:
        """Test that the architecture comment lists the accepted values."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 0
        assert "amd64, win32, arm64" in pyproject.read_text(encoding="utf-8")


class TestInitCommandExistingSection:
    """Tests for how init treats an existing [tool.pyretort] section."""

    def test_init_refuses_to_overwrite_existing_section(self, tmp_path: Path) -> None:
        """Test that init exits with 1 and leaves the file untouched without --force."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
            "tool": {"pyretort": {"python_version": "3.11.0", "custom_key": "keep"}},
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        original = pyproject.read_text(encoding="utf-8")

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 1
        assert (
            "pyproject.toml already contains [tool.pyretort]; use --force to overwrite"
            in result.stderr
        )
        assert pyproject.read_text(encoding="utf-8") == original

    def test_init_force_overwrites_existing_section(self, tmp_path: Path) -> None:
        """Test that --force replaces the existing [tool.pyretort] section."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
            "tool": {"pyretort": {"python_version": "3.11.0", "custom_key": "keep"}},
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        result = runner.invoke(app, ["init", "--force", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        updated_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        pyretort_config = updated_data["tool"]["pyretort"]
        assert "custom_key" not in pyretort_config
        assert "project_source_subdir" in pyretort_config
        assert updated_data["project"]["name"] == "test-app"


class TestInitCommandEntryPoint:
    """Tests for the __main__.py warning and the explanatory comments."""

    def test_init_warns_when_dunder_main_is_missing(self, tmp_path: Path) -> None:
        """Test that a package without __main__.py gets a warning but exit code 0."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "my-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        package_dir = tmp_path / "src" / "my_app"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        expected_path = package_dir / "__main__.py"
        assert (
            f"warning: {expected_path} not found; "
            "'pyretort build' will fail until it exists"
        ) in result.stdout

    def test_init_does_not_warn_when_dunder_main_exists(self, tmp_path: Path) -> None:
        """Test that a package with __main__.py produces no warning."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "my-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        package_dir = tmp_path / "src" / "my_app"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("")
        (package_dir / "__main__.py").write_text("")

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        assert "warning" not in result.output

    def test_init_comments_explain_install_as_package_and_main_file(
        self, tmp_path: Path
    ) -> None:
        """Test that the generated section explains both fields' real semantics."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        content = pyproject.read_text(encoding="utf-8")
        assert "Must be true: standalone mode (false) is not supported yet" in content
        assert "Used only when install_as_package = false; ignored otherwise" in content


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

        assert source_subdir == "src/my_project"

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
