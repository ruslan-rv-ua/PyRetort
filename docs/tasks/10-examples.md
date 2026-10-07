# 10. Приклади

Залежить від: 04. Оцінка: S.

## Мета

У `examples/` лише те, що збирається поточною версією: GUI-приклад Simple RSS і новий консольний hello-cli, обидва з інструкцією.

## Контекст

- `examples/Simple RSS/`: у git — `src/simple_rss/**` (є `__main__.py`), `pyproject.toml` з актуальною `[tool.pyretort]` (python 3.13.9, amd64), `README.md`, `uv.lock`, `.python-version`, `.gitignore` і бінарник `Simple RSS.exe` (123 392 байти — згенерований лаунчер, артефакт, якому не місце в git). Локально є ще `.venv/`, `build/`, `dist/`, `downloads/` — усі вже ігноруються кореневим `.gitignore` (патерни без провідного `/` діють на будь-якому рівні).
- `examples/SystemMonitor/`: у git — `app.py` (плоский скрипт FastAPI + pywebview, без пакета і `__main__.py`), `pyproject.toml` без `[build-system]` і без `[tool.pyretort]`, `pyretort.toml` у старому плоскому форматі, який код більше не читає. У режимі пакета не збирається; це кандидат на standalone-приклад у задачі 12.
- Після задачі 04 `check` вимагає `__main__.py` для режиму пакета.

## Рішення

1. Simple RSS: `git rm "examples/Simple RSS/Simple RSS.exe"`; у `examples/Simple RSS/README.md` додати розділ «Build with PyRetort» з командою `uv run pyretort build -p "examples/Simple RSS/pyproject.toml"` (із кореня репозиторію) і описом результату.
2. SystemMonitor: видалити теку з git повністю (`git rm -r examples/SystemMonitor`). У повідомленні коміту вказати, що її можна відновити для задачі 12 командою `git checkout 3f3e0f4 -- examples/SystemMonitor`.
3. Новий `examples/hello-cli/`: `pyproject.toml` (`name = "hello-cli"`, `uv_build`, `[tool.pyretort]` з `show_console_window = true`, `create_dist_zip_file = true`, `python_version` = актуальний патч 3.13 з https://www.python.org/downloads/windows/ на момент виконання), `src/hello_cli/__init__.py` (друкує привітання, версію Python і аргументи командного рядка), `__main__.py`, короткий `README.md`.
4. `examples/README.md`: список прикладів, що кожен демонструє, команди `check` і `build` для кожного.

## Сіми

Тестів немає. Перевірка — `pyretort check` для кожного прикладу і одна реальна збірка hello-cli.

## Кроки

1. Видалення (пункти 1 і 2) окремим комітом.
2. Створити hello-cli; `uv run pyretort check -p examples/hello-cli/pyproject.toml` → valid; `uv run pyretort build -p examples/hello-cli/pyproject.toml` → `Build complete`; запустити `examples/hello-cli/build/<dist_name>/hello-cli.exe arg1` з іншої теки — друкує привітання й `arg1`. Після перевірки `uv run pyretort cleanup -p examples/hello-cli/pyproject.toml`.
3. `uv run pyretort check -p "examples/Simple RSS/pyproject.toml"` → valid.
4. README-файли. Критерій завершення з [README.md](README.md).

## Критерій завершення

- `git ls-files examples` не містить `.exe` і `SystemMonitor`.
- `examples/hello-cli` зібрано і запущено хоча б раз; обидва приклади проходять `check`.
- Статус → DONE.

## Поза межами

Зміни в коді Simple RSS — ні. Standalone-приклад — задача 12.

## Коміти

- `chore(examples): remove generated exe and stale SystemMonitor example`
- `docs(examples): add hello-cli example and examples index`

## Джерела

- Випуски Python для Windows (актуальний патч 3.13): https://www.python.org/downloads/windows/
