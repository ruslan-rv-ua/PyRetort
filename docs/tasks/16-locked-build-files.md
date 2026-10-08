# 16. Зайняті файли збірки: `BuildError` замість трейсбека

Залежить від: 06. Оцінка: S.

## Мета

Коли `pyretort build` не може очистити `build/<dist_name>/` або перезаписати `dist/<dist_name>.zip`, бо файл тримає інший процес, команда друкує зрозуміле повідомлення без трейсбека і завершується з кодом 1, як вимагає рішення 1 задачі 05.

## Контекст

Номери рядків — станом на коміт `38b97fc` (задача 06).

- Рішення 1 задачі 05: «Усі передбачувані збої збірки кидають `BuildError` з повідомленням для людини». `build_command` ([`src/pyretort/cli/commands/build.py:33-37`](../../src/pyretort/cli/commands/build.py)) друкує `BuildError` у stderr і виходить із кодом 1; будь-який інший виняток Typer показує трейсбеком (код виходу теж 1).
- [`src/pyretort/builder/base_builder.py`](../../src/pyretort/builder/base_builder.py): `prepare_directories` (34-41) видаляє стару `build/<dist_name>/` через `shutil.rmtree`, `create_archive` (43-55) пише архів через `shutil.make_archive`. `OSError` з них ніхто не перехоплює. `UVBuilder.build` ([`src/pyretort/builder/uv_builder.py:23-41`](../../src/pyretort/builder/uv_builder.py)) викликає `prepare_directories` першим кроком, а `create_archive` — останнім, після встановлення пакетів і генерації лаунчера.
- Знайдено 8 жовтня 2026 під час рев'ю задачі 06. Перевірено того ж дня на Python 3.13.9 справжньою збіркою `examples/Simple RSS`: скрипт тримав файл відкритим через `win32file.CreateFile(path, GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, 0, None)` і запускав `pyretort build`.
  - Зайнятий `build/simple-rss-0.1.0-amd64/simple-rss.exe` (так буває, коли застосунок із попередньої збірки ще працює): після рядка `Preparing build directory ...` — трейсбек із `shutil.rmtree` і `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: '...\simple-rss.exe'`, код 1.
  - Зайнятий `dist/simple-rss-0.1.0-amd64.zip` (архів відкрито в іншій програмі): збірка проходить повністю, до `Generating launcher ...`, потім трейсбек із `zipfile` і `PermissionError: [Errno 13] Permission denied: '...\simple-rss-0.1.0-amd64.zip'`, код 1.
- `shutil.rmtree` зупиняється на першій помилці, тож тека після збою частково видалена (як у задачі 13).
- Як заблокувати файл у тесті (перевірено того ж дня): файл, відкритий звичайним `open(path, "rb")`, не дає себе видалити (`[WinError 32]`), але перезапис і `shutil.make_archive` поверх нього вдаються, бо Python відкриває файли з `FILE_SHARE_WRITE`. Перезапис забороняє лише відкриття без `FILE_SHARE_WRITE`, як у `win32file.CreateFile` вище; pywin32 — залежність проєкту.
- Тести збірки: `tests/test_uv_builder.py` (фікстури `externals` і `generate_exe` з `tests/conftest.py`, хелпер `make_config` з параметром `create_dist_zip_file`) і `tests/cli/test_build.py` (клас `TestBuildCommandOutput` зі справжнім `UVBuilder`).

## Рішення

1. `BaseBuilder.__init__` обчислює й шлях архіву, як решту шляхів: `self.archive_path = self.dist_path / f"{self.config.dist_name}.zip"`; `create_archive` повертає його. Шлях потрібен повідомленню про помилку ще до того, як `make_archive` поверне ім'я файлу.
2. `prepare_directories`: будь-який `OSError` → `BuildError` з першим рядком `Could not prepare the build directory <app_path>: <помилка>` і другим `Close the application from the previous build and other programs that use its files, then run the build again.`
3. `create_archive`: будь-який `OSError` → `BuildError` з першим рядком `Could not write the archive <archive_path>: <помилка>` і другим `Close the programs that use the archive, then run the build again.`
4. Решта без змін: `build_command` друкує `BuildError` у stderr через `echo` і виходить із кодом 1; з `-q` вивід порожній.

