# 12. Standalone-режим: збірка без встановлення пакета

Залежить від: 11. Оцінка: M.

## Мета

`install_as_package = false` збирає проєкт, який не встановлюється як пакет: джерела з `project_source_subdir` копіюються в теку застосунку, залежності з `[project].dependencies` ставляться у вбудований Python, а лаунчер запускає `main_file` як скрипт. Режим для проєктів без `__main__.py` і без build-backend, зокрема створених `uv init` без `--package`. Новий приклад `examples/hello-script` показує такий проєкт.

## Контекст

Функції й тести названо станом на коміт `f6a7b60`; номерів рядків задача не наводить.

**Що є зараз.**

- `UVBuilder._build_as_standalone` (`src/pyretort/builder/uv_builder.py`) кидає `NotImplementedError`. `_build_as_package` сам встановлює embedded Python, викликає uv і пише лаунчер, перекладаючи помилки кожного кроку в `BuildError`.
- `BuildConfig.from_pyproject_toml` (`src/pyretort/types.py`):
  - відхиляє `install_as_package = false` повідомленням «not supported yet» (задача 04). Це перевіряють три тести: `test_from_pyproject_rejects_standalone_mode` (`tests/test_types.py`), `test_check_rejects_standalone_mode` (`tests/cli/test_check.py`) і `test_build_rejects_standalone_mode_without_traceback` (`tests/cli/test_build.py`);
  - вимагає `[build-system]` і для будь-якого режиму перевіряє точку входу `python -m`;
  - перевіряє існування `main_file` відносно `project_source_subdir` лише для `install_as_package = false` (задача 14).
- `BuildConfig.build_backend: str` — обов'язкове поле, яке ніхто не читає.
- `DEFAULT_BLACKLIST` (`src/pyretort/constants.py`) ще ніде не використовується.
- `PydistManager.patch_pth_file(version, relative_path_to_source)` пише `._pth` з рядків `python3XX.zip`, переданого шляху і `import site`; режим пакета передає `"."`.
- `init` пише над `install_as_package` коментар «Must be true: standalone mode (false) is not supported yet». Той самий рядок стоїть у `examples/hello-cli/pyproject.toml`, а `test_init_comments_explain_install_as_package_and_main_file` перевіряє його.
- README проєкту: рядки `install_as_package` і `main_file` таблиці Configuration та пункт «Package mode only» розділу Limitations називають standalone-режим запланованим; Quick start і How it works описують лише режим пакета.
- Лаунчер із задачі 15 запускає команду без `cmd.exe`, допускає кілька шляхів у лапках і не змінює робочу теку; довжина команди — до 1023 одиниць UTF-16.

**Перевірено 8 жовтня 2026** на embedded Python 3.13.9 з `examples/Simple RSS/downloads` і uv 0.12.23 (`uv pip install --offline`, пакети з кешу uv):

1. Будь-який `._pth` вмикає ізольований режим: `sys.flags.isolated == 1`, `sys.flags.safe_path is True`. Документація це підтверджує: `._pth` вмикає isolated mode, а в ньому `sys.path` не містить теки скрипта. Тому `python.exe <тека>\main.py` **не** додає теку скрипта в `sys.path`, і `import helper` сусіднього `helper.py` падає з `ModuleNotFoundError`. Рядок із цією текою в `._pth` лагодить імпорт; шляхи в `._pth` відносні до його теки, `..` дозволено. Тека стає в `sys.path` після `python3XX.zip` і теки Python та перед `Lib\site-packages`. Рядок `.` потрібен і далі: у теці Python лежать `.pyd` стандартної бібліотеки.
2. `uv pip install --python <embedded python.exe> -r <тека>\pyproject.toml` ставить лише `[project].dependencies`: ні сам проєкт, ні `[dependency-groups]` не встановлюються. Команда працює без `[build-system]`, з `readme`, що вказує на відсутній файл, і з `[build-system]` (hatchling): статичні залежності uv читає без збірки.
3. `dependencies = []` і `[project]` без ключа `dependencies` → код 0, нічого не встановлено.
4. `dynamic = ["dependencies"]` без `[build-system]` → код 0, нічого не встановлено, без попередження.
5. `requires-python = ">=3.14"` при embedded 3.13.9 → код 0: з `-r` uv не звіряє `requires-python` з інтерпретатором. Встановлення теки проєкту (режим пакета) за тієї ж розбіжності завершується кодом 1: `No solution found … does not satisfy Python>=3.14`.
6. uv відкидає `[project].name` з пробілом (`Not a valid package or extra name: "Probe App"`): з `-r pyproject.toml` — код 2, під час встановлення теки проєкту — код 1. `check` таке ім'я зараз пропускає.
7. `shutil.ignore_patterns(*DEFAULT_BLACKLIST)` на Windows порівнює лише імена, не шляхи, і без урахування регістру. Він відкидає `icons` і `Icons` (через шаблон `Icon?`), `dist`, `build`, `env`, `ci` на будь-якій глибині, а також `native.dll` і `ext.pyd`; лишає `downloads` і `tests`. Шаблони `docker/*` і `docs/_build` не спрацьовують ніколи.

