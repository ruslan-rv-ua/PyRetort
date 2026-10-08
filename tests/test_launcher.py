"""Tests that run launchers written by generate_exe against a probe script."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pyretort.builder.exe_generator import generate_exe

pytestmark = pytest.mark.windows

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


def make_launcher(directory: Path) -> Path:
    """Write probe.py and a launcher that runs it with the base interpreter.

    sys.executable in a virtual environment is a redirector that starts the
    base interpreter as a child process, so the probe would not see the
    launcher as its parent; sys._base_executable is the interpreter itself.
    """
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "probe.py").write_text(PROBE, encoding="utf-8")
    launcher = directory / "app.exe"
    command = f'"{sys._base_executable}" "{{EXE_DIR}}\\probe.py"'
    generate_exe(target=launcher, command=command)
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

    @pytest.mark.parametrize("args", ARGUMENT_LISTS)
    def test_launcher_passes_arguments_verbatim(
        self, tmp_path: Path, args: list[str]
    ) -> None:
        """Test that the child gets the arguments unchanged and no cmd.exe runs."""
        launcher = make_launcher(tmp_path)

        completed = run_launcher(launcher, *args)

        assert probe_result(completed)["argv"] == args
        assert not (tmp_path / "out.txt").exists()
