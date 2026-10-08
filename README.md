# PyRetort

<p align="center"><img src="https://raw.githubusercontent.com/ruslan-rv-ua/PyRetort/develop/docs/assets/logo.png" alt="PyRetort logo" width="256"></p>

<p align="center">Turn your Python projects into standalone Windows applications that run without a Python installation.</p>

<p align="center">
<a href="https://github.com/ruslan-rv-ua/PyRetort/actions/workflows/ci.yml"><img src="https://github.com/ruslan-rv-ua/PyRetort/actions/workflows/ci.yml/badge.svg?branch=develop" alt="CI"></a>
<img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="python 3.11+">
<a href="https://github.com/ruslan-rv-ua/PyRetort/blob/develop/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license MIT"></a>
<img src="https://img.shields.io/badge/platform-Windows-blue" alt="platform Windows">
</p>

PyRetort puts your project, its dependencies and an embedded Python into one
folder with a small `.exe` launcher. Copy the folder, or its ZIP archive, to
another Windows computer, and the application runs there as is.

## Windows only

PyRetort runs only on Windows and builds only Windows applications: the
embedded Python it bundles and the launcher it generates are Windows programs.
To package a project for several operating systems, use a cross-platform tool
such as [PyInstaller](https://pyinstaller.org/) or
[cx_Freeze](https://cx-freeze.readthedocs.io/).

## Who is it for

- Developers who want to share a Python application with people who don't have
  Python.
- Teams that hand out internal tools.
- Open-source projects that want to offer a ready-to-run `.exe`.

## Requirements

To build applications you need:

- Windows;
- Python 3.11 or later to run PyRetort itself;
- [uv](https://docs.astral.sh/uv/) in `PATH`: the build installs your project
  with `uv pip install`;
- internet access during the build: the embeddable Python comes from
  python.org (once per project, version and architecture; later builds reuse
  it from `downloads/`), and uv fetches your project's dependencies.

The people who run a built application need no Python: any Windows version
that the bundled Python release supports will do.

## Installation

From the source repository:

```powershell
uv tool install git+https://github.com/ruslan-rv-ua/PyRetort
```

From PyPI:

```powershell
uv tool install pyretort
```

`uv tool install` puts the `pyretort` command on `PATH`. Check that it works:

```powershell
pyretort version
```

Changes between versions are listed in
[CHANGELOG.md](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/CHANGELOG.md).

## Quick start

PyRetort builds a project that has:

- a `pyproject.toml` with `name` and `version` in `[project]` and a
  `[build-system]` table; any build backend works;
- a package with a `__main__.py`: the launcher starts the application with
  `python -m <package>`.

A project without a package, for example one created with
`uv init --no-package`, is built in [standalone mode](#standalone-mode)
instead: the build copies the sources and the launcher runs a script.

A project created with `uv init --package` lacks only the `__main__.py`:

```powershell
uv init --package hello
cd hello
```

Create `src\hello\__main__.py`, so that `python -m hello` runs the program:

```python
from hello import main

main()
```

Add the PyRetort settings to `pyproject.toml`:

```powershell
pyretort init
```

`init` writes a commented `[tool.pyretort]` section (see
[Configuration](#configuration)). `hello` prints to the console, so set
`show_console_window = true` in that section; the default, `false`, suits GUI
applications. Then validate the configuration and build:

```powershell
pyretort check
pyretort build
```

The build creates these folders next to `pyproject.toml`:

```text
hello/
├── downloads/
│   └── python-<version>-embed-amd64.zip   embeddable Python, reused by later builds
├── build/
│   └── hello-0.1.0-amd64/                 the application folder
│       ├── hello.exe                      the launcher
│       └── hello/                         embedded Python with your project installed
└── dist/
    └── hello-0.1.0-amd64.zip              the application folder as one archive
```

The names follow the pattern `<name>-<version>-<architecture>`, where `<name>`
is the project name in lowercase with dashes. Run the launcher:

```powershell
build\hello-0.1.0-amd64\hello.exe
```

```text
Hello from hello!
```

To share the application, copy the `build\hello-0.1.0-amd64` folder or send
the ZIP archive: it unpacks into the same single folder and runs on another
Windows computer without Python.

Four complete projects live in the repository: a console program, a console
script in standalone mode, a wxPython application and a pywebview application
in standalone mode. See the
[examples](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/examples/README.md).

### Commands

| Command | What it does |
|---|---|
| `pyretort init` | Adds a `[tool.pyretort]` section with values detected from the project and picks [standalone mode](#standalone-mode) for scripts in the project root; `--force` replaces an existing one. |
| `pyretort check` | Validates the configuration and the files and folders it names. |
| `pyretort build` | Builds `build/<name>-<version>-<architecture>/` and, with `create_dist_zip_file = true`, the archive in `dist/`. |
| `pyretort cleanup [targets]` | Removes `downloads/` (target `cache`), `build/` and `dist/` (target `build`), or all three (`all`, the default). |
| `pyretort version` | Prints the installed version. |

`init`, `check`, `build` and `cleanup` work on `pyproject.toml` in the current
folder; `-p` (`--pyproject-toml`) points them at another one, for example
`pyretort build -p path\to\pyproject.toml`. `cleanup` removes the folders next
to that file. The global option `-q` (`--quiet`) goes before the command and
suppresses all output: `pyretort -q build`.

## Configuration

PyRetort reads the `[tool.pyretort]` section of `pyproject.toml`; the name and
the version of the application come from `[project]`. `pyretort init` writes
the section with a comment above every field. Without the comments, the
section of the Quick start project looks like this (`python_version` depends
on the Python that runs PyRetort):

```toml
[tool.pyretort]
project_source_subdir = "src/hello"
install_as_package = true
python_version = "3.13.9"
python_architecture = "amd64"
show_console_window = true
create_dist_zip_file = true
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `project_source_subdir` | string | yes | — | Folder of the package, relative to the project root, for example `"src/hello"`. Its last component is the module the launcher runs with `python -m`. `"."` means that the sources lie in the project root: the module is then the project name in lowercase with underscores, as a `<module>/__main__.py` package or a `<module>.py` file. In [standalone mode](#standalone-mode) it is the folder whose contents are copied into the application; `"."` copies the project root without the excluded files. |
| `python_version` | string | yes | — | Version of the embedded Python, 3.11 or later, for example `"3.13.9"`. python.org must have a Windows embeddable package for it; security-only releases have none. `init` writes the version of the Python that runs PyRetort. |
| `python_architecture` | string | yes | — | `"amd64"`, `"win32"` or `"arm64"`: the architecture of the embedded Python and of the launcher. The build runs the embedded Python, so an `arm64` build needs Windows on ARM. `init` writes `amd64` for a 64-bit Python and `win32` for a 32-bit one. |
| `create_dist_zip_file` | boolean | yes | — | Also pack the application folder into `dist/<name>-<version>-<architecture>.zip`. `init` writes `true`. |
| `show_console_window` | boolean | no | `false` | `true` for console programs: the launcher runs in a console window and shares it with the program. `false` for GUI applications: no console window appears. |
| `icon_file_rel_path` | string | no | no icon | Path to an `.ico` file, relative to the project root; it becomes the icon of the launcher. Include images of 16, 32, 48 and 256 px, so that Windows shows a sharp icon at every size. |
| `install_as_package` | boolean | no | `true` | `true`: install the project into the embedded Python as a package; the launcher runs `python -m <module>`. `false`: [standalone mode](#standalone-mode), the build copies the sources and the launcher runs `main_file` as a script. |
| `main_file` | string | when `install_as_package = false` | — | Script the launcher runs in standalone mode, relative to `project_source_subdir`, for example `"main.py"`. Ignored in package mode. |

### Standalone mode

Choose `install_as_package = false` for a project that is not a package: a
script with the modules it imports next to it, as `uv init --no-package`
creates. Such a project needs neither a `[build-system]` table nor a
`__main__.py`; the launcher runs `main_file` as a script.

```toml
[tool.pyretort]
project_source_subdir = "."
main_file = "main.py"
install_as_package = false
python_version = "3.13.9"
python_architecture = "amd64"
show_console_window = true
create_dist_zip_file = true
```

`pyretort init` picks standalone mode by itself for scripts in the project
root. It writes `install_as_package = false` and `main_file` when all of these
hold, where `<module>` is the project name in lowercase with underscores:

- there is no `<module>` folder in the project root or in `src`, `source`,
  `app` or `lib`, so `project_source_subdir` is `"."`;
- there is no `<module>.py` in the project root, which `python -m <module>`
  would run;
- the project root holds `main.py`, `app.py`, `cli.py` or `run.py`; the first
  of them in this order becomes `main_file`.

Otherwise `init` writes `install_as_package = true`. This includes a package
that has a `main.py` but no `__main__.py`: such a file often imports its
neighbours relatively, as in `from .database import …`, which fails when it
runs as a script. `init` then warns about the missing `__main__.py`.

The build copies `project_source_subdir` into `<name>\app` inside the
application folder and installs `[project].dependencies` into the embedded
Python with `uv pip install -r pyproject.toml`. Nothing else is installed, so
`dependencies` may not be listed in `[project].dynamic`, and `python_version`
must satisfy `requires-python`, which uv does not check here. The copy leaves
out:

- directly in the project root: `build`, `dist`, `downloads`, `venv`, `env`
  and `ci`. A folder with the same name deeper in the tree, such as
  `ui\dist` of a built frontend, is copied;
- at any depth: `__pycache__`, `*.pyc`, `.venv`, `.git`, `.github`, `tests`,
  the settings of IDEs, the caches of pytest, mypy and ruff, `uv.lock` and
  other lock files, `*.log`, `*.bak` and similar development files. Binary
  modules and libraries (`*.pyd`, `*.dll`) and folders such as `icons` are
  copied.

The folder of `main_file` is on the module search path of the application,
so the script imports its neighbours as usual. The files it ships with lie
next to it in `<name>\app`: open them through `Path(__file__).parent`, because
the working directory stays the one the launcher was started from. The
[hello-script](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/examples/hello-script/README.md)
example is such a project.

## How it works

`pyretort build` assembles the application folder
`build/<name>-<version>-<architecture>/`:

1. **Embedded Python.** It downloads the Windows embeddable package
   `python-<version>-embed-<architecture>.zip` from python.org into
   `downloads/` and unpacks it into the `<name>` subfolder. Later builds reuse
   the downloaded archive. The standard library stays in `python<XY>.zip`, as
   python.org ships it: uv copies that file into the environment in which it
   builds the project and the dependencies that come without a wheel.
2. **`._pth` file.** The embeddable Python takes its module search path from
   its `python<XY>._pth` file only. PyRetort rewrites that file so that
   `import site` runs and the packages in `Lib\site-packages` can be imported.
   In standalone mode the file also lists the folder of `main_file` inside
   `app`, because a `._pth` file puts Python into isolated mode, which keeps
   the script's folder off `sys.path`.
3. **Your project.** `uv pip install --python <name>\python.exe <project>`
   builds the project with its own build backend and installs it, together
   with its dependencies, into that Python. In standalone mode the build
   instead copies `project_source_subdir` into `<name>\app` and runs
   `uv pip install --python <name>\python.exe -r pyproject.toml`, which
   installs `[project].dependencies` only.
4. **Launcher.** `<name>.exe` is a small program compiled from
   [`launcher/launcher.c`](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/launcher/launcher.c),
   in the console or the GUI variant and for the architecture of the embedded
   Python. The build writes the command `"{EXE_DIR}\<name>\python.exe" -m <module>`,
   or in standalone mode
   `"{EXE_DIR}\<name>\python.exe" "{EXE_DIR}\<name>\app\<main_file>"`, into
   it and adds the icon, if one is set.
5. **Archive.** With `create_dist_zip_file = true` the folder is packed into
   `dist/<name>-<version>-<architecture>.zip`.

When someone runs `<name>.exe`, the launcher replaces `{EXE_DIR}` with its own
folder, appends its command-line arguments exactly as it received them and
starts Python directly, without `cmd.exe`. Quotes, spaces, non-ASCII text and
characters such as `&`, `|` and `%` reach the program unchanged. The launcher
waits for the program and exits with its exit code. The GUI variant opens no
console window.

## Troubleshooting

- `Configuration file not found: …\pyproject.toml` → run PyRetort in the
  project folder or pass the file: `pyretort build -p path\to\pyproject.toml`.
- `Missing [tool.pyretort] section in pyproject.toml. Run 'pyretort init' to create it.`
  → run `pyretort init`.
- `Package mode requires '…\__main__.py': the launcher runs 'python -m …'. Point project_source_subdir at the package directory or add __main__.py.`
  → set `project_source_subdir` to the folder of your package, for example
  `src/hello`, or add `__main__.py` to the package. A project without a
  package is built in [standalone mode](#standalone-mode).
- `Standalone mode (install_as_package = false) requires 'main_file' in [tool.pyretort]`
  → set `main_file` to the script the launcher should run, relative to
  `project_source_subdir`, for example `main_file = "main.py"`.
- `Invalid name in [project]: '…'. …` → uv accepts only a name of ASCII
  letters, digits, `-`, `_` and `.` that starts and ends with a letter or a
  digit. PyRetort names the `.exe` and the folders after the name in
  lowercase with hyphens anyway (`System Monitor` would give
  `system-monitor.exe`), so the suggested name builds the same application.
- `Invalid version in [project]: '…'. …` → uv accepts only a
  [PEP 440](https://packaging.python.org/en/latest/specifications/version-specifiers/)
  version, such as `1.0.0` or `1.0b1`.
- `uv was not found in PATH. Install uv: https://docs.astral.sh/uv/getting-started/installation/`
  → install uv, then open a new terminal.
- `Could not prepare the build directory …: [WinError 5] Access is denied: …`
  → the application from the previous build is still running, or another
  program holds its files. Close it and run the build again.
- `python.org has no Windows embeddable package for Python … (…): https://www.python.org/ftp/python/…/python-…-embed-….zip`
  → security-only releases don't ship one. Set `python_version` to a release
  that has one: `init` writes the version of the Python that runs PyRetort,
  which can be such a release.
- `Could not download the embedded Python … (…): …` → check the internet
  connection and run the build again. Behind a proxy, set the `HTTPS_PROXY`
  and `HTTP_PROXY` environment variables: PyRetort downloads through httpx,
  which reads them.
- `uv pip install failed with exit code 2: … (os error 216)` → this computer
  cannot run the embedded Python of the chosen architecture: build `arm64` on
  Windows on ARM.

## Limitations

- **Standalone mode copies only `project_source_subdir`.** Files outside
  that folder, for example a `data` folder next to a `src` source folder,
  do not reach the application: keep them under the source folder, or make
  the project a package.
- **No code protection.** The application ships as ordinary Python files in
  `Lib\site-packages` or `<name>\app`; anyone who has the folder can read
  your code.
- **Windows only.** PyRetort runs on Windows and builds only Windows
  applications.
- **Size.** Every application carries its own Python: the folder of a project
  without dependencies takes about 25 MB, its archive about 11 MB.

## Credits

PyRetort started from [gen-exe](https://github.com/silvandeleemput/gen-exe) by
Sil C. van de Leemput. The code that adds an icon to the launcher comes from
it; the launcher itself is PyRetort's own. gen-exe is distributed under the MIT
License; see
[THIRD_PARTY_LICENSES.md](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/THIRD_PARTY_LICENSES.md).

## License

PyRetort is distributed under the
[MIT License](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/LICENSE).
