from __future__ import annotations

# whether to show spawned process consoles by default
SHOW_CONSOLE_DEFAULT = False

# whether to install the project as a package by default
INSTALL_AS_PACKAGE_DEFAULT = True

# Default directory name where built distributions/artifacts are placed
PYDIST_DIR_DEFAULT = "pydist"

# cache directory for downloaded packages/files
DOWNLOAD_DIR_DEFAULT = "downloads"

# directory for intermediate build outputs
BUILD_DIR_DEFAULT = "build"

# directory for final distribution packages
DIST_DIR_DEFAULT = "dist"

# Default blacklist of file patterns to exclude from application distribution.
# These patterns represent files and directories that should not be included in the final
# built application to reduce size and avoid including unnecessary or sensitive files.
# Used during the build process to filter out unwanted artifacts when packaging the application.
# Includes: bytecode, virtual environments, version control, IDE settings, test artifacts,
# build outputs, and other common development-related files.
DEFAULT_BLACKLIST = [
    # === Python artifacts ===
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__",
    "*.so",
    "*.dll",
    "*.dylib",
    "*.egg-info",
    "*.egg",
    ".eggs",
    "*.spec",  # PyInstaller
    # === Virtual environments ===
    ".venv",
    "venv",
    "env",
    "ENV",
    ".env",
    # === Build outputs ===
    "build",
    "dist",
    "pip-wheel-metadata",
    # === Version control ===
    ".git",
    ".gitignore",
    ".gitattributes",
    ".hg",
    ".svn",
    ".bzr",
    # === IDE/Editor ===
    ".vscode",
    ".idea",
    ".vs",
    "*.swp",
    "*.swo",
    "*~",
    "*~.nib",
    "*.sublime-workspace",
    "*.sublime-project",
    ".emacs.d",
    # === Testing ===
    ".pytest_cache",
    ".coverage",
    ".coverage.*",
    "coverage.xml",
    "htmlcov",
    ".tox",
    ".nox",
    ".benchmarks",
    # === Type checking ===
    ".mypy_cache",
    ".ruff_cache",
    ".pytype",
    "*.tsbuildinfo",
    # === OS files ===
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",  # Windows is case-insensitive
    "Icon?",
    ".spotlight-V100",
    ".Trash-*",
    # === Dependency locks ===
    "uv.lock",
    "poetry.lock",
    "pdm.lock",
    "pyproject.lock",
    ".pdm-build",
    "pnpm-lock.yaml",
    "package-lock.json",
    # === CI/CD ===
    ".github",
    ".circleci",
    ".travis.yml",
    "appveyor.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
    "buildkite.yml",
    "ci",
    # === Docker ===
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.*.yml",
    "docker/*",
    # === Node.js ===
    "node_modules",
    "npm-debug.log",
    "yarn-error.log",
    # === Java/Maven/Gradle ===
    ".m2",
    ".gradle",
    # === Documentation ===
    "docs/_build",
    # === Kilocode ===
    "kilocode",
    "kilocode.*",
    ".kilocode",
    # === Misc ===
    "*.log",
    "*.orig",
    "*.bak",
    "*.tmp",
    ".cache",
]
