from __future__ import annotations

# whether to show spawned process consoles by default
SHOW_CONSOLE_DEFAULT = False

# whether to install the project as a package by default
INSTALL_AS_PACKAGE_DEFAULT = True

# cache directory for downloaded packages/files
DOWNLOAD_DIR_DEFAULT = "downloads"

# directory for intermediate build outputs
BUILD_DIR_DEFAULT = "build"

# directory for final distribution packages
DIST_DIR_DEFAULT = "dist"

# Entries of the project root that the standalone build leaves out of the copy
# of the sources: PyRetort's own folders, virtual environments and CI files.
# They are skipped only directly in the project root (the copy starts there when
# project_source_subdir is "."), so a folder with the same name deeper in the
# tree, such as ui/dist/ of a built frontend, is copied.
PROJECT_ROOT_EXCLUDES = [
    BUILD_DIR_DEFAULT,
    DIST_DIR_DEFAULT,
    DOWNLOAD_DIR_DEFAULT,
    "venv",
    "env",
    "ci",
]

# Names that the standalone build leaves out of the copy of the sources at any
# depth: bytecode, version control, IDE settings, test and tool caches, lock
# files and other development files. A name is compared with every pattern
# through fnmatch, like shutil.ignore_patterns does, so the match is
# case-insensitive on Windows and a pattern cannot name a path.
DEFAULT_BLACKLIST = [
    # === Python artifacts ===
    "*.pyc",
    "*.pyo",
    "__pycache__",
    "*.egg-info",
    "*.egg",
    ".eggs",
    "*.spec",  # PyInstaller
    # === Virtual environments ===
    ".venv",
    ".env",
    # === Build outputs ===
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
    "tests",
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
    "desktop.ini",
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
    # === Docker ===
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.*.yml",
    # === Node.js ===
    "node_modules",
    "npm-debug.log",
    "yarn-error.log",
    # === Java/Maven/Gradle ===
    ".m2",
    ".gradle",
    # === Misc ===
    "*.log",
    "*.orig",
    "*.bak",
    "*.tmp",
    ".cache",
]
