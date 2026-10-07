# 07. Наскрізний тест збірки

Залежить від: 06. Оцінка: M.

## Мета

Один повільний тест збирає крихітний проєкт справжнім `pyretort build`, запускає згенерований exe з чужої теки і перевіряє, що застосунок виконався вбудованим Python. Він ловить поломки, яких мок-тести не бачать: формат `._pth`, встановлення через uv у embedded Python, шаблон лаунчера.

## Контекст

Такий сценарій уже перевірявся вручну 7 жовтня 2026 на коміті `64b8b21`: проєкт `hello-app` (`uv_build`, пакет `src/hello_app` з `__init__.py` і `__main__.py`), `pyretort init` → `check` → `build` → `build/hello-app-0.1.0-amd64/hello-app.exe`. Запуск exe з `C:\` завершився з кодом 0 і записав файл-маркер із `sys.version` = 3.13.9 і шляхом до `hello-app\python.exe`. Повторна збірка в тій самій теці теж пройшла.

Факти для тесту:

- Архів embedded Python: `https://www.python.org/ftp/python/3.13.9/python-3.13.9-embed-amd64.zip`, 10,9 МБ (`PydistManager._download_embedded_python`, `src/pyretort/builder/pydist_manager.py:48-53`). `Downloader` кешує в `<project>/downloads/` і не завантажує повторно, якщо файл уже там (`downloader.py:45-47`).
- `uv pip install` під час тесту теж ходить у мережу за backend `uv_build`, якщо його немає в кеші uv.
- Маркери з `pyproject.toml`: `slow`, `e2e`, `integration`, `windows`, `requires_network`; за замовчуванням `addopts = "-m 'not slow'"`. Повільні тести запускаються `uv run pytest -m slow` (AGENTS.md).
- Лаунчер із `show_console_window = false` запускає Python приховано; stdout недоступний, тому результат перевіряється файлом-маркером. `subprocess.run` на exe повертається після завершення застосунку (перевірено).
- Після задачі 06 збірка створює `dist/<dist_name>.zip`.

## Рішення

1. Файл `tests/test_e2e_build.py`, клас `TestEndToEndBuild`, маркери `slow`, `e2e`, `requires_network`, `windows`.
2. Фікстура `hello_project(tmp_path)` створює:
   - `pyproject.toml`: `name = "hello-app"`, `version = "0.1.0"`, `requires-python = ">=3.13"`, `dependencies = []`, `[build-system] requires = ["uv_build>=0.9.4,<0.10.0"]`, `build-backend = "uv_build"`, `[tool.pyretort]`: `project_source_subdir = "src/hello_app"`, `install_as_package = true`, `python_version = "3.13.9"`, `python_architecture = "amd64"`, `show_console_window = false`, `create_dist_zip_file = true`;
   - `src/hello_app/__init__.py` з `main()`, яка пише `Path(sys.executable).resolve().parent.parent / "e2e_marker.txt"` з текстом `sys.version`;
   - `src/hello_app/__main__.py`: `from hello_app import main; main()`.
3. Кеш завантаження: якщо встановлено змінну середовища `PYRETORT_E2E_DOWNLOAD_DIR` і там є `python-3.13.9-embed-amd64.zip`, фікстура копіює його в `<project>/downloads/` перед збіркою. Без змінної — звичайне завантаження.
4. Тест `test_build_produces_runnable_launcher`:
   - `CliRunner().invoke(app, ["build", "-p", str(pyproject)])` → код 0, у виводі `Build complete`;
   - `build/hello-app-0.1.0-amd64/hello-app.exe` і `hello-app/python.exe` існують;
   - `subprocess.run([str(exe)], cwd=tmp_path / "elsewhere", timeout=120)` → код 0;
   - `build/hello-app-0.1.0-amd64/e2e_marker.txt` існує і містить `3.13.9`;
   - `dist/hello-app-0.1.0-amd64.zip` існує.
5. Тест `test_second_build_in_same_project_succeeds`: повторний `build` → код 0, маркер від попереднього запуску зник (тека перестворюється).
6. AGENTS.md, розділ про запуск тестів: додати рядок про `uv run pytest -m e2e` і змінну `PYRETORT_E2E_DOWNLOAD_DIR`.

## Сіми

Тільки CLI `build` через `CliRunner` плюс запуск згенерованого exe через `subprocess.run`.

## Кроки

Для наскрізного тесту «червоний» етап окремо не влаштовується: тест пишеться одразу повністю і запускається `uv run pytest -m e2e -v`. Якщо він падає — лагодиться код, а тест змінюється лише при помилці в самому тесті.

1. Написати фікстуру й перший тест, запустити з увімкненим кешем: `$env:PYRETORT_E2E_DOWNLOAD_DIR = "<тека з уже завантаженим zip>"` (архів є в `examples\Simple RSS\downloads\`, якщо тека не видалена).
2. Другий тест.
3. Один запуск без змінної середовища (справжнє завантаження).
4. Оновити AGENTS.md. Критерій завершення з [README.md](README.md).

## Критерій завершення

- `uv run pytest -m e2e` → 2 passed (з інтернетом).
- `uv run pytest` (швидкі) не запускає e2e-тести і залишається зеленим; чотири команди з README зелені.
- У AGENTS.md згадано `-m e2e` і `PYRETORT_E2E_DOWNLOAD_DIR`.
- Статус у README → DONE.

## Поза межами

Тест для standalone-режиму — задача 12. Тест з іконкою — потребує `.ico` у репозиторії; окремо пізніше.

## Коміти

- `test: add end-to-end build test with a real embedded python`
- `docs(agents): document the e2e test run`

## Джерела

- Python embeddable package і `._pth`: https://docs.python.org/3/using/windows.html#the-embeddable-package
- uv, `uv pip install --python`: https://docs.astral.sh/uv/pip/environments/
- pytest, маркери: https://docs.pytest.org/en/stable/how-to/mark.html
