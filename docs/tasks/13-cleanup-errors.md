# 13. Команда `cleanup`: код 1, коли теку не вдалося видалити

Залежить від: 01. Оцінка: S.

## Мета

Якщо хоч одну теку артефактів не вдалося видалити, `pyretort cleanup` завершується з кодом 1 і не пише `Cleanup complete.`, а решту запитаних тек усе одно чистить.

## Контекст

Номери рядків — станом на коміт `6420673` (кінець задачі 01).

- `_cleanup_dir` ([`src/pyretort/cli/commands/clean.py:83-92`](../../src/pyretort/cli/commands/clean.py)) ловить `OSError` від `shutil.rmtree`, друкує в stderr `Error removing <description> '<path>': <помилка>` і повертається так само, як після успіху. Далі `cleanup_command` друкує `Cleanup complete.` (рядок 80) і завершується з кодом 0.
- Типова причина на Windows — файл у теці відкритий іншим процесом, наприклад зібраний застосунок запущено з `build/`. Перевірено 7 жовтня 2026 на Python 3.13.9: поки `build/artifact.txt` відкритий через `open(...)`, `cleanup all` друкує в stdout `Removed cache directory: ...`, `Removed dist directory: ...`, `Cleanup complete.`, у stderr — `Error removing build directory '...': [WinError 32] The process cannot access the file because it is being used by another process: '...'`, код виходу 0. `downloads/` і `dist/` видалено, `build/` лишилась.
- `shutil.rmtree` зупиняється на першій помилці: файли, до яких він дійшов раніше, вже видалено, решта лишається. Тека після збою частково видалена.
- Тести команди — у `tests/cli/test_cleanup.py` (задача 01): фікстури `cwd_elsewhere`, `bare_project`, `project` (теки `downloads/`, `build/`, `dist/`, у кожній `artifact.txt`) і хелпер `remaining_artifact_dirs`. Гілка `except OSError` — єдині непокриті рядки `clean.py` (89-90).

## Рішення

1. Після невдачі з однією текою команда пробує решту запитаних тек — так уже є, закріпити тестом.
2. Повідомлення про невдачу для конкретної теки — без змін.
3. Якщо хоч одна тека не видалилась, замість `Cleanup complete.` у stderr друкується `Cleanup incomplete: some directories could not be removed.`, код виходу 1. Якщо все видалено або тек не було — як зараз: `Cleanup complete.`, код 0.
4. Усі повідомлення — через `echo(ctx, ...)`: з `-q` вивід порожній, а код виходу 1 лишається.

## Сіми

Тільки CLI: `CliRunner().invoke(app, ["cleanup", ...])` з фікстурами `tests/cli/test_cleanup.py`. Збій видалення — справжнє блокування Windows, без підміни `shutil`: тест тримає файл відкритим на час виклику.

```python
with open(project / "build" / "artifact.txt", "rb"):
    result = runner.invoke(
        app, ["cleanup", "build", "-p", str(project / "pyproject.toml")]
    )
```

## Кроки

Кожен крок: тест → червоний → мінімальна зміна → `uv run pytest -q tests/cli/test_cleanup.py` зелений → далі.

1. `test_cleanup_fails_when_dir_cannot_be_removed`: файл у `build/` відкритий, `cleanup build -p ...` → код 1; у `result.stderr` є `Error removing build directory` і `Cleanup incomplete`; у `result.output` немає `Cleanup complete.`. Падає, бо зараз код 0. Мінімальна зміна: `_cleanup_dir` повертає `bool` (вдалося чи ні), `cleanup_command` збирає результати.
2. `test_cleanup_continues_after_failed_dir`: файл у `build/` відкритий, `cleanup all -p ...` → код 1, `remaining_artifact_dirs(project) == {"build"}`. Поведінка вже є, тож тест пройде одразу: переконайся, що він червоніє на тимчасовому мутанті «зупинитися після першої невдалої теки», і поверни код.
3. `test_cleanup_quiet_still_fails_when_dir_cannot_be_removed`: `-q cleanup build -p ...` з відкритим файлом → код 1, `result.output == ""`. Пройде одразу після кроку 1; закріплює рішення 4 для скриптів, які запускають `-q` і дивляться лише на код виходу.

## Критерій завершення

- Три тести вище існують під цими назвами і проходять; `uv run pytest` зелений.
- `uv run pytest --cov=pyretort.cli.commands.clean --cov-report=term-missing tests/cli/test_cleanup.py` показує 100 % для `clean.py`.
- Чотири команди з [README.md](README.md) — за його правилами.
- Статус задачі в [README.md](README.md) змінено на DONE.

## Поза межами

Інші команди; повторні спроби видалення; зняття атрибута «лише читання»; пошук процесу, який тримає файл.

## Коміти

- `fix(cli): fail cleanup when an artifact directory cannot be removed`

## Джерела

- `shutil.rmtree`: https://docs.python.org/3/library/shutil.html#shutil.rmtree
