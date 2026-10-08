# 05. Надійна збірка

Залежить від: 04. Оцінка: L.

## Мета

`pyretort build` падає зрозумілим повідомленням замість трейсбека, коли немає `uv` або встановлення не вдалося; іконка береться відносно теки проєкту; надто довга команда лаунчера — помилка, а не мовчазне обрізання; команда друкує прогрес і поважає `--quiet`; `-p` у всіх командах обчислюється під час виклику.

## Контекст

### Теки збірки

`BaseBuilder.__init__` ([`src/pyretort/builder/base_builder.py:15-24`](../../src/pyretort/builder/base_builder.py)) обчислює `download_path`, `build_path`, `dist_path`, `app_path = build/<dist_name>`, `pydist_path = app_path/pydist`, `source_dist_path = app_path/<slug-dash>` і одразу викликає `_create_directories` (26-33): створює `pydist_path` (рядок 30), потім видаляє весь `app_path` разом із ним і створює `app_path` порожнім. `pydist_path` і константа `PYDIST_DIR_DEFAULT` (`src/pyretort/constants.py:10`) більше ніде не використовуються: вбудований Python ставиться в `source_dist_path` (`uv_builder.py:24`). Після збірки `build/<dist_name>/` містить `<slug-dash>.exe` і теку `<slug-dash>/` з Python і site-packages — така розкладка залишається.

### Виклик uv

`uv_builder.py:32-46`: `subprocess.run(["uv", "pip", "install", "--python", str(python_exe), str(project_dir)], capture_output=True, text=True, check=True)`. Якщо `uv` немає в PATH — `FileNotFoundError` із трейсбеком. Якщо встановлення впало — `CalledProcessError` із трейсбеком, а stderr uv (де справжня причина) користувач не бачить, бо він захоплений. `build_command` ([`src/pyretort/cli/commands/build.py:46`](../../src/pyretort/cli/commands/build.py)) винятки з `builder.build()` не ловить.

### Іконка

`uv_builder.py:56` передає в `generate_exe` відносний `config.icon_file_rel_path`; `generate_exe` ([`generate_exe.py:58-60`](../../src/pyretort/builder/exe_generator/generate_exe.py)) робить `Path(icon_file).absolute()` — відносно поточної теки процесу, а не теки проєкту. Із `-p шлях/до/pyproject.toml` з іншої теки іконка не знаходиться, і `add_icon_to_exe` кидає `FileNotFoundError`. Існування файлу відносно проєкту вже перевіряє `from_pyproject_toml` (`types.py:288-298`).

### Довжина команди

Шаблон лаунчера має місце рівно під 259 символів команди (`MAX_CMD_LENGTH`, `generate_exe.py:20`; сигнатура-заповнювач `REPLACE_SIGNATURE`, рядок 21). `generate_exe` (рядки 48-51) довшу команду мовчки обрізає → непрацюючий exe. У команду входить `"{EXE_DIR}\<slug-dash>\python.exe" -m <module>`; `{EXE_DIR}` потрапляє в шаблон як текст і розгортається лаунчером під час запуску, тож ліміт стосується саме шаблонного рядка.

### Вивід команди build

`build.py:28-43` пише через `typer.echo`, а не `echo(ctx, ...)`, тому `--quiet` на `build` не діє; збірка нічого не повідомляє про хід роботи й результат.

### Default для `-p`

У `build.py:14`, `check.py:14`, `init.py:22` default `Path.cwd() / "pyproject.toml"` стоїть у сигнатурі й обчислюється під час імпорту. Задача 01 для `cleanup` зробила обчислення під час виклику; тут робиться так само для решти команд. Задача 02 позначила ці три рядки `# noqa: B008` (ruff справедливо скаржиться на виклик `Path.cwd()` у default); після переходу на `PyprojectOption` коментарі зникають разом із рядками.

### Покриття

`uv_builder.py` 40 %, `base_builder.py` 32 %, `generate_exe.py` 30 % — тестів на збірку майже немає (крім тесту з задачі 04).

## Рішення

1. **Помилки збірки.** Новий модуль `src/pyretort/builder/errors.py` з `class BuildError(Exception)`. Усі передбачувані збої збірки кидають `BuildError` з повідомленням для людини. `build_command` ловить `BuildError`, друкує повідомлення в stderr через `echo` і виходить із кодом 1.
2. **Наявність uv.** На початку `build()`: `shutil.which("uv") is None` → `BuildError("uv was not found in PATH. Install uv: https://docs.astral.sh/uv/getting-started/installation/")`.
3. **Збій uv.** `CalledProcessError` → `BuildError(f"uv pip install failed with exit code {e.returncode}:\n{e.stderr}")`. `capture_output=True` залишається.
4. **Іконка.** `BuildConfig` отримує обчислюване поле `icon_file_abs_path: Path | None` = `project_dir_abs_path / icon_file_rel_path`; `UVBuilder` передає його. `generate_exe` і далі приймає будь-який шлях.
5. **Довжина команди.** `generate_exe` кидає `ValueError(f"Launcher command is {n} characters long; the limit is {MAX_CMD_LENGTH}: {command}")` і файл не створює. `UVBuilder` перетворює це на `BuildError`.
6. **Теки.** `_create_directories` → `prepare_directories()`: `mkdir(parents=True, exist_ok=True)` для downloads/build/dist; якщо `app_path` існує — `shutil.rmtree`; створити `app_path`. `pydist_path` і `PYDIST_DIR_DEFAULT` видалити. Викликати з `build()`, а не з `__init__`, щоб конструювання білдера не чіпало диск.
7. **Прогрес.** `BaseBuilder.__init__(config, log: Callable[[str], None] = lambda _: None)`. `UVBuilder.build()` викликає `log` на етапах: `Preparing build directory <app_path>`, `Installing embedded Python <version> (<arch>)`, `Installing project with uv`, `Generating launcher <exe>`, `Build complete: <app_path>`. `build_command` передає `lambda message: echo(ctx, message)` і замінює всі `typer.echo` на `echo(ctx, ...)`.
8. **`-p`.** Спільний модуль `src/pyretort/cli/_options.py`: тип `PyprojectOption = Annotated[Path | None, typer.Option("--pyproject-toml", "-p", help=...)]` і функція `resolve_pyproject(path: Path | None) -> Path`, яка повертає `(path or Path.cwd() / "pyproject.toml").resolve()`; команда сама перевіряє існування файлу і друкує `Configuration file not found: <path>` з кодом 1. Використати в `init`, `check`, `build` і `cleanup` (із задачі 01).

