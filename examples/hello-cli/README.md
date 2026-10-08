# hello-cli

A minimal console application packaged with PyRetort. It prints a greeting, the
Python version it runs on and its command-line arguments.

The example shows what a command-line program needs:

- `show_console_window = true` in `[tool.pyretort]`: the program runs with a
  console window, so its output is visible. GUI programs such as Simple RSS
  use `false`.
- Arguments given to `hello-cli.exe` reach the program in `sys.argv` exactly
  as typed: the launcher starts the bundled Python directly, without
  `cmd.exe`, so `"two words"` stays one argument and characters such as `&`,
  `|`, `>`, `^` and `%` are not interpreted.

## Build with PyRetort

From the repository root:

```powershell
uv run pyretort check -p examples/hello-cli/pyproject.toml
uv run pyretort build -p examples/hello-cli/pyproject.toml
```

The first build downloads the embeddable Python 3.13.16 package from
python.org into `examples/hello-cli/downloads/`; later builds reuse it. The
result is `examples/hello-cli/build/hello-cli-0.1.0-amd64/`:

- `hello-cli.exe`, the launcher: it runs `python -m hello_cli` with the
  bundled Python;
- `hello-cli/`, the embedded Python with the `hello_cli` package installed.

The folder is self-contained: copy it to another Windows PC and
`hello-cli.exe` runs there without an installed Python.

`create_dist_zip_file = true` asks PyRetort to pack this folder into a ZIP
archive in `examples/hello-cli/dist/`; the current version does not create the
archive yet.

## Run

Start the launcher from a terminal; when double-clicked, its console window
closes as soon as the program ends.

```powershell
examples\hello-cli\build\hello-cli-0.1.0-amd64\hello-cli.exe arg1 "two words"
```

```text
Hello from hello-cli!
Python 3.13.16 at C:\...\examples\hello-cli\build\hello-cli-0.1.0-amd64\hello-cli\python.exe
Arguments: ['arg1', 'two words']
```

## Clean up

Remove `build/`, `dist/` and `downloads/`:

```powershell
uv run pyretort cleanup -p examples/hello-cli/pyproject.toml
```
