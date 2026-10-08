# Беклог задач PyRetort

Кожен файл `NN-назва.md` у цій теці — одна задача для однієї сесії Claude Code. Задача самодостатня: контекст, ухвалені рішення, сіми для тестів, кроки TDD, критерій завершення. Код у репозиторії — джерело істини; задача каже, що і чому змінити. Виконана задача — знімок на момент виконання: де вона розходиться з кодом, правий код.

## Як виконувати задачу

Промпт для нової сесії:

```
Виконай задачу docs/tasks/NN-назва.md. Спершу прочитай docs/tasks/README.md.
```

Перед початком перевір у таблиці нижче, що всі залежності задачі мають статус DONE. Залежність-тег `vX.Y.Z` виконана, коли вийшов реліз `vX.Y.Z` або новіший (`git tag --list "v*"`). Наприкінці задачі зміни її статус у таблиці на DONE тим самим комітом, що й останні зміни коду.

## Спільні правила

**Середовище.** Тільки Windows, PowerShell, усі команди через `uv run`. Решта — в [AGENTS.md](../../AGENTS.md).

**TDD-цикл: червоний → зелений.**
- Сіми (публічні межі, на яких пишуться тести) вже узгоджені в розділі «Сіми» кожної задачі. Тести пишуться тільки на них; окреме підтвердження не потрібне.
- Один зріз за раз: один тест, який падає → мінімальна реалізація → `uv run pytest` зелений → наступний зріз. Тести на майбутні зрізи пишуться тоді, коли до них доходить черга.
- Тест перевіряє поведінку через публічний інтерфейс: CLI через `typer.testing.CliRunner`, класи через публічні методи. Очікувані значення — літерали з умови задачі, а не перерахунок за формулою з коду.
- Рефакторинг — окремим кроком після зеленого і окремим комітом.
- Мережа і повільні речі — лише під маркерами `slow`, `requires_network`, `e2e` (секція `[tool.pytest.ini_options]` у `pyproject.toml`); за замовчуванням вони вимкнені.

**Стиль коду.** Python 3.11+, `from __future__ import annotations` у кожному модулі, типи всюди, docstring у публічних функцій. Повідомлення CLI англійською і лише через `echo(ctx, ...)` з `src/pyretort/cli/_output.py`, щоб працював `--quiet`.

**Критерій завершення будь-якої задачі** (на додачу до критеріїв у самій задачі):

```
uv run pytest
uv run ruff check src tests launcher
uv run ruff format --check src tests launcher
uv run mypy src launcher
```

Усі чотири команди завершуються без помилок.

**Гілки й коміти.** Кожна задача — у власній feature-гілці git flow `NN-назва` від `develop`, лише задача 11 — у гілці релізу. Злиття, push, реліз і ініціалізація нового клону описані в розділі «Гілки: git flow» в [AGENTS.md](../../AGENTS.md). Коміти — Conventional Commits, маленькі, по одному на логічну зміну.

## Після релізу

Одразу після `git flow release finish` виконай задачі зі статусом TODO, у яких у стовпці «Залежить від» стоїть тег цього релізу або старіший.

## Задачі

| № | Файл | Суть | Залежить від | Статус |
|---|------|------|--------------|--------|
| 01 | [01-cleanup-command.md](01-cleanup-command.md) | Тести для `cleanup`, необов'язкові цілі, шляхи відносно проєкту | — | DONE |
| 02 | [02-lint-and-types.md](02-lint-and-types.md) | ruff і mypy без помилок, конфігурація інструментів, прибрати debug print | — | DONE |
| 03 | [03-upgrade-dependencies.md](03-upgrade-dependencies.md) | Оновити залежності до актуальних версій | 02 | DONE |
| 04 | [04-config-semantics.md](04-config-semantics.md) | Чесна конфігурація: модуль запуску, будь-який build-backend, зрозуміла відмова standalone, `init --force` | 03 | DONE |
| 05 | [05-build-robustness.md](05-build-robustness.md) | Надійна збірка: іконка, помилки uv, довжина команди, прогрес, `--quiet`, `-p` | 04 | DONE |
| 06 | [06-dist-zip.md](06-dist-zip.md) | ZIP-архів у `dist/` | 05 | DONE |
| 07 | [07-e2e-build-test.md](07-e2e-build-test.md) | Наскрізний тест: реальна збірка і запуск exe | 06 | DONE |
| 08 | [08-ci.md](08-ci.md) | GitHub Actions на windows-latest | 03 | DONE |
| 09 | [09-readme-and-metadata.md](09-readme-and-metadata.md) | README, CHANGELOG, метадані пакета, подяка gen-exe | 06, 14, 15 | DONE |
| 10 | [10-examples.md](10-examples.md) | Приклади: прибрати застарілі, додати hello-cli | 04 | DONE |
| 11 | [11-release-0.1.0.md](11-release-0.1.0.md) | Реліз 0.1.0: тег, публікація на PyPI, перевірка встановлення | 07, 08, 09, 10, 13, 14, 15, 16, 17, 18, 20 | DONE |
| 12 | [12-standalone-mode.md](12-standalone-mode.md) | Після 0.1: standalone-режим — збірка без встановлення пакета, приклад hello-script | 11 | DONE |
| 13 | [13-cleanup-errors.md](13-cleanup-errors.md) | `cleanup`: код 1, коли теку не вдалося видалити | 01 | DONE |
| 14 | [14-optional-config-fields.md](14-optional-config-fields.md) | Необов'язкові поля `[tool.pyretort]`: `main_file` у режимі пакета, типові `install_as_package` і `show_console_window` | 04 | DONE |
| 15 | [15-launcher-without-cmd.md](15-launcher-without-cmd.md) | Власний лаунчер: без cmd.exe, аргументи дослівно, консоль і GUI, три архітектури | 05 | DONE |
| 16 | [16-locked-build-files.md](16-locked-build-files.md) | `build`: `BuildError` замість трейсбека, коли файли попередньої збірки зайняті | 06 | DONE |
| 17 | [17-download-errors.md](17-download-errors.md) | `build`: `BuildError` замість трейсбека, коли вбудований Python не завантажується (немає архіву на python.org, немає мережі) | 09, 16 | DONE |
| 18 | [18-help-markup.md](18-help-markup.md) | `init --help`: назва секції `[tool.pyretort]` зникає з опису `--force` | — | DONE |
| 19 | [19-unused-build-cache.md](19-unused-build-cache.md) | Прибрати мертвий код кешу збірки: `BuildConfig.build_hash` і `CacheManager` | — | DONE |
| 20 | [20-trusted-publishing.md](20-trusted-publishing.md) | Публікація на PyPI з GitHub Actions без токенів (trusted publishing), репетиція на TestPyPI | 08, 09 | DONE |
| 21 | [21-init-detects-standalone.md](21-init-detects-standalone.md) | `init` обирає standalone-режим для скриптів у корені проєкту | 12 | DONE |
| 22 | [22-system-monitor-example.md](22-system-monitor-example.md) | Приклад SystemMonitor: GUI-застосунок у standalone-режимі | 12 | TODO |
| 23 | [23-prune-done-tasks.md](23-prune-done-tasks.md) | Після релізу 0.2.0: прибрати виконані задачі з беклогу, рішення з них — у `docs/decisions.md` | v0.2.0 | TODO |

## Ідеї

Ідеї, для яких ще немає задачі, — у [ideas.md](ideas.md); там же правила, як дописати ідею і як зробити з неї задачу.
