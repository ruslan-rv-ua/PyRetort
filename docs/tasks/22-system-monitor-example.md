# 22. Приклад SystemMonitor: GUI-застосунок у standalone-режимі

Залежить від: 12, 24. Оцінка: M.

## Мета

`examples/SystemMonitor` — GUI-застосунок на FastAPI, uvicorn і pywebview, який показує завантаження процесора й пам'яті. Він збирається в standalone-режимі і запускається на Windows без встановленого Python. Приклад доповнює `hello-script` (консольний приклад із задачі 12): тут GUI-застосунок без пакета і з важкими залежностями.

## Контекст

- Приклад видалено в задачі 10 (коміт `613df48`), відновлюється командою `git checkout 3f3e0f4 -- examples/SystemMonitor`. На `3f3e0f4` у ньому три файли:
  - `app.py` — один файл. FastAPI-сервер на `127.0.0.1:9999` працює у фоновому потоці, поруч відкривається вікно pywebview на весь екран (`fullscreen=True`). Сторінку (htpy) оформлено Bootstrap 5.3.3, а бандл datastar підтягується з CDN; сигнали CPU і пам'яті оновлюються через SSE (`datastar_py.fastapi`);
  - `pyproject.toml`:
    - `name = "System Monitor"`, `readme = "README.md"` (файлу немає), `requires-python = ">=3.13"`;
    - шість залежностей із нижніми межами: `datastar-py>=0.6.5`, `fastapi>=0.119.0`, `htpy>=25.10.0`, `psutil>=7.1.0`, `pywebview>=6.0`, `uvicorn>=0.37.0`;
    - `[dependency-groups] dev = ["pytest>=8.4.2"]`, `[build-system]` немає;
  - `pyretort.toml` — конфігурація старого, покинутого формату.
- Перевірено 8 жовтня 2026 (задача 12, факт 6): uv відкидає `name = "System Monitor"` з `Not a valid package or extra name`. Без перейменування `uv pip install -r pyproject.toml` завершується кодом 2.
- Ризики, через які приклад винесено із задачі 12:
  - pywebview на Windows відкриває вікно через WinForms і WebView2, а до .NET звертається через pythonnet. Чи працює pythonnet у вбудованому Python з `._pth`, не перевірено;
  - бандл datastar береться з `https://cdn.jsdelivr.net/gh/starfederation/datastar@main/bundles/datastar.js`, тобто з гілки `main`, а не з релізу: шлях і API можуть змінитися й розійтися з `datastar-py`;
  - з нижніми межами збірка ставить найновіші версії залежностей (задача 12, рішення 5: `uv.lock` не використовується);
  - під час роботи застосунку потрібні інтернет (CDN) і вільний порт 9999.

## Рішення

1. Відновити приклад, видалити `pyretort.toml` і секцію `[dependency-groups]`: тестів у прикладі немає.
2. `pyproject.toml`:
   - `name = "system-monitor"`; exe і тека, як і раніше, називаються `system-monitor` (`slugify` дає те саме);
   - `description` лишається;
   - залежності фіксуються через `==` на версіях, з якими приклад перевірено (крок 5);
   - `[tool.pyretort]` у форматі, який пише `init`: `project_source_subdir = "."`, `main_file = "app.py"`, `install_as_package = false`, `python_version = "3.13.16"` (як у hello-cli і hello-script), `python_architecture = "amd64"`, `show_console_window = false`, `create_dist_zip_file = true`.
3. `app.py`: URL бандла datastar фіксується на тезі того релізу datastar, з яким сумісна зафіксована версія `datastar-py`. Її README показує такий URL: 8 жовтня 2026 це `https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0-RC.7/bundles/datastar.js`. Решта коду не змінюється. Якщо найновіші версії залежностей із кодом несумісні, фіксуються останні сумісні.
4. `README.md` прикладу, за зразком `examples/hello-cli/README.md`: що показує приклад, Build, Run і Clean up. У Run пояснити, що потрібні інтернет і вільний порт 9999, а вікно на весь екран закривається Alt+F4. Тепер поле `readme` у `pyproject.toml` вказує на наявний файл.
5. Розділ у `examples/README.md`. У README проєкту речення про кількість прикладів у Quick start — чотири. CHANGELOG `[Unreleased]`, `### Added`: приклад SystemMonitor.
6. Якщо зібраний застосунок не запускається через pythonnet або WebView2 у вбудованому Python, PyRetort у цій задачі не латається. Симптом записується в розділ «Результат» цієї задачі, а далі зупинитися й обговорити з користувачем: окрема задача на ядро або інший GUI-тулкіт для прикладу.

## Сіми

Нових автоматичних тестів немає. Приклад перевіряється збіркою і ручним запуском, як Simple RSS у задачі 10.

## Кроки

1. Відновити приклад (рішення 1).
2. `pyproject.toml` (рішення 2, поки з нижніми межами) → `uv run pyretort check -p examples/SystemMonitor/pyproject.toml` з кодом 0.
3. `uv run pyretort build -p examples/SystemMonitor/pyproject.toml` з кодом 0.
4. Запустити `examples\SystemMonitor\build\system-monitor-0.1.0-amd64\system-monitor.exe`: відкривається вікно, де числа CPU і пам'яті оновлюються. Для діагностики можна тимчасово поставити `show_console_window = true`. Якщо не запускається — рішення 6.
5. Зафіксувати версії: `uv pip list --python examples\SystemMonitor\build\system-monitor-0.1.0-amd64\system-monitor\python.exe` показує встановлені версії шести прямих залежностей; записати їх через `==`.
6. Зафіксувати URL datastar (рішення 3), зібрати й запустити ще раз (кроки 3–4).
7. Документація (рішення 4–5).
8. Критерій завершення.

