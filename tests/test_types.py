"""Tests for pyretort.types module."""

from pathlib import Path

import pytest
import tomli_w

from pyretort.types import (
    MIN_PYTHON_VERSION,
    BuildConfig,
    PythonArchitecture,
)


def write_standalone_pyproject(
    project_dir: Path, name: object = "test-app", version: object = "0.1.0"
) -> Path:
    """Write a standalone project with main.py and return its pyproject.toml."""
    data = {
        "project": {"name": name, "version": version, "dependencies": []},
        "tool": {
            "pyretort": {
                "project_source_subdir": ".",
                "main_file": "main.py",
                "python_version": "3.13.9",
                "python_architecture": "amd64",
                "install_as_package": False,
                "show_console_window": False,
                "create_dist_zip_file": True,
            }
        },
    }
    pyproject_path = project_dir / "pyproject.toml"
    pyproject_path.write_bytes(tomli_w.dumps(data).encode())
    (project_dir / "main.py").write_text("print('hello')")
    return pyproject_path


class TestPythonArchitecture:
    """Tests for PythonArchitecture enum."""

    def test_amd64_value(self) -> None:
        assert PythonArchitecture.AMD64 == "amd64"
        assert PythonArchitecture.AMD64.value == "amd64"

    def test_win32_value(self) -> None:
        assert PythonArchitecture.WIN32 == "win32"
        assert PythonArchitecture.WIN32.value == "win32"

    def test_arm64_value(self) -> None:
        assert PythonArchitecture.ARM64 == "arm64"
        assert PythonArchitecture.ARM64.value == "arm64"

    def test_all_architectures(self) -> None:
        expected = {"amd64", "win32", "arm64"}
        actual = {arch.value for arch in PythonArchitecture}
        assert actual == expected

    def test_from_string(self) -> None:
        assert PythonArchitecture("amd64") == PythonArchitecture.AMD64
        assert PythonArchitecture("win32") == PythonArchitecture.WIN32
        assert PythonArchitecture("arm64") == PythonArchitecture.ARM64


