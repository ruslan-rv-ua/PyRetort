# Changelog

All notable changes to PyRetort are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `pyretort check` accepted a `[project]` name or version that uv rejects,
  such as `System Monitor` or `1.0 beta`, and `pyretort build` failed at the
  uv step, after it had already removed the previous build. Both commands now
  report such a name or version before the build starts.

## [0.2.0] - 2026-10-08

### Added

- Standalone mode: `install_as_package = false` builds a project that is not
  a package, as `uv init --no-package` creates it, without a `[build-system]`
  table.
  The build copies `project_source_subdir` into `<name>\app` of the
  application folder, installs `[project].dependencies` with
  `uv pip install -r pyproject.toml` and makes the launcher run `main_file`
  as a script, with the script's folder on the module search path.
- `pyretort init` picks standalone mode for a script in the project root, as
  `uv init --no-package` creates it: it writes `install_as_package = false`
  and, as `main_file`, the first of `main.py`, `app.py`, `cli.py` and
  `run.py` found there. Packages keep package mode.
- hello-script, an example of a console script built in standalone mode.
- SystemMonitor, an example of a GUI application (FastAPI, uvicorn, pywebview)
  built in standalone mode with dependencies pinned to exact versions.

### Fixed

- Building a project with a build backend other than `uv_build`, and
  installing a dependency that PyPI offers only as an sdist, failed with
  `Failed to create temporary virtualenv`. The build unpacked the standard
  library of the embedded Python into a directory named `python3XX.zip`, and
  uv copies that entry as a file into the environment in which it builds.
  The library now stays in the zip file, as python.org ships it.

## [0.1.0] - 2026-10-08

First public release.

### Added

- `pyretort build` turns a Python project into a standalone Windows
  application: one folder with an embedded Python from python.org, the project
  and its dependencies installed with uv, and an `.exe` launcher. With
  `create_dist_zip_file = true` the folder is also packed into a ZIP archive.
- The settings live in the `[tool.pyretort]` section of `pyproject.toml`:
  `pyretort init` writes them with comments, and `pyretort check` validates
  them. Any PEP 517 build backend works.
- The launcher starts the embedded Python directly, without `cmd.exe`, passes
  its arguments unchanged and exits with the program's exit code. It comes in
  a console and a GUI variant for `amd64`, `win32` and `arm64` and can carry an
  `.ico` icon.
- `pyretort cleanup` removes the downloaded Python packages, the build and the
  archive; `pyretort version` prints the installed version.
- `-p`/`--pyproject-toml` points `init`, `check`, `build` and `cleanup` at a
  project in another folder; the global `-q`/`--quiet` option silences the
  output.
- A missing `uv`, an embedded Python that cannot be downloaded, a failed
  installation and files of the previous build that are still in use end with
  a clear message instead of a traceback.
- Two examples: hello-cli, a console program, and Simple RSS, a wxPython
  application.

[unreleased]: https://github.com/ruslan-rv-ua/PyRetort/compare/v0.2.0...develop
[0.2.0]: https://github.com/ruslan-rv-ua/PyRetort/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ruslan-rv-ua/PyRetort/releases/tag/v0.1.0