**Що змінилося проти першої версії цієї задачі.**

- Перша версія розраховувала, що теку скрипта в `sys.path` додасть сам Python, а це хибно (факт 1).
- Її e2e-сценарій імпортував лише залежність із site-packages, тож цієї помилки не помітив би.
- Тека джерел `build/<dist_name>/app/` лежала поруч із `build/<dist_name>/<slug-dash>/` і для проєкту з назвою `app` збігалася з нею.
- Вибір режиму в `init` і приклад SystemMonitor винесено в задачі 21 і 22.

## Рішення

1. **Розкладка.**
   ```text
   build/<dist_name>/
   ├── <slug-dash>.exe        лаунчер
   └── <slug-dash>/           embedded Python, Lib\site-packages із залежностями
       └── app/               копія project_source_subdir
   ```
   Зверху, як і в режимі пакета, — exe і одна тека; за будь-якої назви проєкту імена не конфліктують.
2. **Валідація** в `from_pyproject_toml`, коли `install_as_package = false`:
   - тип `install_as_package` перевіряється раніше за `[build-system]`, бо від режиму залежить, чи `[build-system]` потрібен;
   - `[build-system]` не потрібен і не читається. `build_backend` стає `str | None = None` і в standalone-режимі завжди `None`; у режимі пакета перевірки `[build-system]` не змінюються;
   - без `main_file`: `Standalone mode (install_as_package = false) requires 'main_file' in [tool.pyretort]`;
   - `main_file` поза `project_source_subdir`, наприклад `../main.py`: `Main file must be inside the source subdirectory: ../main.py`. Перевірки «does not exist» і «is not a file» лишаються;
   - перевірка точки входу `python -m` (`__main__.py`) не виконується;
   - `"dependencies"` у `[project].dynamic` (факт 4): `Standalone mode installs [project].dependencies; 'dependencies' in [project].dynamic is not supported`;
   - якщо в `[project]` є `requires-python`, `python_version` мусить йому відповідати (факт 5; `packaging.specifiers.SpecifierSet`): `python_version 3.13.9 does not satisfy requires-python '>=3.14' in [project]`. Невалідний специфікатор: `Invalid requires-python in [project]: '<значення>'`;
   - повідомлення «not supported yet» видаляється.
3. **Порядок збірки.** `_build_as_standalone` виконує кроки так: embedded Python → `._pth` → копія джерел → залежності → лаунчер. Копія йде перед uv, щоб локальна помилка (зайнятий файл) виявилася до повільного кроку. Спершу окремий рефакторинг без зміни поведінки виносить із `_build_as_package` у приватні методи `UVBuilder` спільні з режимом пакета кроки:
   - встановлення embedded Python з перекладом помилок httpx;
   - виклик `uv pip install` з перекладом `CalledProcessError`;
   - `generate_exe` з перекладом `ValueError`.
