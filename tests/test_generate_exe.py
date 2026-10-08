"""Tests for pyretort.builder.exe_generator.generate_exe without an icon."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from pyretort.builder.exe_generator import generate_exe
from pyretort.builder.exe_generator.generate_exe import launcher_template
from pyretort.types import PythonArchitecture


def pe_machine_and_subsystem(exe: Path) -> tuple[int, int]:
    """Read Machine from the COFF header and Subsystem from the optional header."""
    data = exe.read_bytes()
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[pe_offset : pe_offset + 4] == b"PE\0\0"
    machine: int = struct.unpack_from("<H", data, pe_offset + 4)[0]
    # The optional header follows the 20-byte COFF header; Subsystem sits at
    # offset 68 in both PE32 and PE32+.
    subsystem: int = struct.unpack_from("<H", data, pe_offset + 24 + 68)[0]
    return machine, subsystem


class TestGenerateExe:
    """Tests for generate_exe writing a launcher from the template."""

    @pytest.mark.parametrize(
        ("architecture", "show_console", "machine", "subsystem"),
        [
            (PythonArchitecture.AMD64, True, 0x8664, 3),
            (PythonArchitecture.AMD64, False, 0x8664, 2),
            (PythonArchitecture.WIN32, True, 0x14C, 3),
            (PythonArchitecture.WIN32, False, 0x14C, 2),
            (PythonArchitecture.ARM64, True, 0xAA64, 3),
            (PythonArchitecture.ARM64, False, 0xAA64, 2),
        ],
    )
    def test_generate_exe_picks_template_for_console_and_architecture(
        self,
        tmp_path: Path,
        architecture: PythonArchitecture,
        show_console: bool,
        machine: int,
        subsystem: int,
    ) -> None:
        """Test that the PE header matches the architecture and the console flag."""
        target = tmp_path / "app.exe"

        generate_exe(
            target=target,
            command="python.exe",
            show_console=show_console,
            architecture=architecture,
        )

        assert pe_machine_and_subsystem(target) == (machine, subsystem)

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
