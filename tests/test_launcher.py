"""Tests that run launchers written by generate_exe against a probe script."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pyretort.builder.exe_generator import generate_exe
from pyretort.types import PythonArchitecture

pytestmark = pytest.mark.windows

ARM64_ONLY = pytest.mark.skipif(
    platform.machine() != "ARM64", reason="arm64 launchers run only on ARM64"
)
# win32 launchers run on x64 through WOW64; arm64 ones need an ARM64 machine.
LAUNCHER_VARIANTS = [
    pytest.param(PythonArchitecture.AMD64, True, id="amd64-console"),
    pytest.param(PythonArchitecture.AMD64, False, id="amd64-gui"),
    pytest.param(PythonArchitecture.WIN32, True, id="win32-console"),
    pytest.param(PythonArchitecture.WIN32, False, id="win32-gui"),
    pytest.param(PythonArchitecture.ARM64, True, id="arm64-console", marks=ARM64_ONLY),
    pytest.param(PythonArchitecture.ARM64, False, id="arm64-gui", marks=ARM64_ONLY),
]

# Written next to every launcher; reports what the child Python received.
# Modes come from the environment so that argv stays untouched.
PROBE = """\
import json
import os
import sys

result = {"argv": sys.argv[1:], "ppid": os.getppid()}
if os.environ.get("PROBE_READ_STDIN") == "1":
    result["stdin"] = sys.stdin.read()
print(json.dumps(result))
sys.exit(int(os.environ.get("PROBE_EXIT_CODE", "0")))
"""


def make_launcher(
    directory: Path,
    architecture: PythonArchitecture = PythonArchitecture.AMD64,
    show_console: bool = True,
) -> Path:
    """Write probe.py and a launcher that runs it with the base interpreter.

    sys.executable in a virtual environment is a redirector that starts the
    base interpreter as a child process, so the probe would not see the
    launcher as its parent; sys._base_executable is the interpreter itself.
    """
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "probe.py").write_text(PROBE, encoding="utf-8")
    launcher = directory / "app.exe"
    command = f'"{sys._base_executable}" "{{EXE_DIR}}\\probe.py"'
    generate_exe(
        target=launcher,
        command=command,
        show_console=show_console,
        architecture=architecture,
    )
    return launcher


def run_launcher(
    launcher: Path,
    *args: str,
    env: dict[str, str] | None = None,
    stdin: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run the launcher with args in its own directory and capture its output."""
    return subprocess.run(
        [str(launcher), *args],
        capture_output=True,
        cwd=launcher.parent,
        env={**os.environ, **(env or {})},
        input=stdin,
        timeout=60,
    )


def probe_result(completed: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    """Return the JSON the probe printed, or fail with the launcher's stderr."""
    assert completed.stdout, completed.stderr.decode("utf-8", "replace")
    result: dict[str, Any] = json.loads(completed.stdout)
    return result


ARGUMENT_LISTS = [
    pytest.param(["arg1", "two words"], id="space-inside-argument"),
    pytest.param([""], id="empty"),
    pytest.param(["a", "", "b"], id="empty-between"),
    pytest.param(['say "hi"'], id="quotes"),
    pytest.param(["a&b", "x|y", "a>out.txt", "^x", "%USERNAME%"], id="cmd-syntax"),
    pytest.param(["C:\\Program Files\\"], id="trailing-backslash-with-space"),
    pytest.param(["x\\\\", "y z\\"], id="backslashes"),
    pytest.param(["привіт", "світ"], id="cyrillic"),
    pytest.param(["日本", "😀", "é ü ß"], id="outside-cp1251"),
]


class TestLauncherArguments:
    """Tests for the arguments the launcher hands to the child Python."""

    @pytest.mark.parametrize(("architecture", "show_console"), LAUNCHER_VARIANTS)
    @pytest.mark.parametrize("args", ARGUMENT_LISTS)
    def test_launcher_passes_arguments_verbatim(
        self,
        tmp_path: Path,
        architecture: PythonArchitecture,
        show_console: bool,
        args: list[str],
    ) -> None:
        """Test that the child gets the arguments unchanged and no cmd.exe runs."""
        launcher = make_launcher(tmp_path, architecture, show_console)

        completed = run_launcher(launcher, *args)

        assert probe_result(completed)["argv"] == args
        assert not (tmp_path / "out.txt").exists()


class TestLauncherProcess:
    """Tests for how the launcher starts, finds and waits for the child Python."""

    def test_launcher_starts_python_directly(self, tmp_path: Path) -> None:
        """Test that the launcher itself is the parent of the child Python."""
        launcher = make_launcher(tmp_path)

        with subprocess.Popen(
            [str(launcher)], stdout=subprocess.PIPE, cwd=tmp_path
        ) as process:
            stdout, _ = process.communicate(timeout=60)

        assert json.loads(stdout)["ppid"] == process.pid

    def test_launcher_expands_exe_dir_with_spaces_and_non_ascii(
        self, tmp_path: Path
    ) -> None:
        """Test that {EXE_DIR} resolves to a directory with spaces and non-ASCII."""
        launcher = make_launcher(tmp_path / "dir with space тест 日本")

        completed = run_launcher(launcher, "arg1")

        assert probe_result(completed)["argv"] == ["arg1"]

    @pytest.mark.parametrize(("architecture", "show_console"), LAUNCHER_VARIANTS)
    def test_launcher_returns_child_exit_code(
        self, tmp_path: Path, architecture: PythonArchitecture, show_console: bool
    ) -> None:
        """Test that the launcher exits with the child's exit code."""
        launcher = make_launcher(tmp_path, architecture, show_console)

        completed = run_launcher(launcher, env={"PROBE_EXIT_CODE": "3"})

        assert completed.returncode == 3

    def test_launcher_passes_stdin(self, tmp_path: Path) -> None:
        """Test that the child reads what was written to the launcher's stdin."""
        launcher = make_launcher(tmp_path)

        completed = run_launcher(
            launcher, env={"PROBE_READ_STDIN": "1"}, stdin=b"hello from stdin"
        )

        assert probe_result(completed)["stdin"] == "hello from stdin"