4. **Копіювання:** `shutil.copytree(project_dir / project_source_subdir, <slug-dash>/app, ignore=<функція>)`. Функція зіставляє імена через `fnmatch`, як `ignore_patterns` (на Windows без урахування регістру), за двома списками з `constants.py`:
   - `PROJECT_ROOT_EXCLUDES` (новий) діє лише на елементи, що лежать безпосередньо в теці проєкту. До нього входять теки самого PyRetort (`BUILD_DIR_DEFAULT`, `DIST_DIR_DEFAULT`, `DOWNLOAD_DIR_DEFAULT`), а також `venv`, `env` і `ci`. Глибше теки з такими іменами копіюються, наприклад `ui/dist/` зібраного фронтенду. Коли `project_source_subdir` не `.`, копія починається нижче кореня, і цей список не спрацьовує;
   - `DEFAULT_BLACKLIST` діє на будь-якій глибині. З нього прибрати:
     - `*.pyd`, `*.dll`, `*.so`, `*.dylib` — це бінарні модулі й бібліотеки застосунку, наприклад для `ctypes`;
     - `Icon?` — відкидає `icons/`;
     - `build`, `dist`, `venv`, `env`, `ENV`, `ci` — переходять у `PROJECT_ROOT_EXCLUDES`;
     - `docker/*` і `docs/_build` — ніколи не спрацьовують.

     Додати `tests`: тести застосунку в дистрибутиві не потрібні. `uv.lock` у списку вже є. Коментар над списком пояснює, де і як він діє;
   - помилка копіювання (`OSError`, зокрема `shutil.Error`) → `BuildError`: `Could not copy the sources to <тека app>: <помилка>`;
   - лог: `Copying sources to <тека app>`.
5. **Залежності:** `uv pip install --python <embedded python.exe> -r <project_dir>\pyproject.toml` і більше нічого (факт 2). Порожні залежності окремо не обробляються (факт 3).
   - Лог: `Installing dependencies with uv`. Помилка — те саме повідомлення, що в режимі пакета (`uv pip install failed with exit code …`).
   - Коментар біля виклику одним реченням фіксує факт 2.
   - Файл конфігурації з іншою назвою (`-p other.toml`) не підтримується — як і в режимі пакета, де uv читає `pyproject.toml` теки проєкту.