class TestBuildConfig:
    """Tests for BuildConfig model."""

    def test_valid_config_creation(self, sample_build_config: BuildConfig) -> None:
        """Test creating a valid BuildConfig."""
        assert sample_build_config.project_name == "test-project"
        assert sample_build_config.project_version == "1.0.0"
        assert sample_build_config.python_version == "3.11.0"
        assert sample_build_config.python_architecture == PythonArchitecture.AMD64

    def test_python_version_validation_valid_311(self) -> None:
        """Test that Python 3.11.x passes validation."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.11.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.python_version == "3.11.0"

    def test_python_version_validation_valid_313(self) -> None:
        """Test that Python 3.13.x passes validation."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.13.1",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.python_version == "3.13.1"

    def test_python_version_validation_invalid_310(self) -> None:
        """Test that Python 3.10.x fails validation."""
        with pytest.raises(
            ValueError, match=f"Python version must be >= {MIN_PYTHON_VERSION}"
        ):
            BuildConfig(
                project_dir_abs_path=Path("."),
                project_name="test",
                project_version="1.0.0",
                project_source_subdir_rel_path=Path("src"),
                python_version="3.10.0",
                python_architecture=PythonArchitecture.AMD64,
                build_backend="uv_build",
                create_dist_zip_file=False,
            )

    def test_python_version_validation_invalid_27(self) -> None:
        """Test that Python 2.7 fails validation."""
        with pytest.raises(
            ValueError, match=f"Python version must be >= {MIN_PYTHON_VERSION}"
        ):
            BuildConfig(
                project_dir_abs_path=Path("."),
                project_name="test",
                project_version="1.0.0",
                project_source_subdir_rel_path=Path("src"),
                python_version="2.7.18",
                python_architecture=PythonArchitecture.AMD64,
                build_backend="uv_build",
                create_dist_zip_file=False,
            )

    def test_python_version_validation_invalid_format(self) -> None:
        """Test that invalid version format fails validation."""
        with pytest.raises(ValueError, match="Invalid Python version format"):
            BuildConfig(
                project_dir_abs_path=Path("."),
                project_name="test",
                project_version="1.0.0",
                project_source_subdir_rel_path=Path("src"),
                python_version="not.a.version",
                python_architecture=PythonArchitecture.AMD64,
                build_backend="uv_build",
                create_dist_zip_file=False,
            )

    def test_python_version_short_311(self) -> None:
        """Test python_version_short computed field for 3.11."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.11.9",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.python_version_short == "311"

    def test_python_version_short_313(self) -> None:
        """Test python_version_short computed field for 3.13."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.13.1",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.python_version_short == "313"

    def test_project_name_slug_underscore(self) -> None:
        """Test project_name_slug_underscore computed field."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="My Test Project",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.13.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.project_name_slug_underscore == "my_test_project"

    def test_project_name_slug_dash(self) -> None:
        """Test project_name_slug_dash computed field."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="My Test Project",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.13.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.project_name_slug_dash == "my-test-project"

    def test_dist_name(self) -> None:
        """Test dist_name computed field."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="My App",
            project_version="2.1.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.13.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.dist_name == "my-app-2.1.0-amd64"

    def test_dist_name_with_win32(self) -> None:
        """Test dist_name with win32 architecture."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test-app",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.11.0",
            python_architecture=PythonArchitecture.WIN32,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.dist_name == "test-app-1.0.0-win32"

    def test_optional_fields_default_none(self) -> None:
        """Test that optional fields default to None."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.11.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.main_file_rel_path is None
        assert config.icon_file_rel_path is None

    def test_optional_fields_with_values(self) -> None:
        """Test optional fields when provided."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            main_file_rel_path=Path("main.py"),
            icon_file_rel_path=Path("icon.ico"),
            python_version="3.11.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        # Field validators only check if paths are relative, not if they exist
        assert config.main_file_rel_path == Path("main.py")
        assert config.icon_file_rel_path == Path("icon.ico")

    def test_install_as_package_default(self) -> None:
        """Test install_as_package default value."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.11.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.install_as_package is True

    def test_show_console_window_default(self) -> None:
        """Test show_console_window default value."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="test",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src"),
            python_version="3.11.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.show_console_window is False

    def test_standalone_mode_requires_main_file(self) -> None:
        """Test that install_as_package=False without a main file is rejected."""
        with pytest.raises(
            ValueError,
            match=(
                "Standalone mode \\(install_as_package = false\\) requires "
                "'main_file' in \\[tool.pyretort\\]"
            ),
        ):
            BuildConfig(
                project_dir_abs_path=Path("."),
                project_name="test",
                project_version="1.0.0",
                project_source_subdir_rel_path=Path("."),
                install_as_package=False,
                python_version="3.13.0",
                python_architecture=PythonArchitecture.AMD64,
                create_dist_zip_file=False,
            )

    def test_main_module_is_last_component_of_source_subdir(self) -> None:
        """Test that main_module is the package directory named by the subdir."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="My App",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("src/simple_rss"),
            python_version="3.13.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.main_module == "simple_rss"

    def test_main_module_falls_back_to_project_slug_for_root_subdir(self) -> None:
        """Test that main_module is the project slug when the subdir is '.'."""
        config = BuildConfig(
            project_dir_abs_path=Path("."),
            project_name="My App",
            project_version="1.0.0",
            project_source_subdir_rel_path=Path("."),
            python_version="3.13.0",
            python_architecture=PythonArchitecture.AMD64,
            build_backend="uv_build",
            create_dist_zip_file=False,
        )
        assert config.main_module == "my_app"


class TestBuildConfigFromPyprojectToml:
    """Tests for BuildConfig.from_pyproject_toml class method."""

    def test_from_valid_pyproject_toml(self, valid_pyproject_toml: Path) -> None:
        """Test creating BuildConfig from a valid pyproject.toml."""
        config = BuildConfig.from_pyproject_toml(valid_pyproject_toml)

        assert config.project_name == "test-app"
        assert config.project_version == "0.1.0"
        assert config.python_version == "3.13.0"
        assert config.python_architecture == PythonArchitecture.AMD64
        assert config.build_backend == "uv_build"
        assert config.create_dist_zip_file is True
        assert config.show_console_window is False
        assert config.install_as_package is True
        assert config.project_source_subdir_rel_path == Path("src/test_app")

    def test_from_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised for non-existent file."""
        nonexistent = tmp_path / "nonexistent.toml"
        with pytest.raises(FileNotFoundError, match="File not found"):
            BuildConfig.from_pyproject_toml(nonexistent)

    def test_from_pyproject_toml_with_old_python(
        self, invalid_pyproject_old_python: Path
    ) -> None:
        """Test that ValueError is raised for Python < 3.11."""
        with pytest.raises(
            ValueError, match=f"Python version must be >= {MIN_PYTHON_VERSION}"
        ):
            BuildConfig.from_pyproject_toml(invalid_pyproject_old_python)

    def test_from_pyproject_toml_accepts_path_string(
        self, valid_pyproject_toml: Path
    ) -> None:
        """Test that from_pyproject_toml accepts string paths."""
        config = BuildConfig.from_pyproject_toml(str(valid_pyproject_toml))
        assert config.project_name == "test-app"

    def test_missing_project_section(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when [project] section is missing."""
        import tomli_w

        data = {
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Missing \\[project\\] section"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_project_name(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'name' field is missing in [project]."""
        import tomli_w

        data = {
            "project": {
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Missing 'name' field"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_project_version(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'version' field is missing in [project]."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Missing 'version' field"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_tool_pyretort_section(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when [tool.pyretort] section is missing."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Missing \\[tool.pyretort\\] section"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_python_version_in_tool_pyretort(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'python_version' is missing."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(
            ValueError, match="Missing 'python_version' in \\[tool.pyretort\\]"
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_python_architecture_in_tool_pyretort(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'python_architecture' is missing."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(
            ValueError, match="Missing 'python_architecture' in \\[tool.pyretort\\]"
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_project_source_subdir_in_tool_pyretort(
        self, tmp_path: Path
    ) -> None:
        """Test that ValueError is raised when 'project_source_subdir' is missing."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(
            ValueError, match="Missing 'project_source_subdir' in \\[tool.pyretort\\]"
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_build_system_section(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when [build-system] section is missing."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Missing \\[build-system\\] section"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_build_backend(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'build-backend' is missing."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"]},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Missing 'build-backend' field"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_invalid_python_architecture(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for invalid python_architecture."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "invalid_arch",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(
            ValueError, match="Invalid python_architecture: 'invalid_arch'"
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_from_pyproject_accepts_any_build_backend(self, tmp_path: Path) -> None:
        """Test that any PEP 517 build backend is accepted and kept as a string."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {
                "requires": ["setuptools>=68"],
                "build-backend": "setuptools.build_meta",
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "__main__.py").write_text("")

        config = BuildConfig.from_pyproject_toml(pyproject_path)

        assert config.build_backend == "setuptools.build_meta"

    def test_from_pyproject_rejects_empty_build_backend(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for an empty build-backend string."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {
                "requires": ["uv_build"],
                "build-backend": "",
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "__main__.py").write_text("")

        with pytest.raises(
            ValueError,
            match="'build-backend' in \\[build-system\\] must be a non-empty string",
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_from_pyproject_rejects_package_without_dunder_main(
        self, tmp_path: Path
    ) -> None:
        """Test that a package directory without __main__.py is rejected."""
        import tomli_w

        data = {
            "project": {"name": "my-app", "version": "0.1.0", "dependencies": []},
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src/my_app",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        package_dir = tmp_path / "src" / "my_app"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("")

        with pytest.raises(ValueError, match="__main__.py") as exc_info:
            BuildConfig.from_pyproject_toml(pyproject_path)

        assert "python -m my_app" in str(exc_info.value)
        assert str(package_dir / "__main__.py") in str(exc_info.value)

    def test_from_pyproject_accepts_single_module_in_root(self, tmp_path: Path) -> None:
        """Test that a root subdir with '<main_module>.py' passes validation."""
        import tomli_w

        data = {
            "project": {"name": "mytool", "version": "0.1.0", "dependencies": []},
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": ".",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "mytool.py").write_text("print('hello')")

        config = BuildConfig.from_pyproject_toml(pyproject_path)

        assert config.main_module == "mytool"

    def test_source_subdir_does_not_exist(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when source subdirectory doesn't exist."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "nonexistent_dir",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Source subdirectory does not exist"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_source_subdir_is_absolute_path(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when source subdirectory is absolute."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "C:/absolute/path",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        with pytest.raises(ValueError, match="Source subdirectory must be relative"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_main_file_does_not_exist_in_standalone_mode(self, tmp_path: Path) -> None:
        """Test that a missing main file is rejected when install_as_package is false."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "main_file": "nonexistent.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="Main file does not exist"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_main_file_is_not_checked_in_package_mode(self, tmp_path: Path) -> None:
        """Test that main_file may point nowhere when install_as_package is true."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "main_file": "nonexistent.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "__main__.py").write_text("")

        config = BuildConfig.from_pyproject_toml(pyproject_path)

        assert config.main_file_rel_path == Path("nonexistent.py")

    def test_main_file_is_absolute_path(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when main file is absolute."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "main_file": "C:/absolute/path/main.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="Main file must be relative"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_icon_file_does_not_exist(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when icon file doesn't exist."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "icon_file_rel_path": "nonexistent.ico",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="Icon file does not exist"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_icon_file_is_absolute_path(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when icon file is absolute."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "icon_file_rel_path": "C:/absolute/path/icon.ico",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="Icon file must be relative"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_missing_create_dist_zip_file(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'create_dist_zip_file' is missing."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(
            ValueError, match="Missing 'create_dist_zip_file' in \\[tool.pyretort\\]"
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_invalid_install_as_package_type(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'install_as_package' is not a boolean."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": "yes",  # Invalid: should be bool
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="'install_as_package' must be a boolean"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_invalid_show_console_window_type(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'show_console_window' is not a boolean."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": "true",  # Invalid: should be bool
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="'show_console_window' must be a boolean"):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_invalid_create_dist_zip_file_type(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when 'create_dist_zip_file' is not a boolean."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": False,
                    "create_dist_zip_file": "yes",  # Invalid: should be bool
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)

        with pytest.raises(
            ValueError, match="'create_dist_zip_file' must be a boolean"
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_valid_boolean_fields(self, tmp_path: Path) -> None:
        """Test that non-default boolean values are accepted."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": True,
                    "show_console_window": True,
                    "create_dist_zip_file": False,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "__main__.py").write_text("")

        config = BuildConfig.from_pyproject_toml(pyproject_path)
        assert config.install_as_package is True
        assert config.show_console_window is True
        assert config.create_dist_zip_file is False

    @pytest.mark.parametrize(
        ("missing_key", "expected"),
        [("install_as_package", True), ("show_console_window", False)],
    )
    def test_from_pyproject_uses_defaults_for_missing_optional_booleans(
        self, tmp_path: Path, missing_key: str, expected: bool
    ) -> None:
        """Test that an absent optional boolean takes its default value."""
        import tomli_w

        pyretort_section = {
            "project_source_subdir": "src",
            "python_version": "3.13.0",
            "python_architecture": "amd64",
            "install_as_package": True,
            "show_console_window": False,
            "create_dist_zip_file": True,
        }
        del pyretort_section[missing_key]
        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "build-system": {"requires": ["uv_build"], "build-backend": "uv_build"},
            "tool": {"pyretort": pyretort_section},
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "__main__.py").write_text("")

        config = BuildConfig.from_pyproject_toml(pyproject_path)

        assert getattr(config, missing_key) is expected

    def test_from_pyproject_accepts_standalone_mode(self, tmp_path: Path) -> None:
        """Test that standalone mode needs neither [build-system] nor __main__.py."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "requires-python": ">=3.13",
                "dependencies": ["six"],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "main_file": "main.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "main.py").write_text("print('hello')")

        config = BuildConfig.from_pyproject_toml(pyproject_path)

        assert config.install_as_package is False
        assert config.main_file_rel_path == Path("main.py")
        assert config.build_backend is None

    def test_from_pyproject_requires_main_file_in_standalone_mode(
        self, tmp_path: Path
    ) -> None:
        """Test that standalone mode without main_file is rejected."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        source_dir = tmp_path / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "main.py").write_text("print('hello')")

        with pytest.raises(
            ValueError,
            match=(
                "Standalone mode \\(install_as_package = false\\) requires "
                "'main_file' in \\[tool.pyretort\\]"
            ),
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_from_pyproject_rejects_main_file_outside_source_dir_in_standalone_mode(
        self, tmp_path: Path
    ) -> None:
        """Test that main_file may not leave project_source_subdir, even if it exists."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": [],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": "src",
                    "main_file": "../main.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())

        (tmp_path / "src").mkdir()
        (tmp_path / "main.py").write_text("print('hello')")

        with pytest.raises(
            ValueError,
            match="Main file must be inside the source subdirectory: \\.\\./main\\.py",
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_from_pyproject_rejects_dynamic_dependencies_in_standalone_mode(
        self, tmp_path: Path
    ) -> None:
        """Test that dependencies a backend would compute cannot be installed."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dynamic": ["dependencies"],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": ".",
                    "main_file": "main.py",
                    "python_version": "3.13.0",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "main.py").write_text("print('hello')")

        with pytest.raises(
            ValueError,
            match=(
                "Standalone mode installs \\[project\\].dependencies; 'dependencies' "
                "in \\[project\\].dynamic is not supported"
            ),
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_from_pyproject_rejects_python_version_outside_requires_python_in_standalone_mode(
        self, tmp_path: Path
    ) -> None:
        """Test that the embedded Python must satisfy requires-python, which uv skips."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "requires-python": ">=3.14",
                "dependencies": [],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": ".",
                    "main_file": "main.py",
                    "python_version": "3.13.9",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "main.py").write_text("print('hello')")

        with pytest.raises(
            ValueError,
            match=(
                "python_version 3.13.9 does not satisfy requires-python '>=3.14' "
                "in \\[project\\]"
            ),
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    def test_from_pyproject_rejects_invalid_requires_python_in_standalone_mode(
        self, tmp_path: Path
    ) -> None:
        """Test that a requires-python that is no version specifier is reported."""
        import tomli_w

        data = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "requires-python": "3.13 or later",
                "dependencies": [],
            },
            "tool": {
                "pyretort": {
                    "project_source_subdir": ".",
                    "main_file": "main.py",
                    "python_version": "3.13.9",
                    "python_architecture": "amd64",
                    "install_as_package": False,
                    "show_console_window": False,
                    "create_dist_zip_file": True,
                }
            },
        }
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_bytes(tomli_w.dumps(data).encode())
        (tmp_path / "main.py").write_text("print('hello')")

        with pytest.raises(
            ValueError,
            match="Invalid requires-python in \\[project\\]: '3.13 or later'",
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)

    @pytest.mark.parametrize(
        ("name", "version", "message"),
        [
            (123, "0.1.0", "'name' in [project] must be a string, got int"),
            ("test-app", 1.0, "'version' in [project] must be a string, got float"),
        ],
        ids=["name", "version"],
    )
    def test_from_pyproject_rejects_non_string_project_name_and_version(
        self, tmp_path: Path, name: object, version: object, message: str
    ) -> None:
        """Test that a name or version of another TOML type gets a plain message."""
        pyproject_path = write_standalone_pyproject(tmp_path, name, version)

        with pytest.raises(ValueError) as exc_info:
            BuildConfig.from_pyproject_toml(pyproject_path)

        assert str(exc_info.value) == message

    @pytest.mark.parametrize(
        ("name", "message"),
        [
            (
                "System Monitor",
                "Invalid name in [project]: 'System Monitor'. A name may contain "
                "only ASCII letters, digits, '-', '_' and '.' and must start and "
                "end with a letter or digit; try 'system-monitor'.",
            ),
            (
                "Монітор",
                "Invalid name in [project]: 'Монітор'. A name may contain "
                "only ASCII letters, digits, '-', '_' and '.' and must start and "
                "end with a letter or digit; try 'monitor'.",
            ),
            (
                "my-app-",
                "Invalid name in [project]: 'my-app-'. A name may contain "
                "only ASCII letters, digits, '-', '_' and '.' and must start and "
                "end with a letter or digit; try 'my-app'.",
            ),
            (
                "!!!",
                "Invalid name in [project]: '!!!'. A name may contain "
                "only ASCII letters, digits, '-', '_' and '.' and must start and "
                "end with a letter or digit.",
            ),
        ],
        ids=["space", "non-ascii", "trailing-dash", "no-slug"],
    )
    def test_from_pyproject_rejects_invalid_project_name(
        self, tmp_path: Path, name: str, message: str
    ) -> None:
        """Test that a name uv rejects is reported with the slug as a fix."""
        pyproject_path = write_standalone_pyproject(tmp_path, name=name)

        with pytest.raises(ValueError) as exc_info:
            BuildConfig.from_pyproject_toml(pyproject_path)

        assert str(exc_info.value) == message

    def test_from_pyproject_accepts_unusual_valid_project_name(
        self, tmp_path: Path
    ) -> None:
        """Test that a valid name is kept as written and slugged for the build."""
        pyproject_path = write_standalone_pyproject(tmp_path, name="My_App.v2")

        config = BuildConfig.from_pyproject_toml(pyproject_path)

        assert config.project_name == "My_App.v2"
        assert config.dist_name == "my-app-v2-0.1.0-amd64"

    @pytest.mark.parametrize(
        ("version", "message"),
        [
            (
                "1.0 beta",
                "Invalid version in [project]: '1.0 beta'. "
                "Use a PEP 440 version such as '1.0.0' or '1.0b1'.",
            ),
            (
                "latest",
                "Invalid version in [project]: 'latest'. "
                "Use a PEP 440 version such as '1.0.0' or '1.0b1'.",
            ),
        ],
        ids=["space", "no-digits"],
    )
    def test_from_pyproject_rejects_invalid_project_version(
        self, tmp_path: Path, version: str, message: str
    ) -> None:
        """Test that a version uv rejects is reported with PEP 440 examples."""
        pyproject_path = write_standalone_pyproject(tmp_path, version=version)

        with pytest.raises(ValueError) as exc_info:
            BuildConfig.from_pyproject_toml(pyproject_path)

        assert str(exc_info.value) == message

    def test_from_pyproject_keeps_project_version_as_written(
        self, tmp_path: Path
    ) -> None:
        """Test that a valid version is not normalized: dist_name is built from it."""
        pyproject_path = write_standalone_pyproject(tmp_path, version="1.0-beta")

        config = BuildConfig.from_pyproject_toml(pyproject_path)

        assert config.project_version == "1.0-beta"
        assert config.dist_name == "test-app-1.0-beta-amd64"