## Критерій завершення

- `check` і `build` для `examples/SystemMonitor/pyproject.toml` завершуються кодом 0.
- Зібраний `system-monitor.exe` відкриває вікно, де CPU і пам'ять оновлюються (ручна перевірка). Якщо він не запускається — спрацьовує рішення 6.
- `examples/SystemMonitor/pyretort.toml` немає; залежності зафіксовано через `==`; в URL datastar немає `@main`.
- Чотири команди з [README.md](README.md) зелені.
- Статус задачі в [README.md](README.md) → DONE.

## Поза межами

- Перевірка імені проєкту за PEP 508 у `check`: ідея [check-project-name](ideas.md#check-project-name).
- Локальна копія бандла datastar і Bootstrap замість CDN.

## Коміти

- `docs(examples): restore SystemMonitor as a standalone example`

## Джерела

- pywebview, вимоги на Windows: https://pywebview.flowrl.com/guide/installation.html
- datastar-py: https://github.com/starfederation/datastar-python

## Результат

Стан на 8 жовтня 2026, гілка `feature/22-system-monitor-example`: кроки 1, 2, 5, 6 і 7 виконано, крок 3 заблоковано ядром PyRetort, тому кроки 4 і 8 не виконано і статус лишається TODO.

**Симптом.** `uv run pyretort build -p examples/SystemMonitor/pyproject.toml` завершується кодом 1 на кроці «Installing dependencies with uv»:

```
error: Failed to download and build `proxy-tools==0.1.0`
  cause: Failed to create temporary virtualenv
  cause: failed to copy file from ...\system-monitor\python313.zip to C:\scoop\persist\uv\cache\builds-v0\.tmpXXXXXX\Scripts\python313.zip: Access is denied. (os error 5)
```

**Причина.** `proxy-tools` (залежність pywebview) лежить на PyPI лише як sdist, тож uv збирає його в тимчасовому venv від цільового інтерпретатора і для embedded Python копіює `python313.zip` у `Scripts\` того venv. `PydistManager._unzip_pythonzip_file` у `src/pyretort/builder/pydist_manager.py` розпаковує стандартну бібліотеку в **теку** з назвою `python313.zip`; копіювання теки як файлу і дає `Access is denied`. Навіщо розпаковувати, у коді не пояснено. Перевірено: з незайманим embedded Python (zip-файл на місці, `._pth` від PyRetort) `uv venv` і `uv pip install proxy-tools==0.1.0` проходять. `check` цього не ловить.

**Маскування кешем.** uv кешує зібране колесо, тому після будь-якої вдалої збірки `proxy-tools` на цій машині (хоч би у звичайному venv) `pyretort build` проходить і з текою: тимчасовий venv більше не потрібен. Відтворити падіння: `uv cache clean proxy-tools`, потім `build`. На чистій машині й у CI збірка впаде з першого разу.

**Що працює у вбудованому Python.** Експеримент: у зламаній збірці теку `python313.zip` замінено zip-файлом з архіву python.org, `uv pip install -r pyproject.toml` поставив 25 пакетів, застосунок запущено як `python.exe app\app.py` і як `pythonw.exe app\app.py` (так, без консолі, його запускає GUI-лаунчер через `CREATE_NO_WINDOW`). pythonnet 3.2.1 і WebView2 відкривають вікно «System Monitor» на весь екран, uvicorn слухає 9999, вікно саме запитує `/updates`, числа CPU і пам'яті оновлюються (перевірено й у Chromium-браузері). Ризики з розділу «Контекст» щодо pythonnet і WebView2 не підтвердилися.

**Відхилення від рішень.**

- Рішення 3: бандл зафіксовано на `@v1.0.4`, а не на `@v1.0.0-RC.7`. README datastar-py застарів: RC.7 вийшов 16 грудня 2025, а datastar-py 1.0.3 (27 вересня 2026) вийшов уже після datastar v1.0.4 (21 вересня 2026), яку рекомендує посібник data-star.dev. Протокол SSE (`datastar-patch-signals`) в обох бандлах однаковий.
- Рішення 3, «решта коду не змінюється»: `data_on_load` замінено на `data_init`. В обох бандлах, v1.0.4 і RC.7, плагіна `on-load` немає, є `init`; зі старим атрибутом сторінка не запитує `/updates` і назавжди показує 0.0%.
- Крок 5: версії взято з `uv pip list` вбудованого Python експерименту: datastar-py 1.0.3, fastapi 0.143.0, htpy 26.5.1, psutil 7.2.2, pywebview 6.2.1, uvicorn 0.54.0.

**Далі (рішення 6).** Потрібна окрема задача на ядро: лишати `python3XX.zip` файлом або розпаковувати в теку з іншою назвою і вписувати її в `._pth`, з тестом на sdist-залежність. Після неї — кроки 3, 4 і 8 цієї задачі: `build` з чистим кешем uv, запуск `system-monitor.exe`, статус DONE.