6. **`._pth`.** Сигнатура стає `patch_pth_file(version: str, extra_paths: Sequence[str] = ())`, docstring описує вміст файлу.
   - Метод завжди пише `python3XX.zip` і `.`, потім `extra_paths`, потім `import site`.
   - Режим пакета викликає його без `extra_paths`, тож вміст його `._pth` не змінюється.
   - Standalone передає теку, де лежить `main_file`, відносно теки Python і через `\`: `app` для `main.py`, `app\scripts` для `scripts/run.py`. Так поводиться `sys.path[0]` у звичайному Python (факт 1).
7. **Лаунчер:** `"{EXE_DIR}\<slug-dash>\python.exe" "{EXE_DIR}\<slug-dash>\app\<main_file через \>"`, наприклад `"{EXE_DIR}\my-app\python.exe" "{EXE_DIR}\my-app\app\main.py"`. Робоча тека не змінюється: консольні програми отримують відносні шляхи від теки, з якої їх запустили. README радить відкривати файли поруч зі скриптом через `Path(__file__).parent`.
8. **Коментар `init`** над `install_as_package` стає `true: install the project as a package and run python -m <module>; false: copy sources and run main_file as a script`; той самий рядок — у `examples/hello-cli/pyproject.toml`. Вибір режиму в `init` — задача 21.
9. **e2e:** другий сценарій у `tests/test_e2e_build.py` — проєкт `hello-script` без `[build-system]`, з `project_source_subdir = "."`, `main_file = "main.py"`, `install_as_package = false`, `dependencies = ["six"]`.
   - `main.py` імпортує сусідній `helper.py` і `six` і, як `HELLO_APP_INIT`, пише маркер із `helper.VALUE` і `six.__version__`.
   - Сусідній модуль обов'язковий: без нього сценарій пройшов би і з помилкою з факту 1.
   - Архів Python береться з того самого `PYRETORT_E2E_DOWNLOAD_DIR`.
10. **Приклад `examples/hello-script`** — консольна програма, як `hello-cli`, але без пакета:
    - `pyproject.toml`: `name = "hello-script"`, `version = "0.1.0"`, `requires-python = ">=3.13"`, без `[build-system]`. Одна залежність — `rich` з нижньою межею на версії, з якою приклад перевірено. `[tool.pyretort]` з коментарями, які пише `init`:
      - `project_source_subdir = "."`, `main_file = "main.py"`, `install_as_package = false`;
      - `python_version = "3.13.16"` (як у hello-cli), `python_architecture = "amd64"`;
      - `show_console_window = true`, `create_dist_zip_file = true`;
    - `main.py` бере текст привітання з `helper.py` і друкує через `rich` таблицю: версію Python, шлях до скрипта, аргументи;
    - `README.md` за зразком `examples/hello-cli/README.md`: що показує приклад, Build, Run з очікуваним виводом, Clean up;
    - розділ у `examples/README.md`.
11. **Документація.** README проєкту:
    - Configuration: рядки `install_as_package` (обидва значення), `main_file` (обов'язковий при `false`, відносно `project_source_subdir`) і `project_source_subdir` (у standalone-режимі — тека, вміст якої копіюється; `"."` — корінь проєкту без виключених файлів);
    - новий підрозділ `### Standalone mode` у Configuration: коли обирати, приклад `[tool.pyretort]`, що копіюється і що виключається (рішення 4), `Path(__file__).parent`;
    - How it works: варіант кроків для standalone-режиму — копія в `<name>\app`, `uv pip install -r pyproject.toml`, рядок у `._pth`, команда лаунчера;
    - Quick start: одне речення про те, що проєкт без пакета (наприклад, після `uv init`) збирається в standalone-режимі, з посиланням на підрозділ; кількість прикладів — три;
    - Limitations: замість «Package mode only» — що standalone-режим копіює лише `project_source_subdir`; «No code protection» згадує і `<name>\app`;
    - Troubleshooting: повідомлення про обов'язковий `main_file`.

    CHANGELOG `[Unreleased]`, `### Added`: standalone-режим і приклад hello-script.

## Сіми

- `BuildConfig.from_pyproject_toml` — валідація режиму.
- `PydistManager.patch_pth_file` — вміст `._pth`.
- `UVBuilder.build()` з фікстурами `externals` і `generate_exe` з `tests/conftest.py`: вони підміняють `PydistManager`, `subprocess.run`, `shutil.which` і `generate_exe`. `copytree` справжній, у `tmp_path`. `fake_pydist_manager` делегує `patch_pth_file` справжньому `PydistManager`, щоб тест читав `._pth` з `tmp_path`.
- CLI `check`, `build`, `init` через `CliRunner`; e2e — як у задачі 07.

## Кроки

1. `uv run pytest` зелений до змін.
2. Рефакторинг `UVBuilder` (рішення 3) → `uv run pytest` зелений.
3. `patch_pth_file` (рішення 6): новий `test_patch_writes_extra_paths_after_dot` і переписаний під нову сигнатуру `TestPydistManagerPatchPthFile`; тести режиму пакета лишаються зеленими без змін.
4. Валідація (рішення 2), по зрізу на тест:
   - `test_from_pyproject_accepts_standalone_mode` замість `test_from_pyproject_rejects_standalone_mode`: без `[build-system]` і без `__main__.py`, `build_backend is None`;
   - `test_from_pyproject_requires_main_file_in_standalone_mode`;
   - `test_from_pyproject_rejects_main_file_outside_source_dir_in_standalone_mode`;
   - `test_from_pyproject_rejects_dynamic_dependencies_in_standalone_mode`;
   - `test_from_pyproject_rejects_python_version_outside_requires_python_in_standalone_mode`;
   - `test_check_accepts_standalone_mode` замість `test_check_rejects_standalone_mode`;
   - `test_build_reports_missing_main_file_without_traceback` замість `test_build_rejects_standalone_mode_without_traceback`: код 1, повідомлення, без трейсбека, `build/` і `downloads/` не створено.
