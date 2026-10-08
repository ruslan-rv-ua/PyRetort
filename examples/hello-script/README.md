# hello-script

A minimal console script packaged with PyRetort in standalone mode. The
project has no package and no `[build-system]`, the layout `uv init` creates:
`main.py` and `helper.py` in the project root. The script prints a greeting
that it imports from `helper.py` and a table with the Python version, the path
of the script and its command-line arguments.

The example shows what a script project needs:

- `install_as_package = false` and `main_file = "main.py"` in
  `[tool.pyretort]`: the build copies the project folder instead of installing
  it, and the launcher runs `main.py` as a script.
- `helper.py` next to `main.py` is importable in the built application: the
  build lists the script's folder in the `._pth` file of the embedded Python,
  which otherwise keeps it off `sys.path`.
- `dependencies = ["rich>=15.0.0"]` in `[project]`: the build installs the
  dependencies into the embedded Python with `uv pip install -r pyproject.toml`.
- `show_console_window = true`, as in hello-cli: the program runs with a
  console window, so its output is visible.

## Build with PyRetort

From the repository root:

```powershell
uv run pyretort check -p examples/hello-script/pyproject.toml
uv run pyretort build -p examples/hello-script/pyproject.toml
```

The first build downloads the embeddable Python 3.13.16 package from
python.org into `examples/hello-script/downloads/`; later builds reuse it. The
result is `examples/hello-script/build/hello-script-0.1.0-amd64/`:

- `hello-script.exe`, the launcher: it runs `hello-script\app\main.py` with
  `hello-script\python.exe`;
- `hello-script/`, the embedded Python with rich installed and the copy of the
  project in `app/`: `main.py`, `helper.py`, `pyproject.toml` and this README,
  without `build/`, `dist/`, `downloads/` and other development files.

The folder is self-contained: copy it to another Windows PC and
`hello-script.exe` runs there without an installed Python.

`create_dist_zip_file = true` makes the build also pack the folder into
`examples/hello-script/dist/hello-script-0.1.0-amd64.zip`, ready to share. The
archive unpacks into a single `hello-script-0.1.0-amd64/` folder with
`hello-script.exe` inside.

## Run

Start the launcher from a terminal; when double-clicked, its console window
closes as soon as the program ends.

```powershell
examples\hello-script\build\hello-script-0.1.0-amd64\hello-script.exe arg1 "two words"
```

```text
Hello from hello-script!
┌───────────┬──────────────────────────────────────────────────────────────────────────────────────┐
│ Python    │ 3.13.16                                                                              │
│ Script    │ C:\...\examples\hello-script\build\hello-script-0.1.0-amd64\hello-script\app\main.py │
│ Arguments │ ['arg1', 'two words']                                                                │
└───────────┴──────────────────────────────────────────────────────────────────────────────────────┘
```

The script runs from the copy in `app/`, so files it ships with, such as
`helper.py`, lie next to `__file__`: open them through `Path(__file__).parent`.
The working directory stays the one the launcher was started from, so relative
paths typed on the command line work as usual.

## Clean up

Remove `build/`, `dist/` and `downloads/`:

```powershell
uv run pyretort cleanup -p examples/hello-script/pyproject.toml
```
