# 17. Завантаження вбудованого Python: `BuildError` замість трейсбека

Залежить від: 09, 16. Оцінка: S.

## Мета

Коли `pyretort build` не може завантажити вбудований Python з python.org, бо такого архіву там немає або немає мережі, команда друкує зрозуміле повідомлення без трейсбека і завершується з кодом 1, як вимагає рішення 1 задачі 05.

## Контекст

Номери рядків — станом на коміт `c190f9a` (задача 09 код не змінювала).

- Рішення 1 задачі 05: «Усі передбачувані збої збірки кидають `BuildError` з повідомленням для людини». Задача 16 у розділі «Поза межами» відклала «інші винятки збірки (розпакування Python, мережа)» до окремої задачі, «якщо знадобиться». Це вона.
- Шлях завантаження:
  - `UVBuilder._build_as_package` ([`src/pyretort/builder/uv_builder.py:47-57`](../../src/pyretort/builder/uv_builder.py)) викликає `PydistManager.install_embedded_python`;
  - `PydistManager._download_embedded_python` ([`src/pyretort/builder/pydist_manager.py:48-53`](../../src/pyretort/builder/pydist_manager.py)) будує URL `https://www.python.org/ftp/python/<version>/python-<version>-embed-<arch>.zip`;
  - `Downloader._download_file` ([`src/pyretort/builder/downloader.py:51-76`](../../src/pyretort/builder/downloader.py)) качає через `httpx.stream(..., timeout=10.0, follow_redirects=True)` і викликає `raise_for_status()`; при `httpx.HTTPError` видаляє недокачаний файл і прокидає виняток далі;
  - `build_command` ([`src/pyretort/cli/commands/build.py:33-37`](../../src/pyretort/cli/commands/build.py)) ловить лише `BuildError`, решту Typer показує трейсбеком (код виходу теж 1).
- Знайдено 8 жовтня 2026 під час задачі 09, коли команди з README виконувалися одна за одною. Перевірено того ж дня на pyretort із `develop` (Python 3.13.15):
  - `python_version = "3.12.12"`: після рядка `Installing embedded Python 3.12.12 (amd64)` — трейсбек на 102 рядки, останній — `HTTPStatusError: Client error '404 Not Found' for url 'https://www.python.org/ftp/python/3.12.12/python-3.12.12-embed-amd64.zip'`, код 1;
  - без мережі (змінні `HTTPS_PROXY` і `HTTP_PROXY` вказують на закритий порт `http://127.0.0.1:9`, httpx їх читає), версія, якої немає в `downloads/`: трейсбек на 336 рядків, останній — `ConnectError: [WinError 10061] No connection could be made because the target machine actively refused it`, код 1;
  - в обох випадках недокачаного архіву в `downloads/` немає.
- Чому архіву може не бути. Security-релізи гілок, які вже не отримують виправлень, python.org випускає лише у вигляді джерел, без Windows-збірок, а отже й без вбудовуваного архіву (сторінка релізу 3.12.12: «releases of those are made irregularly in source-only form»). HEAD-запити 8 жовтня 2026: `3.12.12` — 404; `3.13.9`, `3.13.15`, `3.13.16`, `3.14.8` — 200.
- `pyretort init` записує в `python_version` версію Python, на якому працює сам PyRetort (`_find_python_version`, [`src/pyretort/cli/commands/init.py:182-184`](../../src/pyretort/cli/commands/init.py)). uv встановлює керовані збірки й security-релізів (на машині розробника є `cpython-3.12.12`), тож `init` → `build` на такому Python падає без жодної ручної правки.
- README (задача 09), розділ Troubleshooting: пункт «A traceback that ends with `HTTPStatusError: Client error '404 Not Found' …`» описує нинішній трейсбек. Після цієї задачі його треба переписати.
- Тести збірки: `tests/test_uv_builder.py` і `tests/cli/test_build.py`. Фікстура `externals` з `tests/conftest.py` замінює `pyretort.builder.uv_builder.PydistManager` фабрикою `fake_pydist_manager` (екземпляр — `MagicMock(spec=PydistManager)`), підміняє `subprocess.run` і `shutil.which`. `tests/test_downloader.py` підміняє `httpx.stream` через `patch("httpx.stream", ...)`.

## Рішення

