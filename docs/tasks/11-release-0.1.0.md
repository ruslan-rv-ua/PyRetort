# 11. Реліз 0.1.0

Залежить від: 07, 08, 09, 10, 13, 14, 15. Оцінка: S.

## Мета

Тег `v0.1.0`, зібране колесо, перевірене встановлення як інструмента, реліз на GitHub. PyPI — за бажанням користувача.

## Контекст

- Версія в `pyproject.toml` уже `0.1.0`; тегів у репозиторії немає; гілка `develop` — єдина і за замовчуванням.
- Задачі ведуться у feature-гілках git flow (див. [README.md](README.md)). `git flow release` і `hotfix` спираються на гілку `main`, якої немає, тому план нижче ставить тег без `git flow release`. Реліз через `git flow release` можливий, лише якщо користувач вирішить створити `main`.
- uv 0.12.x має `uv version` (читання і зміна версії, `--bump`, `--dry-run`), `uv build` (створює `dist/*.whl` і `dist/*.tar.gz`; `--no-sources` рекомендується перед публікацією) і `uv publish` (токен через `--token`/`UV_PUBLISH_TOKEN` або trusted publishing).
- Перевірка колеса без встановлення в проєкт: `uv run --no-project --with <шлях до .whl> -- pyretort version`; встановлення як інструмента: `uv tool install <шлях до .whl>`.
- `dist/` у корені ігнорується git.
- Push, створення релізу і публікація на PyPI — зовнішні дії: виконуються лише з явної згоди користувача в поточній сесії.

## Рішення

1. У `CHANGELOG.md` секція `[Unreleased]` стає `[0.1.0] - <дата>`, над нею з'являється нова порожня `[Unreleased]`.
2. Анотований тег `v0.1.0` на коміті релізу.
3. Реліз на GitHub із текстом із CHANGELOG і прикріпленим `.whl` (`gh release create v0.1.0 dist/*.whl --notes-file <файл>`), якщо `gh` доступний і користувач погодився на push.
4. PyPI: лише якщо користувач просить і сам задає токен через змінну середовища `UV_PUBLISH_TOKEN` у своєму терміналі; токен у файли й у чат не потрапляє.

## Кроки

1. Повна перевірка: чотири команди з [README.md](README.md) плюс `uv run pytest -m "slow or not slow"`.
2. `uv version` → `pyretort 0.1.0`. Оновити CHANGELOG. Коміт `chore(release): v0.1.0`.
3. `Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue; uv build --no-sources`.
4. Перевірка колеса з чужої теки: `uv run --no-project --with "<repo>\dist\pyretort-0.1.0-py3-none-any.whl" -- pyretort version` → `PyRetort 0.1.0`; `uv tool install "<repo>\dist\pyretort-0.1.0-py3-none-any.whl"` → `pyretort build -p examples/hello-cli/pyproject.toml` працює без `uv run`; `examples\hello-cli\build\hello-cli-0.1.0-amd64\hello-cli.exe arg1 "two words" "a&b"` з іншої теки друкує `Arguments: ['arg1', 'two words', 'a&b']` (лаунчер із задачі 15); потім `pyretort cleanup -p examples/hello-cli/pyproject.toml` і `uv tool uninstall pyretort`.
5. `git tag -a v0.1.0 -m "PyRetort 0.1.0"`.
6. Спитати користувача про злиття гілки задачі в `develop`, `git push --follow-tags` і реліз на GitHub; виконати після згоди. Опційно PyPI (пункт 4 рішень).

## Критерій завершення

- Локально: тег `v0.1.0` є, `uv build` дав колесо, колесо встановлюється й працює з іншої теки.
- Якщо користувач погодився: тег запушений, реліз на GitHub створений, CI на тегу зелений.
- Статус → DONE; у README задач секція «Ідеї після 0.1» стає наступною чергою.

## Поза межами

Автоматична публікація з CI — ні.

## Коміти

- `chore(release): v0.1.0`

## Джерела

- uv, build & publish: https://docs.astral.sh/uv/guides/package/
- uv tool install: https://docs.astral.sh/uv/guides/tools/
- GitHub CLI, `gh release create`: https://cli.github.com/manual/gh_release_create
