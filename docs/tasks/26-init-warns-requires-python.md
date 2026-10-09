# 26. `init` попереджає, коли `python_version` не задовольняє `requires-python`

Залежить від: нічого. Оцінка: S.

## Мета

`pyretort init` більше не пише мовчки `python_version`, якої не приймає `[project].requires-python`. Записавши секцію, він попереджає тим самим повідомленням, яким `check` відхиляє таку конфігурацію в standalone-режимі, а саме повідомлення тепер каже, що робити. Найважливіше це для режиму пакета, яким іде Quick start у README: там `check` таку версію пропускає, і помилку видно лише на кроці uv під час збірки. Що саме `init` пише в `python_version`, не змінюється, а `check` і `build` відхиляють те саме, що й раніше.

## Контекст

Факти станом на 9 жовтня 2026: коміт `5271810`, uv 0.12.23, packaging 26.3, PyRetort з репозиторію на Python 3.13.9. Перевірено на пробних проєктах у тимчасовій теці, а `uv tool install` — в окремих `UV_TOOL_DIR` і `UV_TOOL_BIN_DIR`.

- **Що робить `init`.** Пише в `python_version` версію Python, на якому працює PyRetort: `_find_python_version` (`src/pyretort/cli/commands/init.py:206-208`) бере `sys.version_info`, а `_build_pyretort_section` (рядки 160-163) кладе її в секцію. `[project].requires-python` `init` не читає: з `[project]` він бере лише `name` (рядок 45). Записавши файл, друкує успіх, «Next steps» і рядок про режим: `Standalone mode: …` або `warning: <шлях>\__main__.py not found; 'pyretort build' will fail until it exists` (рядки 67-86). Попередження йде в stdout через `echo` без `err`, код виходу 0. README в описі `python_version` (`README.md:186`) так і каже: `init` writes the version of the Python that runs PyRetort.
- **Що робить `check`.** `_check_requires_python` (`src/pyretort/types.py:71-90`) кидає `ValueError`: `Invalid requires-python in [project]: '<значення>'`, коли специфікатор не розбирається, і `python_version <версія> does not satisfy requires-python '<значення>' in [project]`, коли версія поза ним (`SpecifierSet.contains(…, prereleases=True)`). `from_pyproject_toml` викликає її лише в standalone-режимі (рядки 407-418), а в режимі пакета розбіжність лишено uv ([задача 12](https://github.com/ruslan-rv-ua/PyRetort/blob/v0.2.0/docs/tasks/12-standalone-mode.md), факт 5 і «Поза межами»). Що робити, повідомлення не каже, хоча інші повідомлення про `python_version` кажуть: на 404 збірка пише `Security-only releases ship no Windows binaries; set python_version to a release that has one.` (`src/pyretort/builder/uv_builder.py:169-174`). Troubleshooting у README про `requires-python` нічого не має.
- **Звідки розбіжність.**
  - `uv init` пише `requires-python = ">=X.Y"` за версією свого Python (довідка `--python`: «The Python interpreter to use to determine the minimum supported Python version») і `.python-version` з `X.Y`: `uv init --python 3.14` дає `">=3.14"`. Без `--python` uv бере найновіший із Python, які встановив сам uv, а коли таких немає — перший знайдений системний.
  - README радить ставити PyRetort через `uv tool install` (`README.md:48-60`). Середовища `uv tool install` і `uvx` за документацією uv не зважають на `.python-version` і `requires-python` проєкту. Перевірено: `uvx pyretort@0.2.0 init` у проєкті з `.python-version` `3.14` і `requires-python = ">=3.14"` записав `python_version = "3.13.15"`, тобто Python, на якому uv на цій машині за замовчуванням створює середовища.
  - Інструмент лишається на тій мінорній версії Python, з якою його встановили, а нові проєкти uv робить на найновішому. Тож розбіжність з'являється, коли новий Python виходить після встановлення PyRetort; Python 3.15.0 за графіком PEP 790 виходить 9 жовтня 2026. Якщо поставити PyRetort і одразу зробити `uv init`, обидві команди беруть той самий Python (тут керований uv 3.13.15, а не системний 3.14.8 зі scoop), і розбіжності немає.
  - Інструмент можна перенести на інший Python: `uv tool upgrade --python 3.14 pyretort` друкує ``Upgraded tool environment for `pyretort` to Python 3.14``, після чого `init` записав `3.14.8`, а `check` сказав `is valid`.
- **Наслідки** (PyRetort з репозиторію, 3.13.9):
  - standalone (`uv init --no-package --python 3.14`): `init` мовчки пише `python_version = "3.13.9"`, а `check` завершується з кодом 1: `Configuration validation failed: python_version 3.13.9 does not satisfy requires-python '>=3.14' in [project]`. `build` зупиняється на тій самій перевірці;
  - режим пакета (`uv init --package --python 3.14` і `src\hello314\__main__.py`, як у Quick start): `check` друкує `is valid`. `build` проходить `Preparing build directory …` і `Installing embedded Python 3.13.9 (amd64)`, тобто видаляє попередню збірку і, якщо архіву немає в `downloads/`, завантажує ~11 МБ, а потім падає: `uv pip install failed with exit code 1:` … `Because the current Python version (3.13.9) does not satisfy Python>=3.14 and hello314==0.1.0 depends on Python>=3.14, we can conclude that hello314==0.1.0 cannot be used.` Лишається `build\hello314-0.1.0-amd64\` з вбудованим Python без exe; з архівом у кеші це забирає 0,8 с.
- **uv ігнорує верхні межі `requires-python`** (документація uv, Resolver internals: «uv ignores upper-bounds on `requires-python`»). `uv pip install --dry-run` проєкту з `uv_build` у вбудований 3.13.9, 14 специфікаторів:
  - збіглися з `SpecifierSet.contains` 9: обидва відкидають `>=3.14`, `~=3.13.10`, `>=3.13.10` і обидва приймають `>=3.13`, `<3.14`, `==3.13.*`, `~=3.13`, `>3.13`, `>=3.11,<4`;
  - розійшлися 5: `<3.13`, `<=3.13`, `==3.13`, `>=3.12,<3.13` і `>=3.11,!=3.13.9` uv ставить, а `packaging` каже «не задовольняє».

  Повна збірка пакета з `requires-python = ">=3.11,<3.13"` і `python_version = "3.13.9"`: `check` — `is valid`, `build` — успіх, `python -m upper` у вбудованому Python друкує `Hello from upper!`. У standalone-режимі uv `requires-python` не звіряє взагалі (`-r pyproject.toml`), а `check` звіряє весь специфікатор.
- **Неправильний `requires-python`** (`"3.13 or later"`) uv відкидає скрізь: `uv pip install <тека>` — код 1 (`Failed to extract static metadata from pyproject.toml`, ``Failed to parse version: Unexpected end of version specifier, expected operator. Did you mean `==3.13`?``), `uv pip install -r pyproject.toml` — код 2, `uv sync` — код 2. `check` відхиляє його лише в standalone-режимі.
- **Правильну версію без мережі не вибрати.** Для security-релізів python.org не дає вбудовуваного архіву: для керованого uv 3.12.12, встановленого на цій машині, `python-3.12.12-embed-amd64.zip` дає 404, а для 3.13.15, 3.13.16 і 3.14.8 архіви є. Релізи з архівами перелічує https://www.python.org/downloads/windows/ (посилання «Windows embeddable package (64-bit)»). Вибір за цим списком — ідея [check-python-version-exists](ideas.md#check-python-version-exists).
- **Прецеденти.** `init` уже попереджає з кодом 0 про відсутній `__main__.py`. Функції `types.py`, якими користуються інші модулі, публічні: `launcher_entry_point` (рядок 50) імпортує й `init`, а імен із підкресленням з іншого модуля не імпортує жоден модуль.
- **Тести.** `tests/cli/test_init.py`: фікстура `my_app_pyproject` (рядки 18-37) має `requires-python = ">=3.11"`, бо `init` пише версію Python, на якому біжать тести ([задача 21](https://github.com/ruslan-rv-ua/PyRetort/blob/v0.2.0/docs/tasks/21-init-detects-standalone.md), «Контекст»). `test_init_warns_when_dunder_main_is_missing` (рядок 348) перевіряє попередження в `result.stdout`; `test_init_does_not_warn_when_dunder_main_exists` (рядок 372, без `requires-python`) і `test_init_does_not_warn_about_dunder_main_in_standalone_mode` (рядок 501, `>=3.11`) вимагають, щоб слова `warning` у виводі не було. Повідомлення `check` перевіряють `test_from_pyproject_rejects_python_version_outside_requires_python_in_standalone_mode` і `test_from_pyproject_rejects_invalid_requires_python_in_standalone_mode` (`tests/test_types.py:1328-1399`). PyRetort вимагає Python 3.11+ (`pyproject.toml`), CI тестує на 3.13 (`.github/workflows/ci.yml`). Вивід `init` інші тести не розбирають: `tests/test_integration.py` перевіряє лише коди виходу `init` і `check`.
- **Перевірка задачі.** Чернетку рішень 1–3 перевірено й відкинуто: 274 швидкі тести, mypy і `ruff check` проходять, мутанти кроків 4–5 червонять саме названі там тести, а ручна перевірка кроку 7 дає вказаний там вивід.

## Рішення

1. **Коли й де.** Записавши секцію і надрукувавши рядок про режим, `init` звіряє записану `python_version` з `[project].requires-python`, якщо воно є, тією ж функцією, що й `check`. Коли функція кидає `ValueError`, `init` друкує через `echo` в stdout `warning: <повідомлення>`, тож `-q` його глушить. Секція записується як і раніше, код виходу 0. Попередження — в обох режимах: у режимі пакета воно єдиний сигнал до збірки.
2. **Текст.** Повідомлення функції про розбіжність отримує пораду, як повідомлення про 404, а `init` друкує повідомлення функції дослівно, з префіксом `warning: `:

   ```text
   warning: python_version 3.13.9 does not satisfy requires-python '>=3.14' in [project]; set python_version to a release that satisfies it
   warning: Invalid requires-python in [project]: '3.13 or later'
   ```

   `check` отримує ту саму пораду: `Configuration validation failed: python_version 3.13.9 does not satisfy requires-python '>=3.14' in [project]; set python_version to a release that satisfies it`. Через однаковий текст один пункт Troubleshooting у README пояснює і попередження `init`, і помилку `check`. Порада правдива для обох команд. Звідки взялася версія (`init`, `uv tool`, `uvx`), пояснює README, бо в `check` її могли вписати й вручну. Текст не обіцяє, що збірка впаде: у режимі пакета з верхньою межею вона проходить. Неправильний `requires-python` дає попередження заодно, бо функція кидає той самий `ValueError`; тест кроку 4 гарантує, що `init` на ньому не падає з трейсбеком.
3. **Функція.** `_check_requires_python` стає публічною `check_requires_python` у `types.py`, як `launcher_entry_point`: нею тепер користуються два модулі. Перейменування — окремим комітом рефакторингу. `init_command` обчислює `python_version = _find_python_version()` один раз і передає в `_build_pyretort_section` новим параметром.
4. **Що пише `init`, не змінюється:** версію Python, на якому працює PyRetort, як і обіцяє README. Версію, що задовольняє `requires-python` і має архів, `init` вибиратиме за списком із python.org (ідея check-python-version-exists).
5. **Що відхиляють `check` і `build`, не змінюється.** У standalone-режимі `check` і далі звіряє весь `requires-python`, бо uv не звіряє нічого. У режимі пакета розбіжність лишається uv, а він перевіряє лише нижню межу й ігнорує верхні. Повна перевірка в `check` відхилила б збірки, які працюють (`>=3.11,<3.13` з 3.13.9), а копія правила uv дублювала б uv заради помилки, яку той і так зрозуміло пояснює. Це уточнює запис журналу «Залежності — лише `[project].dependencies`»: у режимі пакета uv виявляє лише `python_version`, нижчу за `requires-python`.
6. **Документація.**
   - README, опис `python_version` (`README.md:186`): `init` пише версію Python, на якому працює PyRetort, і попереджає, коли вона не задовольняє `requires-python`.
   - README, Troubleshooting, після пунктів про помилки конфігурації (пункт про `main_file`, а якщо задачу 25 уже виконано, то після її пунктів про ім'я й версію): `python_version … does not satisfy requires-python '…' in [project]; set python_version to a release that satisfies it` → `init` пише версію Python, на якому працює PyRetort, а `uv tool install` і `uvx` обирають цей Python, не дивлячись на проєкт. Поставити в `python_version` реліз, що задовольняє `requires-python` і має Windows embeddable package; їх перелічує https://www.python.org/downloads/windows/. Щоб `init` писав підхожу версію для наступних проєктів, перенести PyRetort на їхній Python, наприклад `uv tool upgrade --python 3.14 pyretort`.
   - README, Troubleshooting, перед пунктом про `os error 216`: `uv pip install failed with exit code 1: … the current Python version (…) does not satisfy Python>=…` → `python_version` нижча, ніж дозволяє `requires-python`. У режимі пакета `check` лишає це uv, який ігнорує верхні межі на кшталт `<3.13`, тож збірка зупиняється лише на цьому кроці. Виправити `python_version`, як у пункті про `requires-python` вище.
   - CHANGELOG `[Unreleased]`, `### Fixed` (якщо розділ уже створила задача 25, дописати туди): `init` мовчки писав `python_version`, що не задовольняє `requires-python`, коли PyRetort працює не на тому Python, якого потребує проєкт (наприклад 3.13.9 для `requires-python = ">=3.14"`); `check` таку конфігурацію відхиляв у standalone-режимі, а в режимі пакета збірка падала на кроці uv. Тепер `init` про це попереджає, а повідомлення `init` і `check` кажуть, що виправити.

## Сіми

- CLI `init` через `CliRunner`, як у `tests/cli/test_init.py`.

## Кроки

Кожен крок: тест → червоний → мінімальна зміна → `uv run pytest` зелений → далі. Тест, що проходить одразу, перевіряють тимчасовим мутантом (журнал рішень, «Тест, що проходить одразу, перевіряють мутантом»).

1. Рефакторинг (рішення 3): `_check_requires_python` → `check_requires_python` разом із викликом у `from_pyproject_toml`. `uv run pytest` зелений до і після, коміт `refactor(config): make the requires-python check public`. Якщо задача 25 ще TODO, онови назву функції в її «Контексті».
2. `test_from_pyproject_rejects_python_version_outside_requires_python_in_standalone_mode` (`tests/test_types.py:1328`): у `match` — повне повідомлення з порадою з рішення 2, `…in \\[project\\]; set python_version to a release that satisfies it`.
   - зараз падає: поради немає. Без неї тест проходив, бо `pytest.raises(match=…)` шукає збіг через `re.search` і задовольняється початком повідомлення;
   - зміна: порада в повідомленні `check_requires_python` (рішення 2).
3. `test_init_warns_when_python_version_does_not_satisfy_requires_python` (`tests/cli/test_init.py`, новий клас `TestInitCommandRequiresPython`, як і тест кроку 4), параметризований розкладкою:
   - standalone: `main.py` у корені → `install_as_package = false`;
   - пакет: `src/my_app/__init__.py` і `src/my_app/__main__.py` → `install_as_package = true`;
   - `pyproject.toml`: `name = "my-app"`, `version = "0.1.0"`, `requires-python = "<3.11"` і `[build-system]` з hatchling, як в інших тестах файлу (на вибір режиму він не впливає);
   - очікування: код 0; `install_as_package` у записаній секції — як у розкладки; у `result.stdout` є рядок `warning: python_version <V> does not satisfy requires-python '<3.11' in [project]; set python_version to a release that satisfies it`, де `<V>` — `python_version` із записаного файлу. `<3.11` не задовольняє жоден Python, на якому працює PyRetort, тож тест не залежить від Python машини чи CI;
   - зараз падає: попередження немає;
   - зміна: рішення 1 і 3.
4. `test_init_warns_about_invalid_requires_python`: розкладка standalone, `requires-python = "3.13 or later"` → код 0, секцію записано, у `result.stdout` є `warning: Invalid requires-python in [project]: '3.13 or later'`, у `result.output` немає `Traceback`. Проходить одразу; мутант — попереджати лише про розбіжність версії, а неправильний специфікатор пропускати мовчки.
5. Мутанти для наявних тестів, нового тесту немає:
   - попереджати й тоді, коли версія задовольняє `requires-python`, → червоніє `test_init_does_not_warn_about_dunder_main_in_standalone_mode` (`>=3.11`);
   - звіряти й тоді, коли `requires-python` немає (функція отримує `None`), → червоніє `test_init_does_not_warn_when_dunder_main_exists`.
6. Документація (рішення 6).
7. Ручна перевірка в тимчасовій теці поза репозиторієм. `requires-python` має бути вищим за Python репозиторію (`uv run python --version`, зараз 3.13.9):
   - `uv init --no-package --python 3.14 probe-script` і `uv init --package --python 3.14 probe-pkg`, у другому — `src\probe_pkg\__main__.py` з `from probe_pkg import main` і `main()`;
   - `uv run --project <репозиторій> pyretort init -p <проєкт>\pyproject.toml` → для обох код 0 і останній рядок `warning: python_version 3.13.9 does not satisfy requires-python '>=3.14' in [project]; set python_version to a release that satisfies it`;
   - `check` → для `probe-script` код 1 і той самий текст після `Configuration validation failed: `, для `probe-pkg` — `is valid` (рішення 5);
   - `requires-python = ">=3.13"` і `init --force` → попередження немає.
8. Критерій завершення.

## Критерій завершення

- Тест кроку 2 вимагає повного повідомлення, тести з кроків 3–4 існують під цими назвами; усі проходять. Тест кроку 4 червонів зі своїм мутантом, а наявні тести з кроку 5 — зі своїми.
- У `src/` і `tests/` не лишилося `_check_requires_python`.
- Ручна перевірка з кроку 7 дала очікувані коди й повідомлення.
- README і CHANGELOG оновлено (рішення 6).
- Чотири команди з [README.md](README.md) зелені.
- Статус задачі в [README.md](README.md) → DONE.

## Поза межами

- Вибір `python_version`, що задовольняє `requires-python`: потрібен список релізів з архівом із python.org, бо security-релізи архіву не мають, — ідея [check-python-version-exists](ideas.md#check-python-version-exists). Те саме з версією з `.python-version` чи `.venv` проєкту: це змінює, що пише `init`, і без списку однаково може дати реліз без архіву.
- Перевірка `requires-python` у `check` для режиму пакета (рішення 5). Втрату попередньої збірки через пізню помилку розв'язує ідея [build-keeps-previous-on-failure](ideas.md#build-keeps-previous-on-failure).
- Неправильний `requires-python` у `check` для режиму пакета: на ньому раніше падають `uv sync`, `uv run` і `uv add`, як і на помилках у `[project].dependencies` ([задача 25](25-check-project-name-version.md), «Поза межами»).
- Текст «Next steps» в `init`.

## Коміти

- `refactor(config): make the requires-python check public`
- `fix(config): say how to fix a python_version outside requires-python`
- `fix(init): warn when python_version does not satisfy requires-python`
- `test(init): warn about an invalid requires-python`
- `docs: explain the requires-python warning`

## Джерела

- uv, Tools: середовища інструментів не зважають на `.python-version` і `requires-python` проєкту: https://docs.astral.sh/uv/concepts/tools/
- uv, Python versions: порядок пошуку, керовані версії — від новіших: https://docs.astral.sh/uv/concepts/python-versions/
- uv, Resolver internals: верхні межі `requires-python` ігноруються: https://docs.astral.sh/uv/reference/internals/resolver/
- uv CLI, `uv init --python` і `uv tool upgrade --python`: https://docs.astral.sh/uv/reference/cli/
- PEP 790, графік Python 3.15: https://peps.python.org/pep-0790/
- python.org, релізи для Windows із вбудовуваними архівами: https://www.python.org/downloads/windows/
- Задача 12, факт 5 і «Поза межами»: https://github.com/ruslan-rv-ua/PyRetort/blob/v0.2.0/docs/tasks/12-standalone-mode.md
