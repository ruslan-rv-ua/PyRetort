# 14. Необов'язкові поля `[tool.pyretort]`: `init` → `check` без ручних правок

Залежить від: 04. Оцінка: S.

## Мета

Конфігурація, яку щойно записав `pyretort init` для звичайного пакета (`src/<pkg>/` з `__main__.py`, без `main.py`), проходить `check` і `build` без ручних правок. Поля, які код і документація називають необов'язковими, справді необов'язкові:

- `main_file` у режимі пакета ігнорується, як і обіцяє коментар, що його пише `init`;
- без ключів `install_as_package` і `show_console_window` діють типові значення `true` і `false`.

## Контекст

Номери рядків — станом на коміт `362b089` (кінець задачі 05; задача 10 код не змінювала).

### `main_file`

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

### `install_as_package` і `show_console_window`

- Модель має типові значення: `install_as_package: bool = True` (`src/pyretort/types.py:82`) і `show_console_window: bool = False` (рядок 100). Ті самі значення лежать у `SHOW_CONSOLE_DEFAULT` і `INSTALL_AS_PACKAGE_DEFAULT` (`src/pyretort/constants.py:4` і `7`), які пише `init`. Тести `test_install_as_package_default` (`tests/test_types.py:254-267`) і `test_show_console_window_default` (з рядка 269) перевіряють їх лише для прямого створення `BuildConfig`.
- `from_pyproject_toml` читає обидва ключі через `tool_pyretort.get(...)` (рядки 338 і 349) і кладе результат у `config_data` (373-387). Коли ключа немає, туди потрапляє `None`, а pydantic не приймає `None` для `bool`. Перевірено 8 жовтня 2026: `check` для конфігурації без `install_as_package` завершується з кодом 1:

  ```
  Configuration validation failed: 1 validation error for BuildConfig
  install_as_package
    Input should be a valid boolean [type=bool_type, input_value=None, input_type=NoneType]
  ```

  Те саме буває без `show_console_window` і без обох ключів. `init` завжди пише обидва, тож баг бачать ті, хто пише секцію вручну. Задача 09 документує `show_console_window` як «default false».

## Рішення

1. **`main_file`.**
   - `from_pyproject_toml` перевіряє існування `main_file` лише для `tool_pyretort.get("install_as_package") is False`.
   - Блок лишається на своєму місці, до розбору `install_as_package`, тож для standalone-конфігурації він досяжний і покритий тестом до задачі 12.
   - У режимі пакета (`true` або ключа немає) існування файлу не перевіряється.
   - Перевірка, що шлях відносний (`Main file must be relative`), лишається для обох режимів: це помилка формату, а не відсутній файл.
   - `main_file_rel_path` зберігає значення, як і раніше.
2. **`init`.** Якщо `_find_main_file` нічого не знайшов, ключ `main_file` не пишеться. Під двома поясненнями лишається закоментований приклад `# main_file = "main.py"`, а рядок `TODO` зникає. Якщо файл знайдено, поведінка як зараз: `main_file = "<знайдене ім'я>"`.
3. **Типові значення.**
   - Якщо ключа `install_as_package` або `show_console_window` немає, `from_pyproject_toml` не передає його в `BuildConfig`, і діє типове значення моделі.
   - Модель бере типові значення з `INSTALL_AS_PACKAGE_DEFAULT` і `SHOW_CONSOLE_DEFAULT`, щоб `init` і модель мали одне джерело.
   - Перевірка типу для наявного ключа (`must be a boolean`) не змінюється.
4. Тексти повідомлень `check` і `build` не змінюються.

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
2. `test_from_pyproject_uses_defaults_for_missing_optional_booleans` (`tests/test_types.py`), параметризований двома випадками:
   - без `install_as_package` → `config.install_as_package is True`;
   - без `show_console_window` → `config.show_console_window is False`;
   - решта секції повна, `src/__main__.py` існує;
   - зараз обидва випадки падають з `Input should be a valid boolean`;
   - зміна: рішення 3.
3. `test_init_leaves_main_file_commented_out_when_none_found` (`tests/cli/test_init.py`):
   - умова: проєкт без `main.py`, `app.py`, `run.py`;
   - очікування: `"main_file" not in pyretort_config`, у тексті файлу є `# main_file = "main.py"`, немає `TODO`;
   - зараз падає, бо ключ записано;
   - зміна: рішення 2.
4. `test_init_then_check_without_main_file` (`tests/test_integration.py`, клас `TestCLIWorkflow`):
   - умова: `src/workflow_test/__init__.py` і `__main__.py`, без `main.py`;
   - кроки: `init -p` → код 0; `check -p` → код 0 і `is valid` у виводі (просто `valid` трапляється й у `Configuration validation failed`);
   - після кроків 1 і 3 тест пройде одразу. Переконайся, що він червоніє, якщо тимчасово повернути обидві зміни, потім поверни їх.
5. Ручна перевірка:
   - скопіювати `examples/hello-cli` у тимчасову теку й видалити з копії секцію `[tool.pyretort]`;
   - `uv run pyretort init -p <копія>\pyproject.toml`, потім `uv run pyretort check -p <копія>\pyproject.toml` → `is valid`;
   - у копії видалити рядки `install_as_package` і `show_console_window`, знову `check` → `is valid`.
6. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Тести з кроків 1-4 існують під цими назвами й проходять, `test_main_file_does_not_exist_in_standalone_mode` теж. Чотири команди з [README.md](README.md) зелені.
- Ручна перевірка з кроку 5 щоразу дає `is valid`.
- Статус у [README.md](README.md) → DONE.

## Поза межами

- Standalone-режим і обов'язковість `main_file` для нього — задача 12.
- Пошук main-файлів за іншими іменами — ні.
- Обов'язкові поля (`python_version`, `python_architecture`, `project_source_subdir`, `create_dist_zip_file`) лишаються обов'язковими.
- Зміна `[tool.pyretort]` у прикладах — ні: `examples/hello-cli` уже без `main_file`, у Simple RSS `main.py` існує.

## Коміти

- `fix(config): ignore main_file in package mode`
- `fix(config): default install_as_package and show_console_window when absent`
- `fix(init): leave main_file commented out when no main file is found`

## Джерела

- tomlkit, коментарі в таблицях: https://tomlkit.readthedocs.io/en/latest/quickstart/
- pydantic, типові значення полів: https://docs.pydantic.dev/latest/concepts/fields/#default-values
