# 25. `check` і `build` відхиляють `[project].name` і `version`, які відкидає uv

Залежить від: нічого. Оцінка: S.

## Мета

`pyretort check` більше не схвалює `[project].name` чи `[project].version`, на яких збірка гарантовано падає: uv приймає лише ім'я за правилами назв пакетів Python і версію за PEP 440. `build` зупиняється на тій самій перевірці, ще до того як видалить попередню збірку чи завантажить Python. Повідомлення називає поле, значення і правило, а для імені пропонує правильне, з яким збірка дасть ті самі exe і теки.

## Контекст

Факти станом на 9 жовтня 2026: коміт `79ffa81`, uv 0.12.23, packaging 26.3. Перевірено на пробних проєктах у тимчасовій теці. Уперше помічено в [задачі 12](https://github.com/ruslan-rv-ua/PyRetort/blob/v0.2.0/docs/tasks/12-standalone-mode.md), факт 6.

- `BuildConfig.from_pyproject_toml` (`src/pyretort/types.py:289-298`) перевіряє лише, що `name` і `version` є в `[project]`, і передає значення в модель без змін (рядки 437-438). `check` (`src/pyretort/cli/commands/check.py:18-22`) і `build` (`src/pyretort/cli/commands/build.py:20-27`) друкують `ValueError` з неї й завершуються з кодом 1. Сам PyRetort бере з імені лише slug (`project_name_slug_dash`, `project_name_slug_underscore`, `types.py:231-247`), тож пробіл йому не заважає.
- Значення, які `check` зараз називає valid, а uv відкидає в обох режимах (`uv pip install -r pyproject.toml` — код 2, `uv pip install <тека проєкту>` — код 1):
  - імена `System Monitor`, `Монітор`, `café`, `my-app-`, `-my-app`, `_a`, `a.`, `a+b`, `app!` і порожнє. uv: `Not a valid package or extra name: "System Monitor". Names must start and end with a letter or digit and may only contain -, _, ., and alphanumeric characters.`;
  - версії `1.0 beta`, `latest` і порожня. uv: ``after parsing `1.0 `, found `beta`, which is not part of a valid version`` і `expected version to start with a number, but no leading ASCII digits were found`.

  Незвичні, але правильні значення uv приймає: імена `My_App.v2`, `a..b`, `a-_-b`, `A`, `1`; версії `v1.0`, `1.0` з пробілом попереду, `1.0-beta`, `1.0.0-rc.1`, `1!2.0`, `1.0+local.7`, `01.02`.
- `packaging.utils.canonicalize_name(name, validate=True)` (виняток `InvalidName`) і `packaging.version.Version` (виняток `InvalidVersion`) на 22 іменах і 18 версіях, зокрема всіх наведених вище, відповіли так само, як uv: регулярний вираз у packaging має `re.ASCII`, як і правило uv. Параметр `validate` і `InvalidName` з'явилися в packaging 23.2, а `pyproject.toml` вимагає `packaging>=21.0` (рядок 31). `uv.lock` записує цю межу (`specifier = ">=21.0"`, рядок 685), а CI запускає `uv sync --locked`, який падає, коли `uv.lock` розійшовся з `pyproject.toml`.
- На не-рядку packaging кидає не `ValueError`: `canonicalize_name(123, validate=True)` — `TypeError: expected string or bytes-like object, got 'int'`, `Version(1.0)` до packaging 26.3 — `TypeError`, з 26.3 — `InvalidVersion`. `check` і `build` ловлять лише `ValueError`, тож без перевірки типу впали б із трейсбеком. Зараз не-рядок відкидає pydantic: на `version = 1.0` (у TOML це число) `check` друкує `1 validation error for BuildConfig`, `project_version`, `Input should be a valid string [type=string_type, input_value=1.0, input_type=float]` і посилання на errors.pydantic.dev.
- Ціна пізньої помилки. `UVBuilder.build` (`src/pyretort/builder/uv_builder.py:72-79`) спершу викликає `prepare_directories`, який видаляє `build/<dist_name>/` (`src/pyretort/builder/base_builder.py:47-48`), потім завантажує вбудований Python (~11 МБ, якщо архіву ще немає в `downloads/`), і лише тоді падає uv. Відтворено: після вдалої збірки проєкту `system-monitor` ім'я змінено на `System Monitor`. Slug не змінився, тож `build` за 0,5 с видалив робочу збірку `build/system-monitor-0.1.0-amd64/` і впав, лишивши в ній вбудований Python без `system-monitor.exe`. Саме повідомлення зрозуміле: `uv pip install failed with exit code 2:` і текст uv вище.
- Звідки береться погане ім'я. `uv init` його не пише: з теки `System Monitor` робить `system-monitor`, а для `Монітор` і `my app!` відмовляється (`The target directory (...) is not a valid package name. Please provide a package name with --name.`). `uv sync` і `uv run` на поганому імені чи версії теж падають. Тож ім'я змінюють вручну, найімовірніше заради назви exe, хоча exe однаково називається за slug (`system-monitor.exe`). Власна назва exe — ідея [build-exe-name](ideas.md#build-exe-name).
- Прецеденти. `check` уже відхиляє конфігурацію, на якій падає збірка: режим пакета без точки входу, `dependencies` у `dynamic` і `python_version` поза `requires-python` у standalone-режимі (журнал рішень, «Режим пакета перевіряє точку входу» і «Залежності — лише `[project].dependencies`»). `_check_requires_python` (`types.py:71-90`) перевіряє формат поля `[project]` і пише `Invalid requires-python in [project]: '…'`; помилки типу звучать як `'install_as_package' must be a boolean, got int`.
- Тести. `from_pyproject_toml` з `tmp_path` — у `tests/test_types.py`, наприклад `test_from_pyproject_rejects_invalid_requires_python_in_standalone_mode` (з рядка 1366). CLI — `tests/cli/test_check.py` (`test_check_accepts_standalone_mode`, рядок 155) і `tests/cli/test_build.py`: `test_build_reports_missing_main_file_without_traceback` (рядок 210) перевіряє, що після помилки конфігурації немає `build/`, `downloads/` і `dist/`, а клас `TestBuildCommandOutput` з фікстурами `externals` і `generate_exe` будує з підмінами, без мережі. `test_project_name_slug_underscore`, `test_project_name_slug_dash` і `test_dist_name` (`tests/test_types.py:152-192`) створюють `BuildConfig` напряму з іменами `My Test Project` і `My App`. Решта імен і версій у тестах і прикладах правильні: `test-app`, `hello-script`, `system-monitor`, `0.1.0` тощо.

## Рішення

1. **Де.** Перевірки стоять у `from_pyproject_toml` одразу після перевірок, що `name` і `version` є (`types.py:294-298`), у порядку тип → ім'я → версія, для обох режимів: збірка падає в обох. Так `build` зупиняється ще до `prepare_directories`. Модель `BuildConfig` формату цих значень не перевіряє, як і решти полів `[project]`, тож тести slug-ів з `My Test Project` не змінюються.
2. **Тип.** Значення, що не є рядком, → `ValueError`: `'name' in [project] must be a string, got int`, для `version = 1.0` — `'version' in [project] must be a string, got float`. Ця перевірка перша, бо packaging на не-рядку кидає `TypeError`.
3. **Ім'я.** `canonicalize_name(name, validate=True)`; `InvalidName` → `ValueError`:

   ```text
   Invalid name in [project]: 'System Monitor'. A name may contain only ASCII letters, digits, '-', '_' and '.' and must start and end with a letter or digit; try 'system-monitor'.
   ```

   Підказка — `slugify(name, separator="-")`, той самий slug, за яким PyRetort називає exe і теки, тож із нею збірка дасть ті самі імена. Коли slug порожній (`!!!`, порожнє ім'я), речення закінчується на `…with a letter or digit.` без `; try …`. `project_name` лишається таким, як у `pyproject.toml`: нормалізоване ім'я ніде не використовується.
4. **Версія.** `Version(version)`; `InvalidVersion` → `ValueError`:

   ```text
   Invalid version in [project]: '1.0 beta'. Use a PEP 440 version such as '1.0.0' or '1.0b1'.
   ```

   `project_version` лишається рядком з `pyproject.toml`, без нормалізації: з нього складається `dist_name`, тож `1.0-beta` і далі дає `test-app-1.0-beta-amd64`.
5. **Залежність.** `packaging>=21.0` → `packaging>=23.2` у `[project].dependencies`, бо код починає використовувати `validate` (журнал рішень, «Оновлення залежностей»), потім `uv lock`. Межа піднімається тим самим комітом, що й перевірка імені.
6. **Документація.**
   - README, Troubleshooting, два пункти після пункту про `main_file`:
     - `Invalid name in [project]: '…'. …` → uv приймає лише ім'я з ASCII-літер, цифр, `-`, `_` і `.`, що починається й закінчується літерою чи цифрою. Exe і теки PyRetort однаково називає за ім'ям у нижньому регістрі з дефісами (`System Monitor` дало б `system-monitor.exe`), тож запропоноване ім'я збирає той самий застосунок;
     - `Invalid version in [project]: '…'. …` → версія за PEP 440, наприклад `1.0.0` чи `1.0b1`.
   - CHANGELOG `[Unreleased]`, `### Fixed`: `check` приймав `[project].name` чи `version`, які відкидає uv (наприклад `System Monitor` чи `1.0 beta`), а `build` падав на кроці uv, уже видаливши попередню збірку; тепер обидві команди повідомляють про це до збірки.

## Сіми

- `BuildConfig.from_pyproject_toml` з `tmp_path`, як у `tests/test_types.py`.
- CLI `check` і `build` через `CliRunner`, як у `tests/cli/test_check.py` і `tests/cli/test_build.py`.

## Кроки

Кожен крок: тест → червоний → мінімальна зміна → `uv run pytest` зелений → далі. Тест, що проходить одразу, перевіряють тимчасовим мутантом (журнал рішень, «Тест, що проходить одразу, перевіряють мутантом»).

1. `test_from_pyproject_rejects_non_string_project_name_and_version` (`tests/test_types.py`), параметризований:
   - `name = 123` → `'name' in [project] must be a string, got int`;
   - `version = 1.0` → `'version' in [project] must be a string, got float`;
   - решта конфігурації — standalone, як у `test_from_pyproject_rejects_invalid_requires_python_in_standalone_mode`, з `main.py`;
   - зараз падає: повідомлення pydantic інше;
   - зміна: рішення 1 і 2.
2. `test_from_pyproject_rejects_invalid_project_name` (`tests/test_types.py`, як і тести кроків 3–5), параметризований повними повідомленнями з рішення 3:
   - `System Monitor` → `…; try 'system-monitor'.`;
   - `Монітор` → `…; try 'monitor'.`;
   - `my-app-` → `…; try 'my-app'.`;
   - `!!!` → без `; try …`;
   - зміна: рішення 3 і 5.
3. `test_from_pyproject_accepts_unusual_valid_project_name`: `My_App.v2` → `config.project_name == "My_App.v2"`, `config.dist_name == "my-app-v2-0.1.0-amd64"`. Проходить одразу; мутант — тимчасово відкидати великі літери.
4. `test_from_pyproject_rejects_invalid_project_version`, параметризований: `1.0 beta` і `latest` → повідомлення з рішення 4 зі своїм значенням. Зміна: рішення 4.
5. `test_from_pyproject_keeps_project_version_as_written`: `1.0-beta` → `config.project_version == "1.0-beta"`, `config.dist_name == "test-app-1.0-beta-amd64"`. Проходить одразу; мутант — `str(Version(version))` замість рядка з файлу (дає `1.0b0`).
6. `test_check_rejects_invalid_project_name` (`tests/cli/test_check.py`): standalone-проєкт, як у `test_check_accepts_standalone_mode`, з `name = "System Monitor"` → код 1, у виводі `Configuration validation failed: Invalid name in [project]: 'System Monitor'.`, немає `is valid`. Проходить одразу; мутант — прибрати перевірку імені.
7. `test_build_rejects_invalid_project_name_before_building` (`tests/cli/test_build.py`, клас `TestBuildCommandOutput`): той самий проєкт → код 1, у виводі `Invalid configuration: Invalid name in [project]: 'System Monitor'.`, немає `Traceback`, немає `build/`, `downloads/` і `dist/`. Проходить одразу; мутант — прибрати перевірку імені: підмінена збірка тоді проходить і створює `build/`. Фікстури класу не пускають мутанта в мережу.
8. Документація (рішення 6).
9. Ручна перевірка: скопіювати `main.py`, `helper.py` і `pyproject.toml` з `examples/hello-script` у тимчасову теку поза репозиторієм.
   - `name = "Hello Script"`: `uv run pyretort check -p <копія>\pyproject.toml` → код 1 і `try 'hello-script'`; `uv run pyretort build -p <копія>\pyproject.toml` → код 1, тека `build\` у копії не з'явилася.
   - `name = "hello-script"`, `version = "1.0 beta"`: `check` → код 1 і повідомлення з рішення 4.
   - `version = "0.1.0"`: `check` → `is valid`.
10. Критерій завершення.

## Критерій завершення

- Тести з кроків 1–7 існують під цими назвами й проходять; ті, що пройшли одразу, червоніли з мутантом.
- `pyproject.toml` вимагає `packaging>=23.2`, `uv lock --check` завершується з кодом 0.
- Ручна перевірка з кроку 9 дала очікувані коди й повідомлення.
- README і CHANGELOG оновлено (рішення 6).
- Чотири команди з [README.md](README.md) зелені.
- Статус задачі в [README.md](README.md) → DONE.

## Поза межами

- `[project].dependencies` та інші поля `[project]`: PyRetort їх не читає, а помилки в них ловлять `uv sync` і `uv add` ще до збірки.
- Нормалізація імені чи версії: імена файлів збірки не змінюються.
- Перевірка імені в `init`: він лише шукає теку джерел за slug, а про погане ім'я скаже `check`, який README радить запустити наступним.
- Тести slug-ів з `My Test Project` і `My App` (рішення 1).
- Власна назва exe — ідея [build-exe-name](ideas.md#build-exe-name). Збереження попередньої збірки, коли нова падає, — ідея [build-keeps-previous-on-failure](ideas.md#build-keeps-previous-on-failure).

## Коміти

- `fix(config): require the project name and version to be strings`
- `fix(config): reject a project name that uv rejects`
- `fix(config): reject a project version that uv rejects`
- `test(cli): stop check and build at an invalid project name`
- `docs: explain the project name and version errors`

## Джерела

- Names and normalization: https://packaging.python.org/en/latest/specifications/name-normalization/
- Version specifiers (PEP 440): https://packaging.python.org/en/latest/specifications/version-specifiers/
- packaging, `canonicalize_name` і `InvalidName` (параметр `validate` — з 23.2): https://packaging.pypa.io/en/stable/utils.html
- packaging, CHANGELOG (26.3: `InvalidVersion` замість `TypeError` на не-рядку): https://github.com/pypa/packaging/blob/main/CHANGELOG.rst
- Задача 12, факт 6: https://github.com/ruslan-rv-ua/PyRetort/blob/v0.2.0/docs/tasks/12-standalone-mode.md
