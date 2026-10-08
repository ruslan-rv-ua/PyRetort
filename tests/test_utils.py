"""Tests for pyretort.builder.utils module."""

import pytest

from pyretort.builder.utils import make_short_python_version


class TestMakeShortPythonVersion:
    """Tests for make_short_python_version function."""

    def test_version_313(self) -> None:
        """Test converting 3.13.0 to 313."""
        assert make_short_python_version("3.13.0") == "313"

    def test_version_311(self) -> None:
        """Test converting 3.11.5 to 311."""
        assert make_short_python_version("3.11.5") == "311"

    def test_version_312(self) -> None:
        """Test converting 3.12.0 to 312."""
        assert make_short_python_version("3.12.0") == "312"

    def test_version_310(self) -> None:
        """Test converting 3.10.1 to 310."""
        assert make_short_python_version("3.10.1") == "310"

    def test_version_39(self) -> None:
        """Test converting 3.9.18 to 39."""
        assert make_short_python_version("3.9.18") == "39"

    def test_version_two_part(self) -> None:
        """Test converting two-part version 3.13 to 313."""
        assert make_short_python_version("3.13") == "313"

    def test_version_preserves_double_digits(self) -> None:
        """Test that double digit minor versions are preserved."""
        assert make_short_python_version("3.11.0") == "311"
        assert make_short_python_version("3.12.4") == "312"

    @pytest.mark.parametrize(
        "version,expected",
        [
            ("3.11.0", "311"),
            ("3.11.9", "311"),
            ("3.12.0", "312"),
            ("3.12.5", "312"),
            ("3.13.0", "313"),
            ("3.13.1", "313"),
            ("3.9.0", "39"),
            ("3.10.0", "310"),
        ],
    )
    def test_parametrized_versions(self, version: str, expected: str) -> None:
        """Test various Python versions with parametrize."""
        assert make_short_python_version(version) == expected
