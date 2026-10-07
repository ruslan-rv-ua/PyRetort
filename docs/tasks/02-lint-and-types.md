# 02. Лінт і типи без помилок

Залежить від: нічого (зручніше після 01). Оцінка: M.

## Мета

`uv run ruff check src tests`, `uv run ruff format --check src tests` і `uv run mypy src` проходять без помилок, правила обох інструментів зафіксовані в `pyproject.toml`, з `init` зник налагоджувальний `print`.

## Контекст

Стан на коміті `3f3e0f4`.

**ruff: 8 помилок E402**, усі одного походження. У чотирьох модулях docstring стоїть після `from __future__ import annotations`:

- `src/pyretort/__init__.py` (рядки 1-3),
- `src/pyretort/__main__.py` (1-3),
- `src/pyretort/builder/downloader.py` (1-3),
- `src/pyretort/builder/exe_generator/generate_exe.py` (1-8).

Docstring модуля має бути першим виразом файлу; інакше це звичайний рядковий літерал, а всі імпорти після нього ruff вважає «не на початку файлу». Виправлення: docstring першим, потім `from __future__`, потім решта імпортів.

**Конфігурації ruff і mypy у `pyproject.toml` немає**: обидва працюють із налаштуваннями за замовчуванням.

**mypy: 12 помилок у 2 файлах.**

- `src/pyretort/types.py:156,166,172,178` — `Decorators on top of @property are not supported [prop-decorator]` на `@computed_field` поверх `@property`. Перевірено 7 жовтня 2026 на mypy 1.18.2 і pydantic 2.12.0: плагін `pydantic.mypy` цю помилку не прибирає. Офіційний обхід із документації pydantic — коментар на рядку декоратора:

  ```python
  @computed_field  # type: ignore[prop-decorator]
  @property
  def dist_name(self) -> str: ...
  ```

- `src/pyretort/cli/commands/init.py:68-112` — `"dict[str, Any]" has no attribute "add"`. Змінна оголошена як `pyretort_config: dict[str, Any] = tomlkit.table()` (рядок 62), а `tomlkit.table()` повертає `tomlkit.items.Table`, у якого є метод `add(key, value=None)` (перевірено на tomlkit 0.13.3). Правильна анотація — `tomlkit.items.Table`. Змінна `tool_section` (рядки 57-60) теж потребує точного типу або `typing.cast`.

**Debug print.** `src/pyretort/cli/commands/init.py:66`: `print(f"{source_subdir=}")` друкує службовий рядок при кожному `pyretort init` і ігнорує `--quiet`. Тест `test_init_quiet_mode` у `tests/cli/test_init.py:154-171` навмисно обходить це (коментар у рядках 169-170).

**Коментар про архітектури.** `src/pyretort/cli/commands/init.py:101` записує в згенерований `pyproject.toml` коментар `(AMD64, x86, ARM64)`, а валідні значення — `amd64`, `win32`, `arm64` (`PythonArchitecture`, `src/pyretort/types.py:15-18`).

**Що дасть увімкнення додаткових правил ruff** (виміряно: `uv run ruff check src tests --select E,F,I,UP,B --statistics`): E501 ×13, E402 ×8, B008 ×6 (виклики `typer.Option`/`typer.Argument` у default-значеннях — відомий хибнопозитив для typer), B904 ×6 (`raise` в `except` без `from`), UP006 ×5, UP035 ×4, UP004 ×2, UP037 ×2, UP045 ×1. Одинадцять із них автовиправні через `--fix`.

**Що дасть `mypy --strict`** разом із плагіном pydantic: 16 помилок (12 наявних + 4) у `types.py`, `init.py`, `generate_exe.py`.

## Рішення

Конфігурація ruff:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I", "UP", "B"]

[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["typer.Option", "typer.Argument"]
```

E5 (довжина рядка) навмисно не вмикається: переноси робить `ruff format`. B008 знімається білим списком typer-викликів, а не вимкненням правила.

Конфігурація mypy:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["pydantic.mypy"]
```

Плагін потрібен для коректної типізації конструкторів моделей pydantic, хоч `prop-decorator` він не лікує. Помилки `strict` виправляються в коді. `# type: ignore[код]` допускається лише з конкретним кодом і коментарем-причиною на тому ж рядку; `ignore_errors`, `ignore_missing_imports` і вимкнення перевірок для цілих модулів не використовуються.

`print` з `init.py:66` видаляється. Коментар про архітектури стає `(amd64, win32, arm64)`.

## Сіми

- CLI `init` через `CliRunner` (`tests/cli/test_init.py`).
- Самі інструменти: команди ruff і mypy — «тести» для конфігурації.

## Кроки

1. Червоний: у `tests/cli/test_init.py::test_init_quiet_mode` замінити перевірку на `assert result.output == ""` і прибрати коментар про `print`. Тест падає через `print`. Зелений: видалити рядок 66 в `init.py`.
2. Червоний: новий тест `test_init_architecture_comment_lists_valid_values` — у тексті згенерованого `pyproject.toml` є підрядок `amd64, win32, arm64`. Зелений: виправити коментар у `init.py:101`.
3. Перенести docstring перед `from __future__` у чотирьох файлах. `uv run ruff check src tests` → 0 помилок.
4. Додати конфігурацію ruff. `uv run ruff check src tests --fix`; решту вручну: B904 — додати `from e` або `from None`; UP035 — `List`, `Optional`, `Tuple` замінити на вбудовані типи й `X | None`. Потім `uv run ruff format src tests`. Тести зелені.
5. Додати конфігурацію mypy. Виправити `prop-decorator` коментарями з документації pydantic, типи tomlkit в `init.py`, решту `strict`-помилок (найімовірніше — відсутні анотації повернення в `generate_exe.py`: `generate_exe` на рядку 24, методи `DataStruct` і `Icon`). `uv run mypy src` → `Success: no issues found`.
6. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Чотири команди з README зелені; `uv run mypy src` друкує `Success: no issues found`.
- У `pyproject.toml` є секції `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.flake8-bugbear]`, `[tool.mypy]` з вмістом вище.
- `uv run pyretort -q init -p <будь-який pyproject.toml>` нічого не друкує (перевіряє тест із кроку 1).
- У коді немає `# type: ignore` без коду помилки: `rg "type: ignore(?!\[)" src` порожній.
- Статус у README → DONE.

## Поза межами

Оновлення версій інструментів — задача 03. Поведінка команд, крім `print` і коментаря, не змінюється.

## Коміти

- `fix(init): remove debug print and fix architecture comment`
- `style: move module docstrings before __future__ imports`
- `build: configure ruff and mypy`
- `refactor: satisfy strict mypy and ruff rules`

## Джерела

- pydantic, `computed_field` і mypy (обхід `# type: ignore[prop-decorator]`): https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.computed_field
- pydantic mypy plugin: https://docs.pydantic.dev/latest/integrations/mypy/
- ruff, налаштування: https://docs.astral.sh/ruff/settings/ ; правила: https://docs.astral.sh/ruff/rules/
- tomlkit API (`tomlkit.items.Table`): https://tomlkit.readthedocs.io/en/latest/api/
- mypy, `--strict`: https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict
