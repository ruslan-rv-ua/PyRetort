# 24. Стандартна бібліотека вбудованого Python лишається файлом `python3XX.zip`

Залежить від: 12. Оцінка: S.

## Мета

`pyretort build` ставить у вбудований Python залежності, які на PyPI лежать лише як sdist, і збирає проєкти з будь-яким PEP 517 build-backend, а не тільки з `uv_build`. Для цього стандартна бібліотека вбудованого Python лишається файлом `python3XX.zip`, як її віддає python.org, а не розпаковується в теку з такою назвою. Після цієї задачі можна завершити задачу 22.

## Контекст

Факти станом на 8 жовтня 2026, uv 0.12.23. Знайдено під час задачі 22; подробиці експериментів у її розділі «Результат».

- `PydistManager.install_embedded_python` (`src/pyretort/builder/pydist_manager.py`) після розпакування архіву викликає `_unzip_pythonzip_file`: перейменовує `python3XX.zip` у `python3XX.temp_zip`, розпаковує його в **теку** з назвою `python3XX.zip` і видаляє тимчасовий файл. `patch_pth_file` пише в `._pth` рядок `python3XX.zip`, і для Python тека й файл тут рівнозначні. Навіщо розпаковувати, у коді не пояснено. Для 3.13.16 розпакована бібліотека — 541 файл, 8,6 МБ; файл з архіву — 3,7 МБ.
- uv збирає sdist-залежність або локальний проєкт за PEP 517 у тимчасовому venv від цільового інтерпретатора (тека `builds-v0` у `uv cache dir`). Для embedded Python він копіює `python3XX.zip` у `Scripts\` того venv. Тека замість файлу дає:

  ```
  error: Failed to download and build `proxy-tools==0.1.0`
    cause: Failed to create temporary virtualenv
    cause: failed to copy file from ...\python313.zip to ...\builds-v0\.tmpXXXXXX\Scripts\python313.zip: Access is denied. (os error 5)
  ```

  Те саме дає `uv venv --python <вбудований python.exe> <тека>`.
- Виняток — бекенд `uv_build`: його колеса uv будує сам, без Python і без venv. Тому hello-cli, Simple RSS і e2e-тести (усі на `uv_build`) проходять, а ті самі проєкти з `setuptools.build_meta` або `hatchling.build` падають з помилкою вище (перевірено `uv pip install --python <вбудований python.exe> <проєкт>`). Обіцянка README «any build backend works» і CHANGELOG 0.1.0 «Any PEP 517 build backend works» зараз не виконується. У standalone-режимі падає будь-яка залежність без колеса; перша зустрінута — `proxy-tools`, залежність pywebview.
- Маскування кешем: зібране колесо sdist-залежності uv кешує, тож після будь-якої вдалої збірки `proxy-tools` на машині (хоч би у звичайному venv) `pyretort build` проходить і з текою. Відтворення: `uv cache clean proxy-tools`, потім `build`. Локальний проєкт у новій теці (як e2e з `tmp_path`) uv будує щоразу, тому e2e-тест із бекендом, відмінним від `uv_build`, ловить помилку без чищення кешу.
- Із zip-файлом на місці перевірено в задачі 22: `uv venv` працює, `uv pip install -r pyproject.toml` ставить 25 пакетів разом із `proxy-tools`, застосунок на fastapi, pydantic-core, uvicorn, pywebview і pythonnet 3.2.1 запускається з `python.exe` і з `pythonw.exe`. Стандартний embeddable-дистрибутив python.org саме так і працює, зі стисненою бібліотекою.
- `Downloader.download` повертає файл із `downloads/`, якщо він там уже лежить, тож тест може підкласти штучний архів `python-3.13.0-embed-amd64.zip` і викликати `install_embedded_python` без мережі. Фікстури `pydist_dir`, `download_dir`, `downloader` і `pydist_manager` вже є в `tests/test_pydist_manager.py`.
- Тести, яких торкається зміна (`tests/test_pydist_manager.py`): `TestPydistManagerUnzipPythonzipFile` — два тести приватного методу; `TestPydistManagerInstallEmbeddedPython.test_install_calls_all_steps` мокає `_unzip_pythonzip_file`; `TestPydistManagerIntegration.test_install_real_python` (`slow`, `requires_network`) очікує `(pydist_dir / "python313.zip").is_dir()`. `tests/test_e2e_build.py` будує hello-app (`uv_build`) і hello-script (standalone, залежність `six` з колесом); `PYTHON_VERSION` там 3.13.9.

## Рішення

1. `install_embedded_python` більше не розпаковує `python3XX.zip`: виклик і метод `_unzip_pythonzip_file` видаляються разом із тестами на нього. Файл лишається таким, яким він є в архіві; `._pth`, як і раніше, перелічує `python3XX.zip`, `.`, `extra_paths` і `import site`, тож формат файлу і тести `patch_pth_file` не змінюються. Docstring `patch_pth_file` описує файл, а не теку.
2. Запасний варіант, лише якщо крок 5 покаже пакет, який не працює зі стисненою бібліотекою: розпаковувати в теку з іншою назвою (наприклад `python3XX`), вписувати її в `._pth` замість zip і видаляти zip. Перед вибором цього варіанту перевірити, що `uv venv --python` працює без `python3XX.zip`, бо uv може вимагати цей файл.
3. Новий e2e-тест у `tests/test_e2e_build.py`: той самий hello-app, але з `[build-system]` `requires = ["setuptools>=80"]`, `build-backend = "setuptools.build_meta"` (setuptools сам знаходить пакет у `src/`). Тест будує проєкт і запускає exe, як `test_build_produces_runnable_launcher`. Він єдиний у наборі змушує uv створити тимчасовий venv від вбудованого Python.
4. Тест без мережі на публічній межі `install_embedded_python` (сіми нижче).
5. Документація. README, розділ «How it works», крок 1: стандартна бібліотека лишається у `python<XY>.zip`, бо uv копіює цей файл у середовище, де збирає проєкт і sdist-залежності. CHANGELOG `[Unreleased]`, нова секція `### Fixed` після `### Added`: збірка проєкту з бекендом, відмінним від `uv_build`, і встановлення залежності без колеса падали з `Failed to create temporary virtualenv`, бо стандартна бібліотека вбудованого Python була розпакована в теку `python3XX.zip`.
6. Ручна перевірка, що стиснена бібліотека нічого не ламає: hello-cli, hello-script і Simple RSS збираються й запускаються (`uv run pyretort build -p ...`, потім exe). SystemMonitor перевіряється в задачі 22.