1. Перетворює `UVBuilder`, як і інші збої збірки (задачі 05 і 16). `Downloader` і `PydistManager` лишаються загальними й далі кидають винятки httpx.
2. В `UVBuilder._build_as_package` виклик `pydist_manager.install_embedded_python(...)` обгортається:
   - `httpx.HTTPStatusError` зі статусом 404 → `BuildError` з першим рядком `python.org has no Windows embeddable package for Python <version> (<architecture>): <url>` і другим `Security-only releases ship no Windows binaries; set python_version to a release that has one.` URL — з `e.request.url`: у `HTTPStatusError` запит є завжди;
   - будь-який інший `httpx.HTTPError` (інший статус, з'єднання, таймаут) → `BuildError` з першим рядком `Could not download the embedded Python <version> (<architecture>): <помилка>` і другим `Check the internet connection and run the build again.`
3. `build_command` не змінюється: друкує `BuildError` у stderr через `echo` і виходить із кодом 1; з `-q` вивід порожній.
4. README, Troubleshooting: пункт про трейсбек замінити пунктом про перше повідомлення (що робити — те саме: обрати реліз з архівом) і додати пункт `Could not download the embedded Python …` → перевірити з'єднання; за проксі httpx бере його зі змінних `HTTPS_PROXY` і `HTTP_PROXY`.
5. CHANGELOG: рядок у розділі Fixed тієї секції, що зараз угорі (`[Unreleased]`).

## Сіми

`UVBuilder(config).build()` і CLI `build` через `CliRunner`, як у задачі 16, з фікстурами `externals` і `generate_exe`. Збій дає справжній виняток httpx, без `MagicMock` усередині; `fake_pydist_manager` імпортується з `tests.conftest`, як `BuildExternals` у `tests/test_uv_builder.py`:

```python
url = "https://www.python.org/ftp/python/3.12.12/python-3.12.12-embed-amd64.zip"
request = httpx.Request("GET", url)
missing = httpx.HTTPStatusError(
    "Client error '404 Not Found'",
    request=request,
    response=httpx.Response(404, request=request),
)
offline = httpx.ConnectError("[WinError 10061] No connection could be made", request=request)


def failing_pydist_manager(error: Exception) -> Callable[..., MagicMock]:
    def make(pydist_path: Path, downloader: Downloader) -> MagicMock:
        manager = fake_pydist_manager(pydist_path, downloader)
        manager.install_embedded_python.side_effect = error
        return manager

    return make


externals.pydist_manager_class.side_effect = failing_pydist_manager(missing)
```

## Кроки

Кожен крок: тест → червоний → мінімальна зміна → `uv run pytest -q tests/test_uv_builder.py tests/cli/test_build.py` зелений → далі.

1. `test_build_reports_missing_embedded_python`: конфігурація з `python_version="3.12.12"`, `install_embedded_python` кидає `missing` → `BuildError`; у повідомленні `python.org has no Windows embeddable package for Python 3.12.12 (amd64)` і URL. Падає, бо зараз вилітає `HTTPStatusError`. Мінімальна зміна — перша гілка рішення 2.
2. `test_build_reports_failed_download`: `install_embedded_python` кидає `offline` → `BuildError`; у повідомленні `Could not download the embedded Python 3.12.12 (amd64)` і `WinError 10061`. Мінімальна зміна — друга гілка рішення 2.
3. CLI: `test_build_reports_missing_embedded_python_without_traceback`: код 1; у `result.stderr` є `python.org has no Windows embeddable package`; у `result.output` немає `Traceback` і `Build complete`. Пройде одразу після кроку 1: переконайся, що він червоніє на тимчасовому мутанті без перехоплення, і поверни код.
4. README і CHANGELOG (рішення 4 і 5).
5. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Три тести вище існують під цими назвами і проходять.
- Ручна перевірка, як у «Контексті», на будь-якому проєкті (наприклад, `examples/hello-cli`):
  - `python_version = "3.12.12"` → `uv run pyretort build -p ...` друкує `python.org has no Windows embeddable package for Python 3.12.12 (amd64): ...` без трейсбека, код 1;
  - версія, якої немає в `downloads/`, і `$env:HTTPS_PROXY = "http://127.0.0.1:9"` → `Could not download the embedded Python ...` без трейсбека, код 1. Після перевірки змінну прибрати, а `pyproject.toml` повернути.
- У README немає пункту про трейсбек; є два нові пункти з рішення 4. У CHANGELOG є рядок із рішення 5.
- Чотири команди з [README.md](README.md) — за його правилами.
- Статус задачі в [README.md](README.md) змінено на DONE.

## Поза межами

- Перевірка під час `check`, що для `python_version` є архів на python.org: це мережевий запит, ідея вже є в списку «після 0.1».
- Вибір у `init` версії, для якої архів існує.
- Повторні спроби завантаження, власні налаштування проксі й таймауту.
- Пошкоджений архів у кеші (наприклад, процес убито під час завантаження) і помилки розпакування — окремою задачею, якщо знадобиться.

## Коміти

- `fix(builder): report failed embedded Python downloads as BuildError`
- `docs: describe download failures in the README troubleshooting`

## Джерела

- Винятки httpx (`HTTPStatusError`, `ConnectError`, `HTTPError`): https://www.python-httpx.org/exceptions/
- Змінні середовища httpx (`HTTPS_PROXY`, `HTTP_PROXY`): https://www.python-httpx.org/environment_variables/
- Python 3.12.12, security-релізи лише у вигляді джерел: https://www.python.org/downloads/release/python-31212/
- Стан гілок Python: https://devguide.python.org/versions/
