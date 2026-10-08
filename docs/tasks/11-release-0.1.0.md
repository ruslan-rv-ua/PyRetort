# 11. Реліз 0.1.0

Залежить від: 07, 08, 09, 10, 13, 14, 15, 16, 17, 18, 20. Оцінка: S.

## Мета

Тег `v0.1.0`, пакет на PyPI, перевірене встановлення як інструмента, реліз на GitHub.

## Контекст

- Версія в `pyproject.toml` уже `0.1.0`; тегів у репозиторії немає; `develop` — гілка за замовчуванням, `main` поки містить лише перший коміт і першим отримає реліз 0.1.0.
- Гілки ведуться за git flow (розділ «Гілки: git flow» в [AGENTS.md](../../AGENTS.md)). Ця задача виконується не у feature-гілці, а в гілці релізу `release/v0.1.0`. `git flow release finish --no-ff` зливає її в `main`, ставить анотований тег із назви релізу (`v0.1.0`) на коміт злиття і підтягує `main` у `develop`.
- CI запускається на push у `develop` і `main`, на тегах — ні; коміт із тегом перевіряє прогін на `main`.
- Push тегу `v0.1.0` запускає `.github/workflows/release.yml` (задача 20): перевірки з `ci.yml`, збірка й smoke test на Windows, артефакт `dist` (колесо і sdist), потім job `publish-pypi` в environment `pypi`. Job чекає, доки користувач підтвердить розгортання в GitHub (сторінка прогону → Review deployments → `pypi` → Approve and deploy), і публікує через trusted publishing, без токенів.
- uv 0.12.x має `uv version` (читання і зміна версії, `--bump`, `--dry-run`), `uv build` (створює `dist/*.whl` і `dist/*.tar.gz`; `--no-sources` рекомендується перед публікацією) і `uv publish`. `uv publish` у проєкті викликає лише `release.yml`.
- README, розділ Installation: рядок `From PyPI (planned: PyRetort is not published there yet):`. PyPI бере опис пакета з README того коміту, з якого зібрано пакет, тому рядок треба виправити до тегу, а не після публікації.
- Перевірка колеса без встановлення в проєкт: `uv run --no-project --with <шлях до .whl> -- pyretort version`; встановлення як інструмента: `uv tool install <шлях до .whl>`.
- `dist/` у корені ігнорується git.
- `uv build` кладе в sdist усі файли робочої копії, яких не виключає `.gitignore` проєкту: hatchling не читає `.git/info/exclude`. 8 жовтня 2026 (задача 09) так у `pyretort-0.1.0.tar.gz` потрапила тека `.kilo/`, 91 файл: git worktree `.kilo/worktrees/near-citrine` на коміті `54a6ffb`, який створив Kilo Code. Git її не показує, бо `.kilo/` виключено через `.git/info/exclude` і `.kilo/.gitignore`.
- Push, створення релізу і публікація на PyPI — зовнішні дії: виконуються лише з явної згоди користувача в поточній сесії. Розгортання в `pypi` підтверджує сам користувач у GitHub.

## Рішення

1. У `CHANGELOG.md` секція `[Unreleased]` стає `[0.1.0] - <дата>`, над нею з'являється нова порожня `[Unreleased]`.
2. Анотований тег `v0.1.0` на коміті злиття релізу в `main`; його ставить `git flow release finish`.
3. Реліз на GitHub із текстом із CHANGELOG і прикріпленим `.whl` з артефакту `dist` прогону `release.yml`, тобто тим самим файлом, що пішов на PyPI: `gh run download <run-id> --name dist --dir <тека в scratchpad>`, потім `gh release create v0.1.0 <тека>\pyretort-0.1.0-py3-none-any.whl --notes-file <файл>`. Лише якщо `gh` доступний і користувач погодився на push.
4. PyPI: публікує `release.yml` після push тегу і підтвердження користувача в environment `pypi` (задача 20). Токенів PyPI немає.
5. README: рядок `From PyPI (planned: PyRetort is not published there yet):` стає `From PyPI:` у гілці релізу, до тегу.

## Кроки

1. Повна перевірка на `develop`: чотири команди з [README.md](README.md) плюс `uv run pytest -m "slow or not slow"`.
2. `git flow release start v0.1.0`; далі вся робота в гілці `release/v0.1.0`. `uv version` → `pyretort 0.1.0`. Оновити CHANGELOG, README (рішення 5) і статус задачі в таблиці README → DONE. Коміт `chore(release): v0.1.0`.
3. `Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue; uv build --no-sources`. У `tar -tzf dist/pyretort-0.1.0.tar.gz` немає `.kilo/` та інших локальних тек (див. «Контекст»); якщо є — спитати користувача, прибрати їх чи виключити зі збірки, і зібрати знову.
4. Перевірка колеса з чужої теки: `uv run --no-project --with "<repo>\dist\pyretort-0.1.0-py3-none-any.whl" -- pyretort version` → `PyRetort 0.1.0`; `uv tool install "<repo>\dist\pyretort-0.1.0-py3-none-any.whl"` → `pyretort build -p examples/hello-cli/pyproject.toml` працює без `uv run`; з іншої теки `& "<repo>\examples\hello-cli\build\hello-cli-0.1.0-amd64\hello-cli.exe" arg1 "two words" "a&b"` друкує `Arguments: ['arg1', 'two words', 'a&b']` (лаунчер із задачі 15); потім `pyretort cleanup -p examples/hello-cli/pyproject.toml` і `uv tool uninstall pyretort`.
5. `git flow release finish --no-ff --no-push -m "PyRetort 0.1.0" v0.1.0`: злиття в `main`, анотований тег `v0.1.0`, `main` підтягується в `develop`.
6. Спитати користувача про `git push origin main develop --follow-tags`; виконати після згоди.
7. Публікація на PyPI:
   - `gh run list --workflow release.yml --limit 1`, потім `gh run watch <run-id>`. Коли перевірки і збірка зелені, попросити користувача підтвердити розгортання `pypi` у GitHub і дочекатися кінця прогону. Якщо прогін упав до публікації — нічого не опубліковано: з'ясувати причину, а тег, якщо його треба перевипустити, лише за погодженням із користувачем.
   - Перевірка з PyPI з іншої теки: `uv run --isolated --no-project --refresh-package pyretort --with pyretort==0.1.0 -- pyretort version` → `PyRetort 0.1.0`; сторінка https://pypi.org/project/pyretort/ показує README з логотипом.
8. Спитати користувача про реліз на GitHub (рішення 3); виконати після згоди.

## Критерій завершення

- Локально: у `main` є коміт злиття `release/v0.1.0` з анотованим тегом `v0.1.0`, `develop` містить `main`; `uv build` дав колесо, колесо встановлюється й працює з іншої теки.
- Якщо користувач погодився: `main`, `develop` і тег запушені, `pyretort 0.1.0` на PyPI встановлюється, реліз на GitHub створений, CI на `main` і прогін `release.yml` зелені.
- Статус → DONE; у README задач секція «Ідеї після 0.1» стає наступною чергою.

## Поза межами

Зміни в `release.yml` і environments — задача 20.

## Коміти

- `chore(release): v0.1.0`

## Джерела

- uv, build & publish: https://docs.astral.sh/uv/guides/package/
- uv tool install: https://docs.astral.sh/uv/guides/tools/
- GitHub CLI, `gh release create`: https://cli.github.com/manual/gh_release_create
- GitHub CLI, `gh run download`: https://cli.github.com/manual/gh_run_download
- GitHub, підтвердження розгортання в environment: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/review-deployments
