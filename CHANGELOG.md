# Changelog

All notable changes to PyRetort are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Work towards the first release, 0.1.0, since development started in October
2025.

### Added

- The `pyretort` command with `version`, `init`, `check`, `build` and
  `cleanup`.
- `pyretort init` writes a commented `[tool.pyretort]` section into
  `pyproject.toml`: the package folder, the version and architecture of the
  Python that runs PyRetort and the defaults of the other fields. It refuses
  to replace an existing section unless `--force` is given, and warns when the
  package has no `__main__.py`.
- `pyretort check` validates the configuration and the files and folders it
  names, including the `__main__.py` that `python -m <package>` needs.
- `pyretort build` downloads the Windows embeddable Python from python.org,
  keeps it in `downloads/` for later builds, installs the project into it with
  `uv pip install` and writes the `<name>.exe` launcher with an optional icon.
  It reports its progress step by step.
- With `create_dist_zip_file = true` the build also writes
  `dist/<name>-<version>-<architecture>.zip`, which unpacks into a single
  folder.
- Launchers for `amd64`, `win32` and `arm64`, each in a console and a GUI
  variant. Their source is `launcher/launcher.c`, and `launcher/build.py`
  builds them reproducibly with `zig cc`.
- `pyretort cleanup [cache|build|all]` removes `downloads/`, `build/` and
  `dist/` next to `pyproject.toml`; without arguments it removes all three.
- The `-p`/`--pyproject-toml` option of `init`, `check`, `build` and `cleanup`,
  and the global `-q`/`--quiet` option.
- Examples: hello-cli, a console program, and Simple RSS, a wxPython
  application with third-party dependencies.
- README, this changelog, the third-party notice for gen-exe, the logo and
  the package metadata.

### Changed

- The launcher runs `python -m <module>`, where `<module>` is the last
  component of `project_source_subdir` (`src/simple_rss` runs `simple_rss`).
  It used to be the project name, which worked only when the two matched.
- Any PEP 517 build backend works. Before, `pyretort build` accepted only
  `uv_build`, and `pyretort check` only `uv_build` and `hatchling`.
- `install_as_package = false` (standalone mode) is rejected by `check` and
  `build` with a clear message, before anything is written to disk. It used to
  fail in the middle of the build.

### Fixed

- The launcher no longer runs the application through `cmd.exe`: it starts
  the embedded Python directly and passes its own arguments exactly as it
  received them. Before, `cmd.exe` split `"two words"` into two arguments and
  interpreted characters such as `&`, `|`, `>`, `^` and `%`; characters
  outside the system code page were lost in arguments, and the application
  did not start from a folder whose name contained them. GUI applications no
  longer flash a console window, and `win32` and `arm64` builds get a launcher
  of their own architecture.
- `pyretort build` reports a missing `uv`, a failed `uv pip install` and build
  files locked by a running application with a clear message and exit code 1
  instead of a traceback.
- The icon path is resolved against the project folder instead of the current
  folder.
- A command that does not fit into the launcher stops the build with an error
  instead of being cut off silently.
- A configuration that `init` writes for a package without `main.py` passes
  `check` and `build` unchanged: `main_file` is ignored in package mode, and a
  missing `install_as_package` or `show_console_window` takes its default.
- `pyretort cleanup` exits with code 1 when a folder cannot be removed, and
  still removes the other folders.
- `pyretort init` no longer prints debug output, reports a `pyproject.toml` it
  cannot write without a traceback, and writes accurate comments.

### Removed

- The launcher template from gen-exe, replaced by PyRetort's own launcher.
- The outdated SystemMonitor example.

[unreleased]: https://github.com/ruslan-rv-ua/PyRetort/commits/develop
