# 21. `init` розпізнає standalone-проєкти

Залежить від: 12. Оцінка: S.

## Мета

`pyretort init` для проєкту зі скриптами в корені, як після `uv init`, пише `install_as_package = false` і `main_file`, тож `pyretort check` проходить одразу. Для пакетів поведінка `init` не змінюється.

## Контекст

Функції й тести названо станом на коміт `f6a7b60`.

- `init_command` (`src/pyretort/cli/commands/init.py`):
  - `_find_project_source_subdir` шукає теку `<slug_underscore>` у `.`, `src`, `source`, `app`, `lib` і повертає `.`, якщо не знайшла;
  - `_find_main_file` шукає `main.py`, `app.py`, `run.py` у теці джерел;
  - `install_as_package` завжди дорівнює `INSTALL_AS_PACKAGE_DEFAULT` (`true`);
  - після запису, якщо `launcher_entry_point(...).exists()` хибне, друкується `warning: <…\__main__.py> not found; 'pyretort build' will fail until it exists`.
- Після задачі 12 standalone-режим працює, а `check` для `install_as_package = false` вимагає `main_file`. Коментар над `install_as_package` описує обидва значення вже після задачі 12.
- `uv init <name>` без `--package` створює `main.py` у корені, `pyproject.toml` без `[build-system]`, `README.md` і `.python-version`. Теки пакета немає, тож `_find_project_source_subdir` повертає `.`.
- Правило з першої версії задачі 12 («немає `__main__.py`, але є `main_file` → standalone») відкинуто через пастку. Пакет `src/my_app/` без `__main__.py`, але з `main.py`, отримав би standalone-режим. Якщо цей `main.py` імпортує відносно (`from .database import …`, як `examples/Simple RSS/src/simple_rss/main.py`), зібраний застосунок падає під час запуску: `ImportError: attempted relative import with no known parent package`.
- Пастка для тесту «`init` → `check`»: `init` пише в `python_version` версію Python, на якому біжать тести. Локально і в CI це 3.13, але PyRetort підтримує 3.11+, а `check` після задачі 12 звіряє `python_version` з `requires-python`. Тому тестовий проєкт має `requires-python = ">=3.11"`.

## Рішення

1. `init` пише `install_as_package = false`, коли виконуються всі три умови:
   - `_find_project_source_subdir` повернув `.`;
   - `launcher_entry_point(project_dir, Path("."), name).exists()` хибне, тобто немає ні `<slug>/__main__.py`, ні `<slug>.py`;
   - `_find_main_file` знайшов файл.

   Інакше `init` пише `true`, як і зараз.

   | Що знайшов `init` | `install_as_package` |
   |---|---|
   | `main.py` у корені, як після `uv init` | `false` |
   | `src/my_app/__main__.py` | `true` |
   | `src/my_app/main.py` без `__main__.py` | `true` + попередження про `__main__.py` |
   | `my_app.py` у корені | `true` |
   | нічого з переліченого | `true` + попередження |
2. У standalone-випадку попередження про `__main__.py` не друкується. Натомість через `echo` друкується `Standalone mode: no package found, the launcher will run <main_file> as a script`, тож `--quiet` його приглушує.
3. `_find_main_file` шукає `main.py`, `app.py`, `cli.py`, `run.py` у такому порядку.
4. README проєкту:
   - у таблиці Commands рядок `pyretort init` каже, що `init` обирає standalone-режим для скриптів у корені проєкту;
   - підрозділ `### Standalone mode` описує правило з рішення 1.

   CHANGELOG `[Unreleased]`: рядок в `### Added`.

## Сіми

- CLI `init` через `CliRunner`. Результат перевіряється за вмістом `pyproject.toml` (через `tomllib`) і за stdout.
- Наскрізна перевірка «`init` → `check`» — теж через `CliRunner`.

## Кроки

Тести — у новому класі `TestInitCommandBuildMode` у `tests/cli/test_init.py`, по зрізу на тест.

1. `test_init_prefers_standalone_for_scripts_in_project_root`: `main.py` у корені, пакета немає → `install_as_package is False`, `main_file == "main.py"`, `project_source_subdir == "."`.
2. `test_init_does_not_warn_about_dunder_main_in_standalone_mode`: у stdout немає `warning`, але є рядок із рішення 2.
3. `test_init_keeps_package_mode_for_package_without_dunder_main`: `src/my_app/__init__.py` і `src/my_app/main.py` без `__main__.py` → `true` і попередження.
4. `test_init_keeps_package_mode_for_single_module_in_root`: проєкт `my-app`, у корені `my_app.py` і `main.py` → `true`.
5. `test_init_finds_cli_py_as_main_file`: у корені лише `cli.py` → `main_file == "cli.py"` і `false`.
6. `test_init_output_passes_check_for_uv_init_project`: розкладка як після `uv init` (`main.py`, `README.md`, `.python-version`, `pyproject.toml` без `[build-system]` з `requires-python = ">=3.11"`), потім `init` і `check` → обидва з кодом 0.
7. Наявні тести `init` лишаються зеленими без змін. `test_init_finds_main_file` і `test_init_finds_app_py` тепер отримують і `install_as_package = false`, але цього не перевіряють.
8. README і CHANGELOG (рішення 4).
9. Ручна перевірка, один раз: `uv init` у тимчасовій теці → `uv run --project C:\dev\PyRetort pyretort init`, потім `check` і `build` → згенерований exe друкує `Hello from …!`. Для консольного виводу перед `build` встановити `show_console_window = true`.
10. Критерій завершення.

## Критерій завершення

- Тести з кроків 1–6 проходять; ручна перевірка з кроку 9 вдалася.
- Чотири команди з [README.md](README.md) зелені.
- Статус задачі в [README.md](README.md) → DONE.

## Поза межами

- Вибір режиму за наявністю `[build-system]`: на рішення 1 він не впливає, тож проєкт зі скриптами в корені і з build-backend теж отримує standalone-режим.
- Нові кандидати на `main_file`, крім `cli.py`.

## Коміти

- `feat(init): detect standalone projects`
- `docs: describe how init picks the build mode`

## Джерела

- uv, `uv init` для застосунків: https://docs.astral.sh/uv/concepts/projects/init/
