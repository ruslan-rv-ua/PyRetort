"""Tests for pyretort.cli.commands.init command."""

from __future__ import annotations

import stat
import tomllib
from pathlib import Path

import pytest
import tomli_w
from typer.testing import CliRunner

from pyretort.cli import app

runner = CliRunner()


@pytest.fixture
def my_app_pyproject(tmp_path: Path) -> Path:
    """Write the pyproject.toml of my-app as 'uv init --no-package' creates it.

    It has no [build-system] table. requires-python admits every Python that
    PyRetort supports, because init writes the version of the Python that runs
    the tests into python_version.
    """
    pyproject = tmp_path / "pyproject.toml"
    data = {
        "project": {
            "name": "my-app",
            "version": "0.1.0",
            "readme": "README.md",
            "requires-python": ">=3.11",
            "dependencies": [],
        },
    }
    pyproject.write_bytes(tomli_w.dumps(data).encode())
    return pyproject


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

    def test_init_leaves_main_file_commented_out_when_none_found(
        self, tmp_path: Path
    ) -> None:
        """Test that init writes no main_file key when it finds no main file."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        package_dir = tmp_path / "src" / "test_app"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("")
        (package_dir / "__main__.py").write_text("")

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        content = pyproject.read_text(encoding="utf-8")
        pyretort_config = tomllib.loads(content)["tool"]["pyretort"]
        assert "main_file" not in pyretort_config
        assert '# main_file = "main.py"' in content
        assert "TODO" not in content

    def test_init_nonexistent_file(self, tmp_path: Path) -> None:
        """Test init command with non-existent pyproject.toml."""
        nonexistent = tmp_path / "nonexistent.toml"

        result = runner.invoke(app, ["init", "-p", str(nonexistent)])

        assert result.exit_code == 1
        assert f"Configuration file not found: {nonexistent}" in result.stderr

    def test_init_fails_clearly_when_pyproject_is_read_only(
        self, tmp_path: Path
    ) -> None:
        """Test that a pyproject.toml that cannot be written gives a message, not a traceback."""
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {"name": "test-app", "version": "0.1.0"},
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        pyproject.chmod(stat.S_IREAD)

        try:
            result = runner.invoke(app, ["init", "-p", str(pyproject)])
        finally:
            pyproject.chmod(stat.S_IREAD | stat.S_IWRITE)

        assert result.exit_code == 1
        assert f"Cannot write {pyproject}" in result.stderr
        assert "Traceback" not in result.output

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

    def test_init_help_shows_the_section_name(self) -> None:
        """Test that Rich markup does not swallow [tool.pyretort] in the --force help."""
        # Wide enough that Rich does not wrap the description mid-sentence.
        result = runner.invoke(app, ["init", "--help"], env={"COLUMNS": "120"})

        assert result.exit_code == 0, result.output
        assert "Overwrite an existing [tool.pyretort] section." in result.output


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
        assert (
            "true: install the project as a package and run python -m <module>; "
            "false: copy sources and run main_file as a script"
        ) in content
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


class TestInitCommandBuildMode:
    """Tests for how init chooses between package mode and standalone mode."""

    def test_init_prefers_standalone_for_scripts_in_project_root(
        self, my_app_pyproject: Path
    ) -> None:
        """Test that main.py in the project root without a package gets standalone mode."""
        (my_app_pyproject.parent / "main.py").write_text("print('hello')")

        result = runner.invoke(app, ["init", "-p", str(my_app_pyproject)])

        assert result.exit_code == 0, result.output
        content = my_app_pyproject.read_text(encoding="utf-8")
        pyretort_config = tomllib.loads(content)["tool"]["pyretort"]
        assert pyretort_config["install_as_package"] is False
        assert pyretort_config["main_file"] == "main.py"
        assert pyretort_config["project_source_subdir"] == "."

    def test_init_does_not_warn_about_dunder_main_in_standalone_mode(
        self, my_app_pyproject: Path
    ) -> None:
        """Test that standalone mode reports the script instead of the missing __main__.py."""
        (my_app_pyproject.parent / "main.py").write_text("print('hello')")

        result = runner.invoke(app, ["init", "-p", str(my_app_pyproject)])

        assert result.exit_code == 0, result.output
        assert "warning" not in result.stdout
        assert (
            "Standalone mode: no package found, "
            "the launcher will run main.py as a script"
        ) in result.stdout

    def test_init_keeps_package_mode_for_package_without_dunder_main(
        self, my_app_pyproject: Path
    ) -> None:
        """Test that a package with main.py but without __main__.py stays a package.

        Its main.py may import relatively, which fails when run as a script.
        """
        package_dir = my_app_pyproject.parent / "src" / "my_app"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("")
        (package_dir / "main.py").write_text("from .database import connect")

        result = runner.invoke(app, ["init", "-p", str(my_app_pyproject)])

        assert result.exit_code == 0, result.output
        content = my_app_pyproject.read_text(encoding="utf-8")
        pyretort_config = tomllib.loads(content)["tool"]["pyretort"]
        assert pyretort_config["install_as_package"] is True
        expected_path = package_dir / "__main__.py"
        assert (
            f"warning: {expected_path} not found; "
            "'pyretort build' will fail until it exists"
        ) in result.stdout

    def test_init_keeps_package_mode_for_single_module_in_root(
        self, my_app_pyproject: Path
    ) -> None:
        """Test that my_app.py in the root keeps package mode: python -m my_app runs it."""
        (my_app_pyproject.parent / "my_app.py").write_text("print('hello')")
        (my_app_pyproject.parent / "main.py").write_text("print('hello')")

        result = runner.invoke(app, ["init", "-p", str(my_app_pyproject)])

        assert result.exit_code == 0, result.output
        content = my_app_pyproject.read_text(encoding="utf-8")
        pyretort_config = tomllib.loads(content)["tool"]["pyretort"]
        assert pyretort_config["install_as_package"] is True

    def test_init_finds_cli_py_as_main_file(self, my_app_pyproject: Path) -> None:
        """Test that cli.py alone in the project root becomes the standalone script."""
        (my_app_pyproject.parent / "cli.py").write_text("print('hello')")

        result = runner.invoke(app, ["init", "-p", str(my_app_pyproject)])

        assert result.exit_code == 0, result.output
        content = my_app_pyproject.read_text(encoding="utf-8")
        pyretort_config = tomllib.loads(content)["tool"]["pyretort"]
        assert pyretort_config["main_file"] == "cli.py"
        assert pyretort_config["install_as_package"] is False

    def test_init_output_passes_check_for_uv_init_no_package_project(
        self, my_app_pyproject: Path
    ) -> None:
        """Test that check accepts what init writes for a 'uv init --no-package' project."""
        project_dir = my_app_pyproject.parent
        (project_dir / "main.py").write_text("print('Hello from my-app!')")
        (project_dir / "README.md").write_text("")
        (project_dir / ".python-version").write_text("3.11\n")

        init_result = runner.invoke(app, ["init", "-p", str(my_app_pyproject)])
        check_result = runner.invoke(app, ["check", "-p", str(my_app_pyproject)])

        assert init_result.exit_code == 0, init_result.output
        assert check_result.exit_code == 0, check_result.output

    def test_init_source_subdir_comment_matches_standalone_mode(
        self, my_app_pyproject: Path
    ) -> None:
        """Test that a standalone section does not claim that the launcher runs python -m."""
        (my_app_pyproject.parent / "main.py").write_text("print('hello')")

        result = runner.invoke(app, ["init", "-p", str(my_app_pyproject)])

        assert result.exit_code == 0, result.output
        content = my_app_pyproject.read_text(encoding="utf-8")
        assert (
            "# In standalone mode its contents are copied into the application"
            in content
        )
        assert "python -m <last path component>" not in content


class TestInitCommandRequiresPython:
    """Tests for the warning about a python_version outside requires-python."""

    @pytest.mark.parametrize(
        ("layout", "install_as_package"),
        [
            (["main.py"], False),
            (["src/my_app/__init__.py", "src/my_app/__main__.py"], True),
        ],
        ids=["standalone", "package"],
    )
    def test_init_warns_when_python_version_does_not_satisfy_requires_python(
        self, tmp_path: Path, layout: list[str], install_as_package: bool
    ) -> None:
        """Test that init still writes the section and warns with the message of check.

        No Python that runs PyRetort satisfies '<3.11', so the test does not
        depend on the Python that runs it.
        """
        pyproject = tmp_path / "pyproject.toml"
        data = {
            "project": {
                "name": "my-app",
                "version": "0.1.0",
                "requires-python": "<3.11",
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }
        pyproject.write_bytes(tomli_w.dumps(data).encode())
        for file_name in layout:
            file_path = tmp_path / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("")

        result = runner.invoke(app, ["init", "-p", str(pyproject)])

        assert result.exit_code == 0, result.output
        content = pyproject.read_text(encoding="utf-8")
        pyretort_config = tomllib.loads(content)["tool"]["pyretort"]
        assert pyretort_config["install_as_package"] is install_as_package
        python_version = pyretort_config["python_version"]
        assert (
            f"warning: python_version {python_version} does not satisfy "
            "requires-python '<3.11' in [project]; "
            "set python_version to a release that satisfies it"
        ) in result.stdout.splitlines()
