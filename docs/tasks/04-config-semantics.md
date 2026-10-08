# 04. Чесна конфігурація

Залежить від: 03. Оцінка: L.

## Мета

Кожне поле `[tool.pyretort]` і кожна перевірка в `BuildConfig` або робить щось корисне, або чесно каже, що не підтримується. Після задачі: модуль для запуску виводиться з `project_source_subdir` і перевіряється під час `check`; будь-який PEP 517 build-backend приймається; `install_as_package = false` відхиляється зрозумілим повідомленням без трейсбека; `init` не затирає наявну секцію без `--force` і попереджає, якщо пакет не має `__main__.py`.

## Контекст

### Як зараз запускається застосунок

`UVBuilder._build_as_package` ([`src/pyretort/builder/uv_builder.py:22-58`](../../src/pyretort/builder/uv_builder.py)) встановлює проєкт у вбудований Python командою `uv pip install --python <embedded python.exe> <project_dir>` (рядки 32-46) і генерує лаунчер із командою (рядки 50-51):

```python
package_name = self.config.project_name_slug_underscore
command_str = f'"{{EXE_DIR}}\\{python_exe_relative}" -m {package_name}'
```

Тобто лаунчер виконує `python -m <слаг_імені_проєкту_через_підкреслення>`. Це працює лише якщо (а) імпортоване ім'я пакета збігається зі слагом імені проєкту і (б) у пакеті є `__main__.py`. Жодне з двох не перевіряється: `check` каже «valid», а зібраний exe мовчки нічого не робить, бо консоль прихована. Поле `project_source_subdir` при цьому лише перевіряється на існування ([`src/pyretort/types.py:266-274`](../../src/pyretort/types.py)) і ніде більше не використовується, як і `main_file` (рядки 276-286).

`init` визначає теку джерел як `<корінь>/{".", "src", "source", "app", "lib"}/<слаг_підкреслення>` ([`src/pyretort/cli/commands/init.py:122-130`](../../src/pyretort/cli/commands/init.py)), тож у типовому випадку вона і є текою пакета, наприклад `src/simple_rss`.

### Обмеження build-backend

`BuildBackend` ([`types.py:21-33`](../../src/pyretort/types.py)) дозволяє лише `hatchling.build` і `uv_build`; `from_pyproject_toml` відхиляє інші (рядки 300-309); `build_command` ([`src/pyretort/cli/commands/build.py:37-44`](../../src/pyretort/cli/commands/build.py)) через `match` приймає лише `uv_build` і друкує «Unsupported build tool» для hatchling. Обмеження штучне: проєкт збирає `uv pip install`, якому байдуже, який PEP 517 backend оголошено (сам PyRetort зібраний hatchling і ставиться uv). Поле `[build-system].build-backend` потрібне лише як ознака, що проєкт збирається стандартним способом.

### Standalone-режим

`install_as_package = false` веде в `NotImplementedError` ([`uv_builder.py:18-20`](../../src/pyretort/builder/uv_builder.py)) уже після того, як `BaseBuilder.__init__` створив теки. Користувач бачить трейсбек.

### `init`

- Затирає наявну `[tool.pyretort]` без попередження: `tool_section["pyretort"] = pyretort_config` ([`init.py:117`](../../src/pyretort/cli/commands/init.py)).
- Пише `main_file` і `install_as_package` без пояснення, що перше ігнорується в режимі пакета, а друге має бути `true`.

### Тести, яких це торкнеться

- `tests/test_types.py`: `TestBuildBackend` (рядок 41), `test_missing_build_backend` (615), `test_invalid_build_backend` (676), `test_install_as_package_default` (271), `test_main_file_*` (768, 800).
- `tests/cli/test_build.py`: `test_build_unsupported_backend` (71-101) очікує код 1 для hatchling.
- Фікстури й inline-побудови, які створюють теку джерел без `__main__.py`: `tests/conftest.py` (`valid_pyproject_toml` 57-68, `invalid_pyproject_old_python` 84-115), `tests/test_types.py`, `tests/cli/test_build.py`, `tests/cli/test_check.py`, `tests/test_integration.py`. Перевірити `rg "fixtures" tests`, чи файли `tests/fixtures/*.toml` взагалі використовуються. Фікстура `tests/conftest.py::sample_build_config` (14-27) передає `build_backend=BuildBackend.UV`.

Приклад `examples/Simple RSS` має `src/simple_rss/__main__.py` і проходить `check` зараз; після задачі теж має проходити.

## Рішення

1. **Модуль запуску.** Нове обчислюване поле `BuildConfig.main_module: str`:
   - якщо `project_source_subdir_rel_path != Path(".")` — ім'я останньої компоненти шляху (`src/simple_rss` → `simple_rss`);
   - інакше — `project_name_slug_underscore`.

   Лаунчер використовує `main_module` замість `project_name_slug_underscore`.
2. **Перевірка точки входу** у `from_pyproject_toml`, коли `install_as_package` істинне, після всіх наявних перевірок шляхів:
   - для subdir ≠ `.`: має існувати `<project_dir>/<subdir>/__main__.py`;
   - для subdir = `.`: має існувати `<project_dir>/<main_module>/__main__.py` або `<project_dir>/<main_module>.py`.

   Інакше `ValueError` з текстом: `Package mode requires '<шлях до __main__.py>': the launcher runs 'python -m <main_module>'. Point project_source_subdir at the package directory or add __main__.py.`
