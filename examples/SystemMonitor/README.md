# SystemMonitor

A GUI application packaged with PyRetort in standalone mode. It shows the CPU
and memory usage of the computer and refreshes the numbers every few seconds.
A FastAPI server with uvicorn runs in a background thread on `127.0.0.1:9999`,
the page is written with htpy and Bootstrap, the numbers arrive as server-sent
events through datastar, and pywebview shows the page in a full-screen window.

The example shows what a GUI script with heavy dependencies needs:

- `install_as_package = false` and `main_file = "app.py"` in `[tool.pyretort]`:
  the project is one file, `app.py`, without a package or a `[build-system]`
  table; the build copies it and the launcher runs it as a script.
- `show_console_window = false`: the launcher starts the application without a
  console window, as Simple RSS does.
- Six dependencies in `[project]`, among them pywebview with pythonnet, pinned
  with `==` to the versions the example was tested with. The build installs
  them into the embedded Python with `uv pip install -r pyproject.toml`; without
  a lock file it would otherwise take the newest versions.
- The datastar bundle comes from the CDN at a fixed release tag (`@v1.0.4`),
  so the page stays compatible with the pinned `datastar-py`.

## Build with PyRetort

From the repository root:

```powershell
uv run pyretort check -p examples/SystemMonitor/pyproject.toml
uv run pyretort build -p examples/SystemMonitor/pyproject.toml
```

The first build downloads the embeddable Python 3.13.16 package from
python.org into `examples/SystemMonitor/downloads/`; later builds reuse it. The
result is `examples/SystemMonitor/build/system-monitor-0.1.0-amd64/`:

- `system-monitor.exe`, the launcher: it runs `system-monitor\app\app.py` with
  the embedded Python, without a console window;
- `system-monitor/`, the embedded Python with the dependencies installed and
  the copy of the project in `app/`: `app.py`, `pyproject.toml` and this
  README.

The folder is self-contained: copy it to another Windows PC and
`system-monitor.exe` runs there without an installed Python. pywebview needs
the Microsoft Edge WebView2 Runtime, which Windows 11 includes and Windows
Update installs on Windows 10.

`create_dist_zip_file = true` makes the build also pack the folder into
`examples/SystemMonitor/dist/system-monitor-0.1.0-amd64.zip`, ready to share.
The archive unpacks into a single `system-monitor-0.1.0-amd64/` folder with
`system-monitor.exe` inside.

## Run

```powershell
examples\SystemMonitor\build\system-monitor-0.1.0-amd64\system-monitor.exe
```

A full-screen window opens with two cards, CPU Usage and Memory Usage; the
percentages refresh every few seconds. Close the window with Alt+F4.

The application needs:

- an internet connection: the page loads Bootstrap and the datastar bundle
  from cdn.jsdelivr.net;
- a free TCP port 9999 on `127.0.0.1`: the server listens there and the window
  opens that address.

There is no console window, so an error at start-up is silent. To see it, set
`show_console_window = true` in `[tool.pyretort]`, build again and start the
launcher from a terminal.

## Clean up

Remove `build/`, `dist/` and `downloads/`:

```powershell
uv run pyretort cleanup -p examples/SystemMonitor/pyproject.toml
```
