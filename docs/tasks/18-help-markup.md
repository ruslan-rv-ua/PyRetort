# 18. Довідка `init --help`: назва секції зникає

Залежить від: нічого. Оцінка: S.

## Мета

`pyretort init --help` показує опис `--force` повністю: `Overwrite an existing [tool.pyretort] section.`

## Контекст

Номери рядків — станом на коміт `c190f9a`.

- Знайдено 8 жовтня 2026 під час задачі 09: `uv run pyretort init --help` показує `--force  Overwrite an existing  section.`, з двома пробілами на місці `[tool.pyretort]`.
- Текст — у [`src/pyretort/cli/commands/init.py:25-29`](../../src/pyretort/cli/commands/init.py): `help="Overwrite an existing [tool.pyretort] section."`.
- Typer 0.27.3 малює довідку через Rich, і за замовчуванням `rich_markup_mode="rich"`: квадратні дужки в описах Rich читає як теги розмітки й прибирає.
- Інших квадратних дужок у текстах довідки `src/pyretort/cli` немає (перевірено пошуком того ж дня). Повідомлення під час роботи команд іде через `typer.echo` ([`src/pyretort/cli/_output.py`](../../src/pyretort/cli/_output.py)) без Rich, тому `pyproject.toml already contains [tool.pyretort]; use --force to overwrite` друкується правильно.
- Проба на Typer 0.27.3 того ж дня, рядок `--force` у `init --help`:

  | Варіант | Результат |
  |---|---|
  | типовий режим, текст як є | `Overwrite an existing  section.` |
  | типовий режим, текст `\[tool.pyretort]` | `Overwrite an existing [tool.pyretort] section.`, у рамці Rich |
  | `rich_markup_mode="markdown"` | текст правильний, у рамці Rich |
  | `rich_markup_mode=None` | текст правильний, але довідка всіх команд втрачає рамки Rich і стає простим текстом |

- Тести CLI — `typer.testing.CliRunner` у [`tests/cli/test_init.py`](../../tests/cli/test_init.py). У пробі рядок `--force` уміщався в типову ширину CliRunner без перенесення.

## Рішення

1. Екранувати дужку в тексті довідки: `help="Overwrite an existing \\[tool.pyretort] section."` Rich покаже `[tool.pyretort]`, вигляд довідки не зміниться.
2. Режим розмітки застосунку лишити типовим: `markdown` почне тлумачити `*`, `_` і бектики в інших описах, а `None` прибере рамки з усієї довідки.
3. CHANGELOG: рядок у розділі Fixed тієї секції, що зараз угорі (`[Unreleased]`).

## Сіми

CLI через `CliRunner`: `runner.invoke(app, ["init", "--help"])`; у `result.output` є `Overwrite an existing [tool.pyretort] section.`

## Кроки

1. `test_init_help_shows_the_section_name` у `tests/cli/test_init.py`: червоний, бо зараз у виводі `Overwrite an existing  section.` Мінімальна зміна — рішення 1. `uv run pytest -q tests/cli/test_init.py` зелений.
2. CHANGELOG (рішення 3).
3. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Тест існує під цією назвою і проходить; `uv run pyretort init --help` показує `[tool.pyretort]`.
- У CHANGELOG є рядок із рішення 3.
- Чотири команди з [README.md](README.md) — за його правилами.
- Статус задачі в [README.md](README.md) змінено на DONE.

## Поза межами

- Зміна `rich_markup_mode` для всього застосунку (рішення 2).
- Загальна перевірка майбутніх текстів довідки на квадратні дужки.

## Коміти

- `fix(cli): show the section name in the init --help text` (разом із рядком CHANGELOG)

## Джерела

- Typer, Rich Markdown and Markup: https://github.com/fastapi/typer/blob/master/docs/tutorial/commands/help.md#rich-markdown-and-markup
- Rich, розмітка і екранування: https://rich.readthedocs.io/en/stable/markup.html#escaping
