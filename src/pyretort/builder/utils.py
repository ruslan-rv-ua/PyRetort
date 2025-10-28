def make_short_python_version(version: str) -> str:
    """Convert a Python version string to a short format.

    Examples:
        "3.13.0" -> "313"
        "3.11.5" -> "311"
        "3.10.1" -> "310"

    Args:
        version: A Python version string in the format "X.Y.Z" or "X.Y"

    Returns:
        A short version string combining major and minor version numbers
    """
    parts = version.split(".")
    major = parts[0]
    minor = parts[1]
    return f"{major}{minor}"