## Сіми

`UVBuilder(config).build()` з фікстурами `externals` і `generate_exe`; CLI `build` через `CliRunner` з тими ж фікстурами і `valid_pyproject_toml`. Збій — справжнє блокування Windows, без підміни `shutil`:

```python
# Файл у build/<dist_name>/: звичайний open() забороняє видалення.
with open(app_dir / "stale.txt", "rb"):
    with pytest.raises(BuildError, match="Could not prepare the build directory"):
        UVBuilder(config).build()

# Архів у dist/: заборона запису потребує CreateFile без FILE_SHARE_WRITE.
handle = win32file.CreateFile(
    str(archive), win32con.GENERIC_READ, win32con.FILE_SHARE_READ,
    None, win32con.OPEN_EXISTING, 0, None,
)
try:
    with pytest.raises(BuildError, match="Could not write the archive"):
        UVBuilder(config).build()
finally:
    handle.Close()
```

## Кроки

Кожен крок: тест → червоний → мінімальна зміна → `uv run pytest -q tests/test_uv_builder.py tests/cli/test_build.py` зелений → далі.

1. `test_build_reports_locked_build_dir`: у `build/my-app-0.1.0-amd64/` лежить `stale.txt`, відкритий через `open` → `BuildError`; у повідомленні `Could not prepare the build directory`, шлях `build/my-app-0.1.0-amd64` і `WinError 32`. Падає, бо зараз вилітає `PermissionError`. Мінімальна зміна — рішення 2.
2. `test_build_reports_locked_archive`: `create_dist_zip_file=True`, у `dist/` лежить `my-app-0.1.0-amd64.zip` з довільними байтами, відкритий через `CreateFile` з `FILE_SHARE_READ` → `BuildError`; у повідомленні `Could not write the archive` і шлях `dist/my-app-0.1.0-amd64.zip`. Мінімальна зміна — рішення 1 і 3.
3. CLI: `test_build_reports_locked_build_dir_without_traceback`: у `build/test-app-0.1.0-amd64/` відкритий файл → код 1; у `result.stderr` є `Could not prepare the build directory`; у `result.output` немає `Build complete`. Пройде одразу після кроку 1: переконайся, що він червоніє на тимчасовому мутанті без перехоплення `OSError`, і поверни код.
4. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Три тести вище існують під цими назвами і проходять.
- Ручна перевірка, як у «Контексті»: поки скрипт тримає `examples\Simple RSS\dist\simple-rss-0.1.0-amd64.zip` через `CreateFile` з `FILE_SHARE_READ`, `uv run pyretort build -p "examples/Simple RSS/pyproject.toml"` друкує `Could not write the archive ...` без трейсбека, код 1; із зайнятим файлом у `build\simple-rss-0.1.0-amd64\` — `Could not prepare the build directory ...`.
- Чотири команди з [README.md](README.md) — за його правилами.
- Статус задачі в [README.md](README.md) змінено на DONE.

## Поза межами

- Перевіряти чи видаляти старий архів на початку збірки, щоб не чекати збою до кінця: видалення падає й тоді, коли перезапис удався б (файл відкрито без `FILE_SHARE_DELETE`), і забирає останній архів, якщо збірка не вдасться.
- Пошук процесу, який тримає файл; повторні спроби; зняття атрибута «лише читання».
- Інші винятки збірки (розпакування Python, мережа) — окремою задачею, якщо знадобиться.

## Коміти

- `fix(builder): report locked build files as BuildError`

## Джерела

- `shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree
- `shutil.make_archive`: https://docs.python.org/3/library/shutil.html#shutil.make_archive
- `CreateFileW`, режими спільного доступу: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
