"""Build the launcher templates from launcher/launcher.c with zig cc.

Run from the repository root:

    uv run --group launcher python launcher/build.py          # write the templates
    uv run --group launcher python launcher/build.py --check  # compare with a fresh build

The templates are src/pyretort/builder/exe_generator/templates/launcher-<arch>-<variant>
for every PythonArchitecture and the console and gui variants; generate_exe names
them through launcher_template. zig cc produces byte-identical files for the same
source and flags, so --check rebuilds into a temporary directory and compares: it
exits with 1 and lists the files that differ.
"""

from __future__ import annotations

import argparse
import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

from pyretort.builder.exe_generator.generate_exe import (
    COMMAND_CAPACITY,
    COMMAND_PLACEHOLDER,
    TEMPLATES_DIR,
    launcher_template,
)
from pyretort.types import PythonArchitecture

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "launcher" / "launcher.c"

ZIG_TARGETS: dict[PythonArchitecture, str] = {
    PythonArchitecture.AMD64: "x86_64-windows-gnu",
    PythonArchitecture.WIN32: "x86-windows-gnu",
    PythonArchitecture.ARM64: "aarch64-windows-gnu",
}
COMMON_FLAGS = ["-municode", "-Os", "-s", "-Wall", "-Wextra", "-Werror"]


def variant_flags(show_console: bool) -> list[str]:
    """Return the flags for the console variant (wmain) or the GUI one (wWinMain)."""
    if show_console:
        return ["-Wl,--subsystem,console"]
    return ["-DPYRETORT_GUI", "-Wl,--subsystem,windows"]


def verify_placeholder(template: Path) -> None:
    """Exit with an error unless the region generate_exe overwrites is intact.

    launcher.c declares command_template as COMMAND_CAPACITY UTF-16 units holding
    COMMAND_PLACEHOLDER and then zeros; the linker must keep all of them in the file.
    """
    data = template.read_bytes()
    marker = COMMAND_PLACEHOLDER.encode("utf-16-le")
    count = data.count(marker)
    if count != 1:
        raise SystemExit(
            f"{template}: expected the command placeholder once, found {count}"
        )
    start = data.index(marker)
    region = data[start : start + COMMAND_CAPACITY * 2]
    if region != marker.ljust(COMMAND_CAPACITY * 2, b"\0"):
        raise SystemExit(
            f"{template}: the command placeholder is not followed by zeros "
            f"up to {COMMAND_CAPACITY} UTF-16 units"
        )


def compile_template(
    architecture: PythonArchitecture, show_console: bool, output: Path
) -> None:
    """Compile launcher.c for one architecture and variant into output."""
    command = [
        sys.executable,
        "-m",
        "ziglang",
        "cc",
        "-target",
        ZIG_TARGETS[architecture],
        *COMMON_FLAGS,
        *variant_flags(show_console),
        "-o",
        str(output),
        str(SOURCE),
    ]
    subprocess.run(command, check=True)
    verify_placeholder(output)


def build_all(directory: Path) -> list[Path]:
    """Compile every template into directory and return their paths."""
    directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for architecture in PythonArchitecture:
        for show_console in (True, False):
            output = directory / launcher_template(architecture, show_console).name
            compile_template(architecture, show_console, output)
            outputs.append(output)
    return outputs


def check() -> int:
    """Rebuild into a temporary directory; return 1 if any template differs."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        fresh = build_all(Path(temp))
        stale = [
            output.name
            for output in fresh
            if not (TEMPLATES_DIR / output.name).is_file()
            or not filecmp.cmp(output, TEMPLATES_DIR / output.name, shallow=False)
        ]
    if stale:
        print(
            "Launcher templates differ from launcher/launcher.c; rebuild them with "
            "'uv run --group launcher python launcher/build.py':",
            file=sys.stderr,
        )
        for name in stale:
            print(f"  {name}", file=sys.stderr)
        return 1
    print(f"All {len(fresh)} launcher templates match launcher/launcher.c")
    return 0


def main() -> int:
    """Build the templates, or compare them with a fresh build under --check."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="rebuild into a temporary directory and compare with the committed files",
    )
    args = parser.parse_args()
    if not TEMPLATES_DIR.is_relative_to(REPO_ROOT):
        raise SystemExit(
            f"pyretort is not installed from this checkout ({REPO_ROOT}); "
            f"its templates are at {TEMPLATES_DIR}"
        )
    if args.check:
        return check()
    for output in build_all(TEMPLATES_DIR):
        print(f"{output.relative_to(REPO_ROOT)}: {output.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
