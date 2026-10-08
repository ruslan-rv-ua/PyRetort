"""Tests for pyretort.builder.exe_generator.generate_exe without an icon."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyretort.builder.exe_generator import generate_exe
from pyretort.builder.exe_generator.generate_exe import launcher_template
from pyretort.types import PythonArchitecture


class TestGenerateExe:
    """Tests for generate_exe writing a launcher from the template."""

    def test_generate_exe_embeds_command_as_utf16(self, tmp_path: Path) -> None:
        """Test that the launcher is the template with the command in UTF-16LE."""
        target = tmp_path / "app.exe"
        command = '"{EXE_DIR}\\мій-застосунок\\python.exe" -m мій_застосунок'

        generate_exe(target=target, command=command)

        assert target.is_file()
        template = launcher_template(PythonArchitecture.AMD64, True)
        assert target.stat().st_size == template.stat().st_size
        assert command.encode("utf-16-le") in target.read_bytes()

    def test_generate_exe_rejects_command_longer_than_limit(
        self, tmp_path: Path
    ) -> None:
        """Test that a command over the template limit fails instead of being cut."""
        target = tmp_path / "app.exe"
        command = "x" * 1100

        with pytest.raises(ValueError, match="1100") as exc_info:
            generate_exe(target=target, command=command)

        assert "1023" in str(exc_info.value)
        assert not target.exists()

    def test_generate_exe_counts_the_limit_in_utf16_units(self, tmp_path: Path) -> None:
        """Test that a character outside the BMP takes two of the 1023 units."""
        target = tmp_path / "app.exe"
        command = "x" * 1022 + "😀"

        with pytest.raises(ValueError, match="1024"):
            generate_exe(target=target, command=command)

        assert not target.exists()
