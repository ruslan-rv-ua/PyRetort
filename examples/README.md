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

Result: `examples/hello-cli/build/hello-cli-0.1.0-amd64/hello-cli.exe`.

## Simple RSS

A wxPython RSS reader. It shows a GUI application without a console window
(`show_console_window = false`) and third-party dependencies (wxPython, httpx,
peewee, fastfeedparser) installed into the embedded Python. See
[Simple RSS/README.md](Simple%20RSS/README.md#build-with-pyretort).

```powershell
uv run pyretort check -p "examples/Simple RSS/pyproject.toml"
uv run pyretort build -p "examples/Simple RSS/pyproject.toml"
```

Result: `examples/Simple RSS/build/simple-rss-0.1.0-amd64/simple-rss.exe`.

## Clean up

`uv run pyretort cleanup -p <path to pyproject.toml>` removes the example's
`build/`, `dist/` and `downloads/`.
