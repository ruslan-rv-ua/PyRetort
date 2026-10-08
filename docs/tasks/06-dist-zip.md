# 06. ZIP-архів у `dist/`

Залежить від: 05. Оцінка: S.

## Мета

При `create_dist_zip_file = true` збірка створює `dist/<dist_name>.zip`, який розпаковується в одну теку `<dist_name>/` з exe і Python усередині.

## Контекст

- Поле `create_dist_zip_file` обов'язкове в `[tool.pyretort]` (`src/pyretort/types.py:74`, перевірка типу 326-330), але нічого не робить: `dist_path` створюється (`base_builder.py:19`), і на цьому все. `init` пише `create_dist_zip_file = true` (`init.py:115`), тому користувачі очікують архів.
- `BuildConfig.dist_name` (`types.py:178-182`) дає `<slug-dash>-<version>-<arch>`, наприклад `simple-rss-0.1.0-amd64`; це ж ім'я має тека `build/<dist_name>/` з вмістом `<slug-dash>.exe` і `<slug-dash>/` (після задачі 05 без змін).
- Після задачі 05 `UVBuilder.build()` веде журнал через `log` і кидає `BuildError`.

## Рішення

1. Після генерації лаунчера, якщо `create_dist_zip_file`: `shutil.make_archive(base_name=str(dist_path / dist_name), format="zip", root_dir=build_path, base_dir=dist_name)`. Так усі записи архіву починаються з `<dist_name>/`. Наявний архів перезаписується.
2. `log(f"Created archive {zip_path}")`.
3. `build()` повертає `BuildResult` (dataclass у `src/pyretort/builder/result.py`): `app_dir: Path`, `archive: Path | None`. `build_command` друкує шлях архіву в підсумку.
4. При `false` у `dist/` нічого не з'являється (тека може існувати порожньою).

## Сіми

`UVBuilder.build()` з підмінами як у задачі 05; підмінені `generate_exe` і `PydistManager` мають створювати в `app_path` файли-заглушки (`<slug-dash>.exe`, `<slug-dash>/python.exe`), щоб архів мав вміст. Архів перевіряється через `zipfile.ZipFile(...).namelist()`. CLI `build` через `CliRunner`.

## Кроки

1. `test_build_creates_zip_with_dist_name_prefix`: `create_dist_zip_file = true` → `dist/<dist_name>.zip` існує; усі імена в `namelist()` починаються з `<dist_name>/`; серед них `<dist_name>/<slug-dash>.exe` і `<dist_name>/<slug-dash>/python.exe`.
2. `test_build_skips_zip_when_disabled`: `false` → у `dist/` немає `*.zip`; `result.archive is None`.
3. `test_build_overwrites_stale_zip`: у `dist/` лежить файл `<dist_name>.zip` з довільним вмістом → після збірки це валідний архів із новим вмістом.
4. `test_build_returns_result_paths`: `result.app_dir == build/<dist_name>`, `result.archive == dist/<dist_name>.zip`.
5. CLI: `test_build_prints_archive_path` — у виводі `Created archive` і шлях.
6. Приклади (задача 10): обидва мають `create_dist_zip_file = true`. У `examples/hello-cli/README.md` речення про те, що архів ще не створюється, замінити описом `dist/hello-cli-0.1.0-amd64.zip`; у розділ «Build with PyRetort» файлу `examples/Simple RSS/README.md` додати `dist/simple-rss-0.1.0-amd64.zip`. Перевірити реальною збіркою `uv run pyretort build -p examples/hello-cli/pyproject.toml`, потім `uv run pyretort cleanup -p examples/hello-cli/pyproject.toml`.
7. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Тести 1-5 існують і проходять; чотири команди з README зелені.
- Ручна перевірка на тестовому проєкті: `Expand-Archive dist\<dist_name>.zip -DestinationPath C:\Temp\x` дає `C:\Temp\x\<dist_name>\<slug-dash>.exe`, і exe запускається звідти.
- Статус у README → DONE.

## Поза межами

Інші формати (7z, інсталятор) — ні. Виключення файлів з архіву — ні.

## Коміти

- `feat(builder): create distributable zip archive in dist/`
- `docs(examples): describe the zip archive in the example READMEs`

## Джерела

- `shutil.make_archive`: https://docs.python.org/3/library/shutil.html#shutil.make_archive
- `zipfile`: https://docs.python.org/3/library/zipfile.html
