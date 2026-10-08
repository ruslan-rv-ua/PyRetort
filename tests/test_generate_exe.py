"""Tests for pyretort.builder.exe_generator.generate_exe without an icon."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyretort.builder.exe_generator import generate_exe
from pyretort.builder.exe_generator.generate_exe import EXE_TEMPLATE_FILE


class TestGenerateExe:
    """Tests for generate_exe writing a launcher from the template."""

    def test_generate_exe_embeds_command_into_template(self, tmp_path: Path) -> None:
        """Test that the launcher is the template with the command written into it."""
        target = tmp_path / "app.exe"
        command = '"{EXE_DIR}\\my-app\\python.exe" -m my_app'

        generate_exe(target=target, command=command)

        assert target.is_file()
        assert target.stat().st_size == EXE_TEMPLATE_FILE.stat().st_size
        assert command.encode("ascii") in target.read_bytes()

    def test_generate_exe_rejects_command_longer_than_limit(
        self, tmp_path: Path
    ) -> None:
        """Test that a command over the template limit fails instead of being cut."""
        target = tmp_path / "app.exe"
        command = "x" * 300

        with pytest.raises(ValueError, match="300") as exc_info:
            generate_exe(target=target, command=command)

        assert "259" in str(exc_info.value)
        assert not target.exists()
