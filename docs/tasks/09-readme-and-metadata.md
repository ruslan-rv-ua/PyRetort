# 09. README, CHANGELOG, метадані пакета, подяка gen-exe

Залежить від: 06, 14 (щоб описувати реальну поведінку). Оцінка: M.

## Мета

Людина, яка відкрила репозиторій уперше, за п'ять хвилин розуміє, що це, для кого, як встановити і як зібрати перший застосунок. Пакет має повні метадані, історія змін ведеться, походження шаблону лаунчера вказане разом із ліцензією.

## Контекст

- `README.md` — 7 рядків: назва, одне речення і два службові рядки (URL `versions-manifest.json` і слово `python-embedded-launcher`), які треба прибрати.
- `pyproject.toml`: `description = "Add your description here"`, немає `keywords`, `classifiers`, `[project.urls]`. `license = {text = "MIT"}`, файл `LICENSE` є (коміт `811dada`).
- `CHANGELOG.md` немає. Історія для першого запису — `git log --oneline` від `4ed4aa3` (жовтень 2025) до поточного HEAD плюс задачі 01-08.
- Поведінка команд і поля конфігурації — як після задач 04-06: команди `version`, `init [--force]`, `check`, `build`, `cleanup`, спільна опція `-p/--pyproject-toml`, глобальна `--quiet`. Поля `[tool.pyretort]`: `python_version`, `python_architecture` (`amd64` | `win32` | `arm64`), `project_source_subdir`, `create_dist_zip_file`, `show_console_window` (default false), `install_as_package` (має бути `true`), `main_file` (ігнорується в режимі пакета), `icon_file_rel_path` (необов'язкове, `.ico`). Точні тексти брати з коду (`src/pyretort/types.py`, `src/pyretort/cli/commands/init.py`), а не з цього документа.
- Результат збірки: `build/<name>-<version>-<arch>/<name>.exe` плюс тека `<name>/` з вбудованим Python і site-packages; `dist/<name>-<version>-<arch>.zip`.
- Вимоги до машини розробника: Windows, Python ≥ 3.11 для самого PyRetort, `uv` у PATH (збірка викликає `uv pip install`).
- **Походження лаунчера.** `src/pyretort/builder/exe_generator/genexe_template` (123 392 байти) і код у `generate_exe.py` (`MAX_CMD_LENGTH = 259`, сигнатура-заповнювач із `X`, макрос `{EXE_DIR}`, прапорець консолі, `add_icon_to_exe` з `RT_GROUP_ICON`/`RT_ICON`) походять із пакета **gen-exe**: PyPI `gen-exe` 0.2.1 від 8 лютого 2021, автор S.C. (Sil) van de Leemput, ліцензія MIT, репозиторій https://github.com/silvandeleemput/gen-exe. Його README описує той самий механізм: exe з вбудованою командою, `{EXE_DIR}` як тека exe, прапорець приховування консолі (з 0.2.1), утиліта `add-icon-to-exe`. Ліцензія MIT вимагає зберігати текст ліцензії й копірайт при поширенні коду.

## Рішення

1. **README.md англійською** (аудиторія GitHub і PyPI), розділи в такому порядку: заголовок і одне речення; «Windows only»; Requirements; Installation (`uv tool install pyretort` після релізу та `uv tool install git+https://github.com/ruslan-rv-ua/PyRetort` з джерел); Quick start (три команди і що з'являється на диску); Configuration (таблиця полів: name, type, required, default, description); How it works (embedded Python + `._pth` + `uv pip install` у нього + лаунчер); Limitations (package mode only, no code protection, Windows only); Credits (gen-exe з посиланням на `THIRD_PARTY_LICENSES.md`); License. Бейдж CI з задачі 08 під заголовком.
2. **CHANGELOG.md** у форматі Keep a Changelog: `## [Unreleased]` з підрозділами Added/Changed/Fixed/Removed, заповнений за задачами 01-08 і історією git.
3. **THIRD_PARTY_LICENSES.md** у корені: розділ `gen-exe` з посиланням, копірайтом і повним текстом MIT з файлу `LICENSE` репозиторію gen-exe (скопіювати дослівно, дату та ім'я звідти).
4. **pyproject.toml**: `description = "Package Python projects into standalone Windows applications with an embedded Python"`, `keywords = ["windows", "packaging", "embedded-python", "exe", "launcher"]`, `classifiers` (`Development Status :: 3 - Alpha`, `Environment :: Console`, `Intended Audience :: Developers`, `License :: OSI Approved :: MIT License`, `Operating System :: Microsoft :: Windows`, `Programming Language :: Python :: 3`, `:: 3.11`, `:: 3.12`, `:: 3.13`, `Topic :: Software Development :: Build Tools`), `[project.urls]` Homepage, Repository, Issues, Changelog.
5. README описує лише те, що працює; майбутнє (standalone-режим, PyPI до релізу) позначено як «planned».

## Сіми

Тестів немає. Перевірки — збірка пакета, виконання кожної команди з README, перевірка посилань.

## Кроки

1. Підтвердити походження шаблону: `uv run --no-project --with gen-exe python -c "import genexe, pathlib, hashlib; p = pathlib.Path(genexe.__file__).parent; [print(f, hashlib.sha256(f.read_bytes()).hexdigest()) for f in p.rglob('*') if f.is_file() and f.stat().st_size > 100000]"` і порівняти з `(Get-FileHash src\pyretort\builder\exe_generator\genexe_template).Hash`. Результат (збіг чи ні) записати в `THIRD_PARTY_LICENSES.md` одним реченням.
2. Написати `THIRD_PARTY_LICENSES.md`, скопіювавши ліцензію з репозиторію gen-exe.
3. Написати README, виконуючи кожну команду з нього під час написання.
4. Написати CHANGELOG.
5. Заповнити метадані; `uv build` → у `dist/` є `.whl` і `.tar.gz`; `uv run --no-project --with dist/pyretort-0.1.0-py3-none-any.whl -- pyretort --help` працює. Видалити `dist/` після перевірки (у `.gitignore` він уже є).
6. Критерій завершення з [README.md](README.md).

## Критерій завершення

- README містить усі розділи з рішення 1; кожна команда з README реально виконана під час задачі.
- Є `CHANGELOG.md` і `THIRD_PARTY_LICENSES.md`.
- `uv build` проходить; у метаданих колеса видно опис, класифікатори й URL: `uv run --no-project --with dist/pyretort-0.1.0-py3-none-any.whl python -c "from importlib.metadata import metadata; print(metadata('pyretort'))"`.
- Чотири команди з README задач зелені; статус → DONE.

## Поза межами

Українська версія README — за бажанням пізніше. Сайт документації — ні.

## Коміти

- `docs: add third-party notice for the gen-exe launcher template`
- `docs: write README and changelog`
- `build: fill project metadata`

## Джерела

- gen-exe на PyPI: https://pypi.org/project/gen-exe/ ; репозиторій: https://github.com/silvandeleemput/gen-exe
- Keep a Changelog 1.1.0: https://keepachangelog.com/en/1.1.0/
- PyPI classifiers: https://pypi.org/classifiers/
- pyproject метадані (PyPA): https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- uv, build & publish: https://docs.astral.sh/uv/guides/package/
