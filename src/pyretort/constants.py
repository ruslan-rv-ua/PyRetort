# whether to show spawned process consoles by default
SHOW_CONSOLE_DEFAULT = False

# Default directory name where built distributions/artifacts are placed
PYDIST_DIR_DEFAULT = "pydist"  

# cache directory for downloaded packages/files
DOWNLOAD_CACHE_DIR_DEFAULT = "downloads"

# directory for intermediate build outputs
BUILD_OUTPUT_DIR_DEFAULT = "build"

# directory for final distribution packages
DIST_OUTPUT_DIR_DEFAULT = "dist"

# Default blacklist of file patterns to exclude from application distribution.
# These patterns represent files and directories that should not be included in the final
# built application to reduce size and avoid including unnecessary or sensitive files.
# Used during the build process to filter out unwanted artifacts when packaging the application.
# Includes: bytecode, virtual environments, version control, IDE settings, test artifacts,
# build outputs, and other common development-related files.
DEFAULT_BLACKLIST = [
    # Python bytecode and cache
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__",
    "*.so",
    "*.dll",
    "*.dylib",
    # Virtual environments
    ".venv",
    "venv",
    "env",
    "ENV",
    ".env",
    # Version control
    ".git",
    ".gitignore",
    ".gitattributes",
    ".hg",
    ".svn",
    ".bzr",
    # IDEs and editors
    ".vscode",
    ".idea",
    "*.swp",
    "*.swo",
    "*~",
    ".DS_Store",
    # Testing and coverage
    ".pytest_cache",
    ".coverage",
    ".coverage.*",
    "coverage.xml",
    "htmlcov",
    ".tox",
    ".nox",
    ".benchmarks",
    # Build artifacts
    "*.egg-info",
    "*.egg",
    "dist",
    "build",
    ".eggs",
    "pip-wheel-metadata",
    "*.spec",  # PyInstaller
    # Dependency lock files
    "uv.lock",
    "poetry.lock",
    "pdm.lock",
    "pyproject.lock",
    ".pdm-build",
    # Documentation
    "docs/_build",
    # Windows-specific
    "Thumbs.db",
    "Desktop.ini",
    ".vs",
    # GitHub and CI
    ".github",
    "GITHUB_WORKFLOW",
    "GITHUB_ACTIONS",
    "GITHUB_*",
    ".github/*",
    # Kilocode (common patterns / guessed names)
    "kilocode",
    "kilocode.*",
    ".kilocode",
    # Editors and tools
    ".emacs.d",
    "*~.nib",
    "*.sublime-workspace",
    "*.sublime-project",
    ".idea/*",
    ".vscode/*",
    ".cache",
    ".m2",
    ".gradle",
    "node_modules",
    "npm-debug.log",
    "yarn-error.log",
    "pnpm-lock.yaml",
    "package-lock.json",
    "*.tsbuildinfo",
    # Docker and container artifacts
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.*.yml",
    "docker/*",
    # Continuous Integration / build system artifacts
    ".circleci",
    ".travis.yml",
    "appveyor.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
    "buildkite.yml",
    "ci",
    # Misc OS and tool artifacts
    ".DS_Store",
    "desktop.ini",
    "Icon?",
    ".spotlight-V100",
    ".Trash-*",
    # Misc
    "*.log",
    ".mypy_cache",
    ".ruff_cache",
    ".pytype",
    "*.orig",
    "*.bak",
    "*.tmp",
]
