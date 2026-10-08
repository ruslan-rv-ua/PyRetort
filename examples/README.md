# Examples

Projects that the current PyRetort builds. Each keeps its build settings in the
`[tool.pyretort]` section of its `pyproject.toml`. Run the commands below from
the repository root; a build needs `uv` in `PATH` and downloads the embeddable
Python from python.org on the first run.

## hello-cli

A console program that prints a greeting, the Python version and its
command-line arguments. It shows the smallest package-mode project (a `src/`
layout with `__main__.py`, no dependencies) and a console application:
`show_console_window = true`, arguments passed through the launcher. See
[hello-cli/README.md](hello-cli/README.md).

```powershell
uv run pyretort check -p examples/hello-cli/pyproject.toml
uv run pyretort build -p examples/hello-cli/pyproject.toml
```

## hello-script

A console script that prints a greeting and a table with the Python version,
the script path and its command-line arguments. It shows the smallest
standalone-mode project (`main.py` and `helper.py` in the project root, no
package, no `[build-system]`, the layout `uv init --no-package` creates) with
one dependency, rich, installed into the embedded Python:
`install_as_package = false`, `main_file = "main.py"`. See
[hello-script/README.md](hello-script/README.md).

```powershell
uv run pyretort check -p examples/hello-script/pyproject.toml
uv run pyretort build -p examples/hello-script/pyproject.toml
```

## SystemMonitor

A GUI application that shows the CPU and memory usage in a full-screen
pywebview window: a FastAPI server with uvicorn runs in a background thread
and datastar refreshes the page over server-sent events. It shows a
standalone-mode project with heavy dependencies (`install_as_package = false`,
`main_file = "app.py"`, six dependencies pinned with `==`) and no console
window (`show_console_window = false`). The application needs an internet
connection and a free port 9999. See
[SystemMonitor/README.md](SystemMonitor/README.md).

```powershell
uv run pyretort check -p examples/SystemMonitor/pyproject.toml
uv run pyretort build -p examples/SystemMonitor/pyproject.toml
```

## Simple RSS

A wxPython RSS reader. It shows a GUI application without a console window
(`show_console_window = false`) and third-party dependencies (wxPython, httpx,
peewee, fastfeedparser) installed into the embedded Python. See
[Simple RSS/README.md](Simple%20RSS/README.md#build-with-pyretort).

```powershell
uv run pyretort check -p "examples/Simple RSS/pyproject.toml"
uv run pyretort build -p "examples/Simple RSS/pyproject.toml"
```