3. **Build-backend.** Будь-який непорожній рядок приймається; `BuildBackend` і його валідатор видаляються; поле `build_backend: str` залишається інформаційним. `[build-system]` з `build-backend` і далі обов'язковий: без нього uv збирає legacy-setuptools із попередженнями, цього не хочемо. `build_command` завжди створює `UVBuilder`; `match` видалити.
4. **Standalone.** `from_pyproject_toml` для `install_as_package = false` кидає `ValueError("install_as_package = false (standalone mode) is not supported yet; set it to true or see docs/tasks/12-standalone-mode.md")`. Завдяки наявній обробці `ValueError` у `check` і `build` користувач бачить повідомлення без трейсбека, а `build` нічого не створює на диску. Поле в моделі залишається: його реалізує задача 12.
5. **`init`.**
   - Якщо `[tool.pyretort]` уже є — stderr `pyproject.toml already contains [tool.pyretort]; use --force to overwrite`, код 1; з `--force` секція перезаписується.
   - Коментар до `install_as_package`: `Must be true: standalone mode (false) is not supported yet`. Коментар до `main_file`: `Used only when install_as_package = false; ignored otherwise`.
   - Після запису, якщо правило 2 для згенерованої конфігурації не виконується — stdout `warning: <шлях>/__main__.py not found; 'pyretort build' will fail until it exists`, код виходу 0.

## Сіми

- `BuildConfig(...)` напряму (поле `main_module`) і `BuildConfig.from_pyproject_toml(path)`.
- `UVBuilder.build()` з підміненими `PydistManager`, `subprocess.run` і `generate_exe` (`patch("pyretort.builder.uv_builder.generate_exe")` тощо): перевіряється лише аргумент `command` у виклику `generate_exe`.
- CLI `check`, `build` (з підміненим `UVBuilder`, як у `tests/cli/test_build.py:64`), `init` через `CliRunner`.

## Кроки

1. `test_main_module_is_last_component_of_source_subdir` (`src/simple_rss` → `"simple_rss"`) і `test_main_module_falls_back_to_project_slug_for_root_subdir` (`.`, ім'я `My App` → `"my_app"`) у `tests/test_types.py`. Додати обчислюване поле.
2. `test_from_pyproject_rejects_package_without_dunder_main` (ValueError, у повідомленні `__main__.py` і `python -m`) та `test_from_pyproject_accepts_single_module_in_root` (`.` + `mytool.py`). Реалізувати перевірку. Далі додати `__main__.py` у всі фікстури й inline-побудови з переліку вище, поки `uv run pytest` не стане зеленим.
3. `test_build_launcher_runs_main_module` у новому `tests/test_uv_builder.py`: конфігурація з subdir `src/my_pkg`, усе зовнішнє підмінене; `generate_exe` викликано з `command`, що закінчується на `-m my_pkg`. Замінити `project_name_slug_underscore` на `main_module` у `uv_builder.py:50`.
4. `test_from_pyproject_accepts_any_build_backend` (`setuptools.build_meta`). Прибрати enum і валідатор; `test_invalid_build_backend` і `TestBuildBackend` замінити на тест «порожній рядок відхиляється»; `test_build_unsupported_backend` перейменувати на `test_build_with_hatchling_backend_uses_uv_builder` з очікуванням коду 0 і виклику `UVBuilder`.
5. `test_check_rejects_standalone_mode` і `test_build_rejects_standalone_mode_without_traceback`: код 1, у виводі `not supported yet`, у виводі немає `Traceback`, у теці проєкту не з'явилися `build/`, `downloads/`, `dist/`.
6. `test_init_refuses_to_overwrite_existing_section`, `test_init_force_overwrites_existing_section`, `test_init_warns_when_dunder_main_is_missing`, `test_init_comments_explain_install_as_package_and_main_file` (підрядки коментарів у файлі).
7. `uv run pyretort check -p "examples\Simple RSS\pyproject.toml"` → `is valid`.
8. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Усі тести з кроків 1-6 існують і проходять; `uv run pytest` зелений; чотири команди з README зелені.
- У `src/pyretort/types.py` немає класу `BuildBackend`; у `build.py` немає `match`.
- `pyproject.toml` з `build-backend = "hatchling.build"` і коректним `__main__.py` проходить `check`.
- Статус у README → DONE.

## Поза межами

Виправлення в `BaseBuilder`/`UVBuilder` (теки, іконка, помилки uv) — задача 05. Реалізація standalone — задача 12. README і таблиця полів — задача 09.

## Коміти

- `feat(config): derive launcher module from source dir and validate __main__.py`
- `feat(config): accept any PEP 517 build backend`
- `feat(config): reject standalone mode with a clear message`
- `feat(init): add --force and warn about missing __main__.py`

## Джерела

- Python, `-m` і `__main__.py`: https://docs.python.org/3/library/__main__.html
- uv pip install із локального проєкту: https://docs.astral.sh/uv/pip/packages/
- pydantic, `computed_field`: https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.computed_field
