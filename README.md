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

From PyPI (planned: PyRetort is not published there yet):

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

Two complete projects live in the repository: a console program and a GUI
application with third-party dependencies. See the
[examples](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/examples/README.md).

### Commands

| Command | What it does |
|---|---|
| `pyretort init` | Adds a `[tool.pyretort]` section with values detected from the project; `--force` replaces an existing one. |
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
| `project_source_subdir` | string | yes | — | Folder of the package, relative to the project root, for example `"src/hello"`. Its last component is the module the launcher runs with `python -m`. `"."` means that the sources lie in the project root: the module is then the project name in lowercase with underscores, as a `<module>/__main__.py` package or a `<module>.py` file. |
| `python_version` | string | yes | — | Version of the embedded Python, 3.11 or later, for example `"3.13.9"`. python.org must have a Windows embeddable package for it; security-only releases have none. `init` writes the version of the Python that runs PyRetort. |
| `python_architecture` | string | yes | — | `"amd64"`, `"win32"` or `"arm64"`: the architecture of the embedded Python and of the launcher. The build runs the embedded Python, so an `arm64` build needs Windows on ARM. `init` writes `amd64` for a 64-bit Python and `win32` for a 32-bit one. |
| `create_dist_zip_file` | boolean | yes | — | Also pack the application folder into `dist/<name>-<version>-<architecture>.zip`. `init` writes `true`. |
| `show_console_window` | boolean | no | `false` | `true` for console programs: the launcher runs in a console window and shares it with the program. `false` for GUI applications: no console window appears. |
| `icon_file_rel_path` | string | no | no icon | Path to an `.ico` file, relative to the project root; it becomes the icon of the launcher. Include images of 16, 32, 48 and 256 px, so that Windows shows a sharp icon at every size. |
| `install_as_package` | boolean | no | `true` | Install the project into the embedded Python as a package. Only `true` works; `false`, standalone mode, is planned. |
| `main_file` | string | no | — | Ignored: reserved for the planned standalone mode. |

## How it works

`pyretort build` assembles the application folder
`build/<name>-<version>-<architecture>/`:

1. **Embedded Python.** It downloads the Windows embeddable package
   `python-<version>-embed-<architecture>.zip` from python.org into
   `downloads/` and unpacks it into the `<name>` subfolder. Later builds reuse
   the downloaded archive.
2. **`._pth` file.** The embeddable Python takes its module search path from
   its `python<XY>._pth` file only. PyRetort rewrites that file so that
   `import site` runs and the packages in `Lib\site-packages` can be imported.
3. **Your project.** `uv pip install --python <name>\python.exe <project>`
   builds the project with its own build backend and installs it, together
   with its dependencies, into that Python.
4. **Launcher.** `<name>.exe` is a small program compiled from
   [`launcher/launcher.c`](https://github.com/ruslan-rv-ua/PyRetort/blob/develop/launcher/launcher.c),
   in the console or the GUI variant and for the architecture of the embedded
   Python. The build writes the command `"{EXE_DIR}\<name>\python.exe" -m <module>`
   into it and adds the icon, if one is set.
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
  `src/hello`, or add `__main__.py` to the package.
- `uv was not found in PATH. Install uv: https://docs.astral.sh/uv/getting-started/installation/`
  → install uv, then open a new terminal.
- `Could not prepare the build directory …: [WinError 5] Access is denied: …`
  → the application from the previous build is still running, or another
  program holds its files. Close it and run the build again.
- A traceback that ends with `HTTPStatusError: Client error '404 Not Found' for url '…/python-…-embed-….zip'`
  → python.org has no Windows embeddable package for this `python_version`:
  security-only releases don't ship one. Choose a release that has one: `init`
  writes the version of the Python that runs PyRetort, which can be such a
  release.
- `uv pip install failed with exit code 2: … (os error 216)` → this computer
  cannot run the embedded Python of the chosen architecture: build `arm64` on
  Windows on ARM.

## Limitations

- **Package mode only.** The project must be installable (it needs a
  `[build-system]` table) and must run with `python -m <package>`. Bundling
  plain scripts without packaging, standalone mode, is planned.
- **No code protection.** The application ships as ordinary Python files in
  `Lib\site-packages`; anyone who has the folder can read your code.
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
