import platform
import sys

from pyretort.types import PythonArchitecture


def get_current_python_version() -> str:
    """Get the current Python version as a string e.g. 3.11.9."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_current_python_architecture() -> PythonArchitecture:
    """Get the current Python architecture as a string."""
    machine = platform.machine().lower()
    if machine == "amd64":
        return PythonArchitecture.AMD64
    if machine == "arm64":
        return PythonArchitecture.ARM64
    # For 32-bit, platform.machine() can be x86, i386, i686.
    # We'll assume anything else is 32-bit for now.
    # A more robust check could involve sys.maxsize.
    # However, for the purposes of this application, 'win32' is used for 32-bit.
    # The value 'win32' is more of a platform identifier than an architecture,
    # but it's what's used in Python's own distribution channels for 32-bit builds.
    # A simple check for 'x86' should suffice for our supported architectures.
    if "x86" in machine or "i386" in machine or "i686" in machine:
        return PythonArchitecture.WIN32

    # Fallback or error
    raise ValueError(f"Unsupported architecture: {platform.machine()}")
