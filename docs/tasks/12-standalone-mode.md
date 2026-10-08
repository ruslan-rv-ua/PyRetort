# 12. Standalone-режим (після 0.1)

Залежить від: 11. Оцінка: L.

## Мета

`install_as_package = false` збирає проєкт без пакування: джерела копіюються як є, залежності з `pyproject.toml` ставляться у вбудований Python, лаунчер запускає `main_file` як скрипт. Для проєктів без `__init__.py`/`__main__.py` і без build-backend.

## Контекст

- Зараз `UVBuilder._build_as_standalone` кидає `NotImplementedError` (`src/pyretort/builder/uv_builder.py:18-20`), а задача 04 змусила `from_pyproject_toml` відхиляти `install_as_package = false` повідомленням «not supported yet».
- У моделі вже є все потрібне: `main_file_rel_path` з перевіркою існування відносно `project_source_subdir` (`types.py:276-286`; після задачі 14 перевірка діє саме для `install_as_package = false`), `DEFAULT_BLACKLIST` зі шаблонами виключення (`constants.py:27`), `PydistManager.patch_pth_file(version, relative_path_to_source)` (`pydist_manager.py:33-46`), який уміє додати теку в `._pth`.
- Embedded Python: `._pth` перелічує теки для `sys.path` і вмикає `site` рядком `import site`; документація Python прямо каже, що сторонні пакети для embeddable distribution треба постачати разом із застосунком. Для скрипта, запущеного як `python.exe шлях\main.py`, Python сам додає теку скрипта в `sys.path[0]`.
- Встановлення лише залежностей без самого проєкту: `uv pip install --python <embedded python.exe> -r pyproject.toml` — uv читає `[project].dependencies` з `pyproject.toml` як файл вимог (документація uv «Installing packages»; uv 0.12: `-r, --requirements <REQUIREMENTS>  Install the packages listed in the given files`). Перевірити на практиці першим кроком задачі: тимчасовий проєкт з однією залежністю й без `[build-system]`, виконати команду і переконатися, що в site-packages з'явилася залежність, а проєкт — ні.
- Розкладка режиму пакета після 0.1: `build/<dist_name>/<slug-dash>.exe` і `build/<dist_name>/<slug-dash>/` (Python + site-packages).
- Лаунчер — власний, із задачі 15: запускає команду без `cmd.exe` і допускає кілька токенів у лапках. Зі старим шаблоном gen-exe команда з рішення 6 (два шляхи в лапках) не стартувала.
- Приклад для режиму: `examples/SystemMonitor` (видалений у задачі 10; відновлюється командою `git checkout 3f3e0f4 -- examples/SystemMonitor`): `app.py` у корені, залежності в `pyproject.toml`, без пакета.

## Рішення

1. **Розкладка.** `build/<dist_name>/<slug-dash>.exe`; `build/<dist_name>/<slug-dash>/` — embedded Python і залежності (як у режимі пакета); `build/<dist_name>/app/` — копія `project_source_subdir`.
2. **Копіювання.** `shutil.copytree(src=project_dir / subdir, dst=app_path / "app", ignore=shutil.ignore_patterns(*DEFAULT_BLACKLIST))`. Якщо subdir = `.`, копіюється весь корінь проєкту крім шаблонів зі списку; переконатися, що `downloads` і `uv.lock` є в `DEFAULT_BLACKLIST`, інакше додати.
3. **Залежності.** `uv pip install --python <embedded> -r <project_dir>/pyproject.toml`. Проєкт без `[project].dependencies` → крок пропускається з повідомленням у `log`. `[build-system]` для standalone не потрібен: прибрати цю вимогу з `from_pyproject_toml` для цього режиму.
4. **Валідація** у `from_pyproject_toml` для `install_as_package = false`: `main_file` обов'язковий; `__main__.py` не потрібен; повідомлення «not supported yet» видалити.
5. **`._pth`:** як у режимі пакета (`python3XX.zip`, `.`, `import site`); тека `app` не додається, бо скрипт запускається напряму.
6. **Лаунчер:** `"{EXE_DIR}\<slug-dash>\python.exe" "{EXE_DIR}\app\<main_file>"`. Ліміт довжини — 1023 одиниці UTF-16 (задача 15).
7. **`init`:** коментар до `install_as_package` стає `true: install the project as a package and run python -m <module>; false: copy sources and run main_file as a script`; якщо `__main__.py` не знайдено, а `main_file` знайдено — `init` записує `install_as_package = false`.
8. **e2e:** другий сценарій у `tests/test_e2e_build.py` — скрипт `main.py` без пакета з однією маленькою залежністю з PyPI (наприклад `six`), який імпортує її й пише маркер.

## Сіми

- `BuildConfig.from_pyproject_toml` (валідація режиму).
- `UVBuilder.build()` з підмінами `PydistManager`, `subprocess.run`, `generate_exe`; справжній `copytree` у `tmp_path`.
- CLI `init`, `check`, `build` через `CliRunner`; e2e як у задачі 07.

## Кроки

1. Експеримент з `-r pyproject.toml` (див. контекст); результат зафіксувати коментарем біля виклику в коді.
2. `test_from_pyproject_requires_main_file_in_standalone_mode`, `test_from_pyproject_allows_missing_build_system_in_standalone_mode`, `test_from_pyproject_accepts_standalone_mode` (замість тесту на «not supported yet» із задачі 04).
3. `test_standalone_build_copies_sources_without_blacklisted_files` (у джерелах є `__pycache__/x.pyc` і `.venv/` — у `app/` їх немає, а `main.py` є).
4. `test_standalone_build_installs_only_dependencies` (`subprocess.run` отримав `-r <pyproject>` і не отримав шлях проєкту як пакет).
5. `test_standalone_build_skips_uv_when_no_dependencies`.
6. `test_standalone_launcher_runs_main_file_as_script` (команда в `generate_exe` закінчується на `\app\main.py"`).
7. `init`: `test_init_prefers_standalone_when_main_file_exists_without_dunder_main`.
8. e2e-тест; відновити `examples/SystemMonitor`, додати `[tool.pyretort]`, видалити `pyretort.toml`, зібрати, запустити.
9. README: розділи Limitations і Configuration; CHANGELOG `[Unreleased]`.

## Критерій завершення

- Тести з кроків 2-7 проходять; `uv run pytest -m e2e` → усі сценарії зелені; чотири команди з [README.md](README.md) зелені.
- `examples/SystemMonitor` збирається і запускається.
- README не містить «standalone mode is not supported».
- Статус → DONE.

## Коміти

- `feat(builder): implement standalone build mode`
- `feat(init): detect standalone projects`
- `test: add standalone end-to-end scenario`
- `docs: document standalone mode`

## Джерела

- uv, встановлення з `pyproject.toml`: https://docs.astral.sh/uv/pip/packages/
- Python embeddable package: https://docs.python.org/3/using/windows.html#the-embeddable-package
- `shutil.copytree`, `ignore_patterns`: https://docs.python.org/3/library/shutil.html#shutil.copytree
- Python, `sys.path` для скрипта: https://docs.python.org/3/library/sys.html#sys.path
