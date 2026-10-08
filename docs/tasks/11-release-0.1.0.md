# 11. Реліз 0.1.0

Залежить від: 07, 08, 09, 10, 13, 14, 15, 16. Оцінка: S.

## Мета

Тег `v0.1.0`, зібране колесо, перевірене встановлення як інструмента, реліз на GitHub. PyPI — за бажанням користувача.

## Контекст

- Версія в `pyproject.toml` уже `0.1.0`; тегів у репозиторії немає; `develop` — гілка за замовчуванням, `main` поки містить лише перший коміт і першим отримає реліз 0.1.0.
- Гілки ведуться за git flow (розділ «Гілки: git flow» в [AGENTS.md](../../AGENTS.md)). Ця задача виконується не у feature-гілці, а в гілці релізу `release/v0.1.0`. `git flow release finish --no-ff` зливає її в `main`, ставить анотований тег із назви релізу (`v0.1.0`) на коміт злиття і підтягує `main` у `develop`.
- CI запускається на push у `develop` і `main`, на тегах — ні; коміт із тегом перевіряє прогін на `main`.
- uv 0.12.x має `uv version` (читання і зміна версії, `--bump`, `--dry-run`), `uv build` (створює `dist/*.whl` і `dist/*.tar.gz`; `--no-sources` рекомендується перед публікацією) і `uv publish` (токен через `--token`/`UV_PUBLISH_TOKEN` або trusted publishing).
- Перевірка колеса без встановлення в проєкт: `uv run --no-project --with <шлях до .whl> -- pyretort version`; встановлення як інструмента: `uv tool install <шлях до .whl>`.
- `dist/` у корені ігнорується git.
- Push, створення релізу і публікація на PyPI — зовнішні дії: виконуються лише з явної згоди користувача в поточній сесії.

## Рішення

1. У `CHANGELOG.md` секція `[Unreleased]` стає `[0.1.0] - <дата>`, над нею з'являється нова порожня `[Unreleased]`.
2. Анотований тег `v0.1.0` на коміті злиття релізу в `main`; його ставить `git flow release finish`.
3. Реліз на GitHub із текстом із CHANGELOG і прикріпленим `.whl` (`gh release create v0.1.0 dist/*.whl --notes-file <файл>`), якщо `gh` доступний і користувач погодився на push.
4. PyPI: лише якщо користувач просить і сам задає токен через змінну середовища `UV_PUBLISH_TOKEN` у своєму терміналі; токен у файли й у чат не потрапляє.

## Кроки

1. Повна перевірка на `develop`: чотири команди з [README.md](README.md) плюс `uv run pytest -m "slow or not slow"`.
2. `git flow release start v0.1.0`; далі вся робота в гілці `release/v0.1.0`. `uv version` → `pyretort 0.1.0`. Оновити CHANGELOG і статус задачі в таблиці README → DONE. Коміт `chore(release): v0.1.0`.
3. `Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue; uv build --no-sources`.
4. Перевірка колеса з чужої теки: `uv run --no-project --with "<repo>\dist\pyretort-0.1.0-py3-none-any.whl" -- pyretort version` → `PyRetort 0.1.0`; `uv tool install "<repo>\dist\pyretort-0.1.0-py3-none-any.whl"` → `pyretort build -p examples/hello-cli/pyproject.toml` працює без `uv run`; з іншої теки `& "<repo>\examples\hello-cli\build\hello-cli-0.1.0-amd64\hello-cli.exe" arg1 "two words" "a&b"` друкує `Arguments: ['arg1', 'two words', 'a&b']` (лаунчер із задачі 15); потім `pyretort cleanup -p examples/hello-cli/pyproject.toml` і `uv tool uninstall pyretort`.
5. `git flow release finish --no-ff --no-push -m "PyRetort 0.1.0" v0.1.0`: злиття в `main`, анотований тег `v0.1.0`, `main` підтягується в `develop`.
6. Спитати користувача про `git push origin main develop --follow-tags` і реліз на GitHub; виконати після згоди. Опційно PyPI (пункт 4 рішень).

## Критерій завершення

- Локально: у `main` є коміт злиття `release/v0.1.0` з анотованим тегом `v0.1.0`, `develop` містить `main`; `uv build` дав колесо, колесо встановлюється й працює з іншої теки.
- Якщо користувач погодився: `main`, `develop` і тег запушені, реліз на GitHub створений, CI на `main` зелений.
- Статус → DONE; у README задач секція «Ідеї після 0.1» стає наступною чергою.

## Поза межами

Автоматична публікація з CI — ні.

## Коміти

- `chore(release): v0.1.0`

## Джерела

- uv, build & publish: https://docs.astral.sh/uv/guides/package/
- uv tool install: https://docs.astral.sh/uv/guides/tools/
- GitHub CLI, `gh release create`: https://cli.github.com/manual/gh_release_create