5. Збірка (рішення 1, 4, 5, 7) — новий клас `TestUVBuilderStandalone` у `tests/test_uv_builder.py`, по зрізу на тест:
   - `test_standalone_build_copies_sources_into_app_dir`: `main.py`, `lib/native.dll`, `lib/ext.pyd`, `icons/app.png`, `ui/dist/index.html` є в `build/my-app-0.1.0-amd64/my-app/app/`;
   - `test_standalone_build_skips_junk_at_any_depth`: `__pycache__/`, `pkg/__pycache__/`, `.venv/`, `tests/`, `pkg/tests/` в `app/` немає;
   - `test_standalone_build_skips_pyretort_dirs_in_project_root`: `build/`, `dist/`, `downloads/`, `venv/` з кореня проєкту в `app/` немає;
   - `test_standalone_build_installs_only_dependencies`: `subprocess.run` отримав рівно `["uv", "pip", "install", "--python", <python.exe>, "-r", <project_dir>\pyproject.toml]`;
   - `test_standalone_build_adds_main_file_dir_to_pth`: у `._pth` є рядок `app`, а для `main_file = "scripts/run.py"` — `app\scripts`;
   - `test_standalone_launcher_runs_main_file_as_script`: команда для `generate_exe` дорівнює `"{EXE_DIR}\my-app\python.exe" "{EXE_DIR}\my-app\app\main.py"`;
   - `test_standalone_build_reports_copy_failure`: джерело відкрите через `win32file.CreateFile` без спільного доступу, як у `test_build_reports_locked_archive`, → `BuildError` `Could not copy the sources`.
6. Коментар `init` (рішення 8): спершу оновити `test_init_comments_explain_install_as_package_and_main_file`, потім код і `examples/hello-cli/pyproject.toml`.
7. e2e (рішення 9) → `uv run pytest -m e2e` зелений.
8. Приклад (рішення 10): `uv run pyretort check` і `uv run pyretort build` з `-p examples/hello-script/pyproject.toml`, потім `hello-script.exe arg1 "two words"` — вивід збігається з README прикладу.
9. Документація (рішення 11).
10. Критерій завершення.

## Критерій завершення

- Тести з кроків 3–6 проходять; `uv run pytest -m e2e` — обидва сценарії зелені.
- `examples/hello-script` збирається, а `hello-script.exe` друкує те, що показує його README.
- `git grep -n "not supported yet" -- src tests examples README.md` нічого не знаходить; README не називає standalone-режим запланованим.
- Чотири команди з [README.md](README.md) зелені.
- Статус задачі в [README.md](README.md) → DONE.

## Поза межами

- Вибір режиму в `init` і `cli.py` серед кандидатів на `main_file` — задача 21.
- Приклад SystemMonitor — задача 22.
- Власні шаблони виключень, перевірка імені проєкту за PEP 508, збірка за `uv.lock` — розділ «Ідеї після 0.1» в [README.md](README.md).
- `requires-python` у режимі пакета: там розбіжність виявляє uv під час встановлення проєкту (факт 5).

## Коміти

- `refactor(builder): extract the steps both build modes share`
- `refactor(builder): pass extra paths to patch_pth_file`
- `feat(config): accept standalone mode`
- `feat(builder): implement standalone build mode`
- `feat(init): describe both values of install_as_package`
- `test: add standalone end-to-end scenario`
- `docs(examples): add hello-script`
- `docs: document standalone mode`

## Джерела

- `._pth` вмикає isolated mode: https://docs.python.org/3/library/sys_path_init.html#pth-files
- Isolated mode, опція `-I`: https://docs.python.org/3/using/cmdline.html#cmdoption-I
- Python embeddable package: https://docs.python.org/3/using/windows.html#the-embeddable-package
- uv, встановлення з `pyproject.toml`: https://docs.astral.sh/uv/pip/packages/
- uv, проєкти-застосунки без `[build-system]`: https://docs.astral.sh/uv/concepts/projects/init/
- `shutil.copytree`: https://docs.python.org/3/library/shutil.html#shutil.copytree
- `fnmatch`: https://docs.python.org/3/library/fnmatch.html
- `packaging.specifiers`: https://packaging.pypa.io/en/stable/specifiers.html