## Сіми

- `PydistManager.install_embedded_python` з `Downloader`, якому підкладено архів у `download_dir`: розкладка теки вбудованого Python після встановлення, без мережі.
- CLI `build` через `CliRunner` і запуск згенерованого exe у `tests/test_e2e_build.py` (маркери `slow`, `e2e`, `requires_network`, `windows`).
- `patch_pth_file` лишається під наявними тестами без змін.

## Кроки

1. Червоний: у `TestPydistManagerInstallEmbeddedPython` новий тест `test_install_keeps_stdlib_zip_as_file`. У `download_dir` лежить `python-3.13.0-embed-amd64.zip` з `python.exe` і `python313.zip`, вміст якого — справжній мініатюрний zip (один файл, зібраний через `ZipFile` в `io.BytesIO`). Після `install_embedded_python("3.13.0", PythonArchitecture.AMD64)` `pydist_dir / "python313.zip"` є файлом із тими самими байтами. Зараз падає: метод робить теку.
2. Зелений: прибрати виклик і метод `_unzip_pythonzip_file`, клас `TestPydistManagerUnzipPythonzipFile`, мок `_unzip_pythonzip_file` у `test_install_calls_all_steps`; у `test_install_real_python` замінити `is_dir()` на `is_file()`; оновити docstring `patch_pth_file`. `uv run pytest` зелений.
3. e2e: константа `SETUPTOOLS_PYPROJECT`, фікстура `setuptools_project` і тест `test_build_with_setuptools_backend_produces_runnable_launcher` за рішенням 3. `uv run pytest -m e2e` з `PYRETORT_E2E_DOWNLOAD_DIR` на теку з `python-3.13.9-embed-amd64.zip` (наприклад `examples\Simple RSS\downloads`) — усі чотири тести зелені. Повільні тести `uv run pytest -m slow` теж зелені.
4. Документація (рішення 5).
5. Ручна перевірка (рішення 6). Якщо щось не працює зі стисненою бібліотекою — рішення 2.
6. Критерій завершення.

## Критерій завершення

- Тест з кроку 1, повільні тести й усі e2e-тести з кроку 3 зелені.
- Після `uv run pyretort build -p examples/hello-script/pyproject.toml` файл `examples\hello-script\build\hello-script-0.1.0-amd64\hello-script\python313.zip` існує і це файл, а `uv venv --python examples\hello-script\build\hello-script-0.1.0-amd64\hello-script\python.exe <тимчасова тека>` завершується кодом 0.
- Ручна перевірка трьох прикладів з рішення 6 вдалася.
- README і CHANGELOG оновлено (рішення 5).
- Чотири команди з [README.md](README.md) зелені.
- Статус задачі в [README.md](README.md) → DONE.

## Поза межами

- Завершення задачі 22: `build` SystemMonitor з чистим кешем uv (`uv cache clean proxy-tools`), запуск exe, статус DONE — окрема сесія після цієї задачі.
- Зменшення розміру дистрибутива понад те, що дає стиснена бібліотека: ідея в [ideas.md](ideas.md).
- Перевірка в `check`, що uv здатен створити venv від вбудованого Python.

## Коміти

- `fix(build): keep the standard library of the embedded Python in python3XX.zip`
- `test(e2e): build a project with the setuptools backend`
- `docs: explain the stdlib zip in how it works and record the fix`

## Джерела

- Python, embeddable package: https://docs.python.org/3/using/windows.html#the-embeddable-package
- uv, build backend (колеса `uv_build` uv будує без Python): https://docs.astral.sh/uv/concepts/build-backend/
- uv, кеш: https://docs.astral.sh/uv/concepts/cache/
- Задача 22, розділ «Результат»: [22-system-monitor-example.md](22-system-monitor-example.md)