## Сіми

- `UVBuilder(config, log=...)` → `build()` з підміненими `PydistManager` (`patch("pyretort.builder.uv_builder.PydistManager")`), `subprocess.run`, `generate_exe`, `shutil.which`. Проєкт — тимчасова тека з `pyproject.toml` і пакетом із `__main__.py`, конфігурація через `BuildConfig.from_pyproject_toml`.
- `generate_exe(target, command, ...)` напряму з `tmp_path`: пише справжній файл із шаблону; без іконки `win32api` не викликається.
- CLI `build`, `check`, `init` через `CliRunner` із підміненим `UVBuilder` або `subprocess.run`.

## Кроки

Файли тестів: `tests/test_uv_builder.py` (із задачі 04), новий `tests/test_generate_exe.py`, `tests/cli/test_build.py`.

1. `test_build_fails_clearly_when_uv_is_missing`: `shutil.which` → `None`; `pytest.raises(BuildError, match="uv was not found")`; на диску не створено `build/`. Створити `errors.py`, перевірку, перенести створення тек у `build()`.
2. `test_build_reports_uv_stderr_on_failure`: `subprocess.run` кидає `CalledProcessError(1, cmd, stderr="No solution found")`; `BuildError` містить `exit code 1` і `No solution found`.
3. `test_build_passes_absolute_icon_path_from_project_dir`: конфігурація з `icon_file_rel_path = "assets/app.ico"` (файл створено), CWD в іншій теці; `generate_exe` отримав `icon_file == project_dir / "assets" / "app.ico"`.
4. `test_generate_exe_rejects_command_longer_than_limit`: команда з 300 символів → `ValueError` з `300` і `259`; файл не створено. `test_generate_exe_embeds_command_into_template`: звичайна команда → файл існує, його розмір дорівнює розміру `genexe_template`, байти команди присутні у файлі. `test_build_turns_long_command_into_build_error` — через `UVBuilder`.
5. `test_build_recreates_app_dir_from_scratch`: у `build/<dist_name>/` лежить сторонній файл → після `build()` його немає. `test_builder_init_does_not_touch_filesystem`: після `UVBuilder(config)` без `build()` тек `build/`, `downloads/`, `dist/` немає. Прибрати `pydist_path`, `PYDIST_DIR_DEFAULT`.
6. `test_build_logs_progress_messages`: зібрані повідомлення `log` містять `Installing embedded Python 3.13.9 (amd64)` і `Build complete:`.
7. CLI: `test_build_prints_progress`, `test_build_quiet_prints_nothing` (`-q build -p ...` → порожній вивід), `test_build_reports_build_error_without_traceback` (`UVBuilder.build` кидає `BuildError("boom")` → код 1, `boom` у виводі, `Traceback` відсутній). Переписати `test_build_builder_exception` (`tests/cli/test_build.py:141-172`) на `BuildError`.
8. `-p`: `test_check_defaults_to_pyproject_in_current_directory` з `monkeypatch.chdir`; аналогічно для `build` і `init`. Ввести `_options.py`, перевести чотири команди.
9. Рефакторинг і критерій завершення з [README.md](README.md).

## Критерій завершення

- Усі тести з кроків 1-8 існують і проходять; `uv run pytest` зелений; чотири команди з README зелені.
- `uv run pytest --cov=pyretort.builder --cov-report=term-missing` показує покриття `uv_builder.py` і `base_builder.py` не нижче 90 %.
- `rg "typer.echo" src/pyretort/cli` знаходить лише `_output.py`.
- Ручна перевірка (потрібен інтернет або кеш `downloads/`): `uv run pyretort build -p <тестовий проєкт>` із чужої CWD завершується рядком `Build complete:`, а `uv run pyretort -q build -p ...` мовчить.
- Статус у README → DONE.

## Поза межами

ZIP у `dist/` — задача 06. Наскрізний тест із реальним завантаженням — задача 07.

## Коміти

- `refactor(builder): prepare build directories lazily and drop unused pydist path`
- `feat(builder): fail with BuildError when uv is missing or fails`
- `fix(builder): resolve icon path relative to the project directory`
- `fix(exe): reject launcher commands longer than the template limit`
- `feat(cli): report build progress, honor --quiet, resolve -p at call time`

## Джерела

- `shutil.which`: https://docs.python.org/3/library/shutil.html#shutil.which
- `subprocess.CalledProcessError`: https://docs.python.org/3/library/subprocess.html#subprocess.CalledProcessError
- uv, встановлення: https://docs.astral.sh/uv/getting-started/installation/
- Typer, `Annotated`-опції: https://typer.tiangolo.com/tutorial/options/name/
