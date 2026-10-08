# 14. `main_file` у режимі пакета: `init` → `check` без ручних правок

Залежить від: 04. Оцінка: S.

## Мета

Свіжий `pyretort init` для звичайного пакета (`src/<pkg>/` з `__main__.py`, без `main.py`) дає конфігурацію, яку `check` і `build` приймають одразу. Поле `main_file` у режимі пакета справді ігнорується, як і обіцяє коментар, який пише `init`.

## Контекст

Номери рядків — станом на коміт `362b089` (кінець задачі 05; задача 10 код не змінювала).

- Знайдено 8 жовтня 2026 під час задачі 10. Для `examples/hello-cli` (`uv_build`, `src/hello_cli/__init__.py` і `__main__.py`, без `main.py`) команда `uv run pyretort init -p examples/hello-cli/pyproject.toml` записала:

  ```toml
  # Name of the main Python file to execute (e.g., main.py, app.py)
  # Used only when install_as_package = false; ignored otherwise
  # TODO: Update this to point to your main application file
  main_file = "main.py"
  ```

  Після цього `uv run pyretort check -p examples/hello-cli/pyproject.toml` завершився з кодом 1: `Configuration validation failed: Main file does not exist: C:\dev\PyRetort\examples\hello-cli\src\hello_cli\main.py`. `build` падає так само (`Invalid configuration: ...`). У прикладі `main_file` довелося прибрати вручну.
- `init`: `_build_pyretort_section` (`src/pyretort/cli/commands/init.py:112-127`) шукає `main.py`, `app.py`, `run.py` у теці джерел (`_find_main_file`, 175-182). Якщо нічого не знайдено, функція пише рядок `TODO` і `main_file = "main.py"`.
- `check` і `build`: `BuildConfig.from_pyproject_toml` (`src/pyretort/types.py:305-315`) перевіряє, що `main_file` існує відносно `project_source_subdir`, щойно ключ є, незалежно від `install_as_package`. Перевірка стоїть до розбору `install_as_package` (337-347), де `false` відхиляється повідомленням «not supported yet».
- Тест `test_main_file_does_not_exist` (`tests/test_types.py:880-910`) закріплює цю поведінку саме для `install_as_package = True`. Тест `test_init_then_check` (`tests/test_integration.py:92-115`) обходить баг: створює `main.py` з коментарем «Create main.py file that init command will find».
- Тести `init` про `main_file`: `test_init_finds_main_file` (`tests/cli/test_init.py:105-123`), `test_init_finds_app_py` (402-420), `test_init_comments_explain_install_as_package_and_main_file` (336-355).
- Задача 12 (standalone) робить `main_file` обов'язковим для `install_as_package = false` і спирається на наявну перевірку існування ([12-standalone-mode.md](12-standalone-mode.md), контекст і рішення 4). Задача 09 описує `main_file` як поле, що ігнорується в режимі пакета.

## Рішення

1. **Перевірка.** `from_pyproject_toml` перевіряє існування `main_file` лише для `tool_pyretort.get("install_as_package") is False`. Блок лишається на своєму місці, до розбору `install_as_package`, тож для standalone-конфігурації він досяжний і покритий тестом до задачі 12. У режимі пакета (`true` або ключа немає) існування файлу не перевіряється. Перевірка, що шлях відносний (`Main file must be relative`), лишається для обох режимів: це помилка формату, а не відсутній файл. `main_file_rel_path` зберігає значення, як і раніше.
2. **`init`.** Якщо `_find_main_file` нічого не знайшов, ключ `main_file` не пишеться. Під двома поясненнями лишається закоментований приклад `# main_file = "main.py"`, а рядок `TODO` зникає. Якщо файл знайдено, поведінка як зараз: `main_file = "<знайдене ім'я>"`.
3. Тексти повідомлень `check` і `build` не змінюються.

## Сіми

- `BuildConfig.from_pyproject_toml` з `tmp_path`, як у `tests/test_types.py`.
- CLI `init` і `check` через `CliRunner`, як у `tests/cli/test_init.py` і `tests/test_integration.py`.

## Кроки

Кожен крок: тест → червоний → мінімальна зміна → `uv run pytest -q <файл тесту>` зелений → далі.

1. `test_main_file_is_not_checked_in_package_mode` (`tests/test_types.py`):
   - умова: `install_as_package = True`, `main_file = "nonexistent.py"`, `project_source_subdir = "src"`, файл `src/__main__.py` існує;
   - очікування: винятку немає, `config.main_file_rel_path == Path("nonexistent.py")`;
   - зараз падає з `Main file does not exist`;
   - зміна: рішення 1;
   - `test_main_file_does_not_exist` перейменувати на `test_main_file_does_not_exist_in_standalone_mode`, у його даних `install_as_package = False`, очікування те саме (`Main file does not exist`).
2. `test_init_leaves_main_file_commented_out_when_none_found` (`tests/cli/test_init.py`):
   - умова: проєкт без `main.py`, `app.py`, `run.py`;
   - очікування: `"main_file" not in pyretort_config`, у тексті файлу є `# main_file = "main.py"`, немає `TODO`;
   - зараз падає, бо ключ записано;
   - зміна: рішення 2.
3. `test_init_then_check_without_main_file` (`tests/test_integration.py`, клас `TestCLIWorkflow`):
   - умова: `src/workflow_test/__init__.py` і `__main__.py`, без `main.py`;
   - кроки: `init -p` → код 0; `check -p` → код 0 і `valid` у виводі;
   - після кроків 1-2 тест пройде одразу. Переконайся, що він червоніє, якщо тимчасово повернути обидві зміни, потім поверни їх.
4. Ручна перевірка:
   - скопіювати `examples/hello-cli` у тимчасову теку й видалити з копії секцію `[tool.pyretort]`;
   - `uv run pyretort init -p <копія>\pyproject.toml`, потім `uv run pyretort check -p <копія>\pyproject.toml` → `is valid`.
5. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Три тести з кроків 1-3 існують під цими назвами й проходять, `test_main_file_does_not_exist_in_standalone_mode` теж. Чотири команди з [README.md](README.md) зелені.
- Ручна перевірка з кроку 4 дає `is valid`.
- Статус у [README.md](README.md) → DONE.

## Поза межами

- Standalone-режим і обов'язковість `main_file` для нього — задача 12.
- Пошук main-файлів за іншими іменами — ні.
- Зміна `[tool.pyretort]` у прикладах — ні: `examples/hello-cli` уже без `main_file`, у Simple RSS `main.py` існує.

## Коміти

- `fix(config): ignore main_file in package mode`
- `fix(init): leave main_file commented out when no main file is found`

## Джерела

- tomlkit, коментарі в таблицях: https://tomlkit.readthedocs.io/en/latest/quickstart/
