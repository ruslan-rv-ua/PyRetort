# 03. Оновити залежності

Залежить від: 02. Оцінка: S.

## Мета

Усі прямі залежності та dev-інструменти на актуальних версіях, `uv.lock` оновлений, усі перевірки зелені.

## Контекст

Останнє оновлення залежностей — грудень 2025. Стан на 7 жовтня 2026 (`uv pip list --outdated` у `.venv`):

| Пакет | Зараз | Доступно | Група |
|---|---|---|---|
| typer | 0.19.2 | 0.27.3 | runtime |
| pydantic | 2.12.0 | 2.13.5 | runtime |
| pywin32 | 311 | 312 | runtime |
| tomlkit | 0.13.3 | 0.15.1 | runtime |
| python-slugify | 8.0.4 | 9.1.3 | runtime |
| packaging | 25.0 | 26.3 | runtime |
| pytest | 8.4.2 | 9.1.1 | dev |
| pytest-cov | 7.0.0 | 7.1.0 | dev |
| mypy | 1.18.2 | 2.4.0 | dev |
| ruff | 0.14.0 | 0.16.10 | dev |
| types-pywin32 | 311.0.0.x | 312.0.0.x | dev |

`httpx` і `tomli-w` не в списку застарілих. Нижні межі в `pyproject.toml` всюди `>=`, тож `uv sync --upgrade` підтягне останні версії без правки меж. `uv lock --check` зараз проходить.

Відомі зміни поведінки в нових версіях (з офіційних release notes, перевірено 7 жовтня 2026):

- **typer 0.20 → 0.27.3.** 0.26: Click вендориться всередину typer, Click-специфічні API більше не підтримуються (PyRetort їх не використовує). 0.24: мінімальний Python 3.10. 0.23: трейсбеки Rich без локальних змінних за замовчуванням. 0.27: змінено друк metavar у довідці. 0.20: підказки при помилці в назві команди увімкнені за замовчуванням. Наші тести перевіряють довідку підрядками (`"version" in result.output` тощо), тож зміни форматування їх не ламають; якщо щось зламається — порівнювати підрядки, а не точний текст.
- **mypy 2.0 (травень 2026) → 2.4.** `--local-partial-types` і `--strict-bytes` увімкнені за замовчуванням; `--allow-redefinition` змінив семантику; `--python-version 3.9` відхиляється; з'явився `--num-workers`. Проєкт уже на `strict = true` після задачі 02, тому нові помилки можливі саме через ці дефолти.
- **pytest 9.0 → 9.1.** Python 3.9 не підтримується; попередження `PytestRemovedIn9Warning` стали помилками; CI-режим вмикається лише при непорожніх `CI`/`BUILD_NUMBER`; перекриті шляхи в аргументах схлопуються. 9.1 деприкує `request.getfixturevalue()` під час teardown і не-Collection ітерабельні в `parametrize`. У проєкті маркери зареєстровані в `[tool.pytest.ini_options]`, `addopts = "-m 'not slow'"` — сумісно.
- **pydantic 2.13, tomlkit 0.15, python-slugify 9, pywin32 312.** Відомих несумісностей для використаних API не знайдено; підтвердження — зелений набір тестів (слагіфікацію перевіряє `tests/test_types.py`, tomlkit — `tests/cli/test_init.py`).

## Рішення

1. `uv sync --upgrade`, потім усі перевірки. Виправляти код, а не відкочувати версії; відкат окремого пакета допустимий лише з коментарем-причиною в `pyproject.toml` і записом для CHANGELOG (задача 09).
2. Нижні межі dev-групи підняти до перевірених мажорів: `pytest>=9`, `mypy>=2`, `ruff>=0.16`, `pytest-cov>=7.1`, `types-pywin32>=312`. Межі runtime-залежностей залишити, крім випадку, коли код починає використовувати новіший API.
3. `requires-python = ">=3.11"` без змін.

## Сіми

Нових тестів немає: наявний набір — страхувальна сітка. Один раз запустити і повільні тести (мережа): `uv run pytest -m "slow or not slow"`.

## Кроки

1. `uv sync --upgrade`; переглянути diff `uv.lock`.
2. Чотири команди з README. Виправити, що впало (очікувані місця: типи під mypy 2.x, нові правила ruff 0.16, довідка typer).
3. `uv run pytest -m "slow or not slow"` (потрібен інтернет).
4. Оновити нижні межі dev-групи в `pyproject.toml`, `uv lock`, `uv lock --check`.
5. `uv run pyretort --help` і `uv run pyretort init --help` очима: довідка читається, опції на місці.

## Критерій завершення

- `uv pip list --outdated` не показує жодного пакета з таблиці вище (або відхилення пояснено коментарем у `pyproject.toml`).
- `uv lock --check` проходить; чотири команди з README зелені; повільні тести пройшли хоча б раз.
- Статус у README → DONE.

## Коміти

- `build(deps): upgrade dependencies and dev tools`

## Джерела

- Typer release notes: https://typer.tiangolo.com/release-notes/
- mypy changelog: https://mypy.readthedocs.io/en/stable/changelog.html
- pytest changelog: https://docs.pytest.org/en/stable/changelog.html
- uv, синхронізація й оновлення: https://docs.astral.sh/uv/concepts/projects/sync/
