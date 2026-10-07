# 01. Команда `cleanup`: тести, необов'язкові цілі, шляхи відносно проєкту

Залежить від: нічого. Оцінка: S.

## Мета

`pyretort cleanup` видаляє артефакти збірки саме того проєкту, на який вказує `pyproject.toml`, без аргументів чистить усе, і має тести.

## Контекст

Команда живе в [`src/pyretort/cli/commands/clean.py`](../../src/pyretort/cli/commands/clean.py) і зареєстрована як `cleanup` у [`src/pyretort/cli/__init__.py:55`](../../src/pyretort/cli/__init__.py). Тестів на неї немає, покриття файлу 31 %.

Що робить зараз:

- Приймає позиційні цілі `cache`, `build`, `all` (`VALID_TARGETS`, рядок 17) без урахування регістру. `cache` видаляє `downloads/`, `build` видаляє `build/` і `dist/`, `all` — усе. Назви тек — константи `DOWNLOAD_DIR_DEFAULT`, `BUILD_DIR_DEFAULT`, `DIST_DIR_DEFAULT` у `src/pyretort/constants.py`.
- Аргумент обов'язковий, тому `pyretort cleanup` без цілей падає з «Missing argument 'TARGETS...'» (код 2), а гілка `if not targets: targets = ["all"]` (рядки 36-37) мертва.
- Теки шукає відносно поточної теки процесу: `_cleanup_dir` робить `Path(dir_path)` (рядки 64-74). Збірка ж створює теки поруч із `pyproject.toml`: `BaseBuilder` бере `config.project_dir_abs_path` ([`src/pyretort/builder/base_builder.py:17-19`](../../src/pyretort/builder/base_builder.py)), а це батьківська тека `pyproject.toml` ([`src/pyretort/types.py:245`](../../src/pyretort/types.py)). Отже `cleanup`, запущений з іншої теки, чистить не те.
- `complete_cleanup_targets` (рядки 20-22) — автодоповнення, яке ніколи не спрацьовує, бо застосунок створено з `add_completion=False`.
- Імпортує `List` із `typing` і `Annotated` з `typing_extensions`; `typing_extensions` не оголошена в залежностях проєкту.
- Повідомлення виводить через `echo(ctx, ...)` з `src/pyretort/cli/_output.py`, тому `--quiet` працює.

Як інші команди отримують шлях до проєкту: опція `-p/--pyproject-toml` з default `Path.cwd() / "pyproject.toml"` (наприклад [`src/pyretort/cli/commands/check.py:13-22`](../../src/pyretort/cli/commands/check.py)). Пастка: цей default стоїть у сигнатурі й обчислюється під час імпорту модуля, тому `monkeypatch.chdir` у тестах на нього не впливає.

Перевірено 7 жовтня 2026 на typer 0.19.2 (встановлена версія): аргумент `targets: Annotated[list[str] | None, typer.Argument()] = None` дає `None`, коли цілей не передано, і список рядків інакше.

## Рішення

1. Цілі необов'язкові. Без цілей — `all`.
2. Нова опція `-p/--pyproject-toml` (та сама назва, що в інших командах). Тека проєкту — батьківська тека цього файлу після `resolve()`. Default — `Path.cwd() / "pyproject.toml"`, обчислений під час виклику команди, а не під час імпорту. Якщо файлу немає — у stderr `Configuration file not found: <path>`, код виходу 1, нічого не видаляється. Вимога існування файлу навмисна: вона захищає від видалення чужої теки `build/` при запуску не там.
3. Семантика цілей, регістронезалежність, тексти повідомлень (`Removed ...`, `... not found: ...`, `Cleanup complete.`, `Invalid cleanup targets: ...`) і код 1 для невідомої цілі — без змін.
4. `complete_cleanup_targets` видалити. `List` → `list`, `typing_extensions.Annotated` → `typing.Annotated`.

## Сіми

Тільки CLI: `CliRunner().invoke(app, ["cleanup", ...])` з `app` із `pyretort.cli`. Функції `_cleanup_*` напряму не тестуються.

Фікстура для тестів (новий файл `tests/cli/test_cleanup.py`): тека `project` всередині `tmp_path` з порожнім `pyproject.toml` і теками `downloads/`, `build/`, `dist/`, у кожній по одному файлу. Поточну теку процесу перемикати на іншу (`monkeypatch.chdir(tmp_path / "elsewhere")`), щоб тест ловив прив'язку до CWD.

## Кроки

Кожен крок: написати тест → побачити, що він падає → мінімальна зміна → `uv run pytest -q tests/cli/test_cleanup.py` зелений → далі.

1. `test_cleanup_cache_removes_only_downloads_dir`: `cleanup cache -p <project>/pyproject.toml` з CWD в іншій теці → код 0, `downloads/` зникла, `build/` і `dist/` на місці. Падає, бо опції `-p` немає. Додати опцію і перенести обчислення шляхів у теку проєкту.
2. `test_cleanup_build_removes_build_and_dist_dirs`: `cleanup build` → `build/` і `dist/` зникли, `downloads/` на місці.
3. `test_cleanup_all_removes_every_artifact_dir`.
4. `test_cleanup_without_targets_removes_everything`: `cleanup -p ...` без цілей → код 0, усі три теки зникли. Падає з «Missing argument». Зробити аргумент необов'язковим.
5. `test_cleanup_targets_are_case_insensitive`: ціль `CACHE`.
6. `test_cleanup_rejects_unknown_target`: `cleanup nope` → код 1, у виводі `Invalid cleanup targets` і `cache, build, all`, теки на місці.
7. `test_cleanup_reports_missing_dirs_without_failing`: проєкт без тек артефактів → код 0, у виводі `not found`.
8. `test_cleanup_quiet_prints_nothing`: `-q cleanup all -p ...` → порожній вивід, теки видалено.
9. `test_cleanup_fails_when_pyproject_missing`: `-p <tmp>/nope.toml` → код 1, `Configuration file not found`, теки на місці.
10. `test_cleanup_defaults_to_pyproject_in_current_directory`: `monkeypatch.chdir(project)` і без `-p` → теки видалено. Падає, поки default обчислюється під час імпорту.
11. Рефакторинг окремим комітом: прибрати автодоповнення, оновити типи, оновити docstring і `help` так, щоб `uv run pyretort cleanup --help` показував `[TARGETS]...` як необов'язкові та опцію `-p`.

## Критерій завершення

- Усі 10 тестів вище існують під цими назвами і проходять; `uv run pytest` зелений.
- `uv run pytest --cov=pyretort.cli.commands.clean --cov-report=term-missing tests/cli/test_cleanup.py` показує покриття `clean.py` не нижче 90 %.
- `uv run ruff check src tests` і `uv run mypy src` показують не більше помилок, ніж до задачі (8 і 12).
- Статус задачі в [README.md](README.md) змінено на DONE.

## Поза межами

Інші команди (`init`, `check`, `build`) і їхній default для `-p` — задача 05.

## Коміти

- `feat(cli): make cleanup targets optional and project-relative` (тести й реалізація разом, бо писалися зрізами).
- `refactor(cli): drop dead completion and modernize typing in cleanup`.

## Джерела

- Typer, аргументи з кількома значеннями: https://typer.tiangolo.com/tutorial/multiple-values/arguments-with-multiple-values/
- pytest, `monkeypatch.chdir`: https://docs.pytest.org/en/stable/how-to/monkeypatch.html
