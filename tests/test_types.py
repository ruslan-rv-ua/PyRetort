"""Tests for pyretort.types module."""

from pathlib import Path

import pytest

from pyretort.types import (
    MIN_PYTHON_VERSION,
    BuildConfig,
    PythonArchitecture,
)


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
            build_hash="test123",
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
            build_hash="test123",
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
                build_hash="test123",
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
                build_hash="test123",
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
                build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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
            build_hash="test123",
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

    def test_main_module_is_last_component_of_source_subdir(self) -> None:
        """Test that main_module is the package directory named by the subdir."""
        config = BuildConfig(
            build_hash="test123",
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
            build_hash="test123",
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

    def test_build_hash_is_generated(self, valid_pyproject_toml: Path) -> None:
        """Test that build_hash is properly generated."""
        config = BuildConfig.from_pyproject_toml(valid_pyproject_toml)
        assert config.build_hash is not None
        assert len(config.build_hash) == 64  # SHA256 hex digest length

    def test_build_hash_changes_with_dependencies(self, tmp_path: Path) -> None:
        """Test that build_hash changes when dependencies change."""
        import tomli_w

        data1 = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": ["httpx>=0.27.0"],
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

        data2 = {
            "project": {
                "name": "test-app",
                "version": "0.1.0",
                "dependencies": ["httpx>=0.27.0", "requests>=2.0.0"],
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

        p1 = tmp_path / "proj1" / "pyproject.toml"
        p1.parent.mkdir()
        (p1.parent / "src").mkdir()
        (p1.parent / "src" / "__main__.py").write_text("")
        p1.write_bytes(tomli_w.dumps(data1).encode())

        p2 = tmp_path / "proj2" / "pyproject.toml"
        p2.parent.mkdir()
        (p2.parent / "src").mkdir()
        (p2.parent / "src" / "__main__.py").write_text("")
        p2.write_bytes(tomli_w.dumps(data2).encode())

        config1 = BuildConfig.from_pyproject_toml(p1)
        config2 = BuildConfig.from_pyproject_toml(p2)

        assert config1.build_hash != config2.build_hash

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

    def test_main_file_does_not_exist(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when main file doesn't exist."""
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

        with pytest.raises(ValueError, match="Main file does not exist"):
            BuildConfig.from_pyproject_toml(pyproject_path)

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

    def test_from_pyproject_rejects_standalone_mode(self, tmp_path: Path) -> None:
        """Test that install_as_package = false is refused until task 12 lands."""
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

        with pytest.raises(
            ValueError,
            match="install_as_package = false \\(standalone mode\\) is not supported yet",
        ):
            BuildConfig.from_pyproject_toml(pyproject_path)
