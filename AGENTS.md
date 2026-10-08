# Instructions for Agents

## Platform: Windows Only

**IMPORTANT:** PyRetort is designed exclusively for Windows. This is a Windows-only project.

### Key Points
- The application only runs on Windows (platform check is performed at startup)
- All development and testing must be done on Windows
- All terminal commands should be Windows-compatible (cmd.exe or PowerShell)
- File path operations assume Windows path conventions (backslashes, drive letters)
- When generating terminal commands, use Windows syntax:
  - Use backslashes or forward slashes for paths (Python's Path handles both)
  - Use Windows-specific commands (e.g., `dir`, `type`, `del`, `copy`)
  - Or use PowerShell commands when appropriate
- Python architecture detection assumes Windows architectures (AMD64, x86, ARM64)

### Windows Terminal Commands
When executing commands in the terminal:
- Prefer PowerShell commands for modern Windows features
- Use `cmd.exe` commands for maximum compatibility
- Remember that the default shell is PowerShell 7+
- Use `&&` to chain commands that depend on each other (works in cmd.exe and PowerShell 7+); `;` in PowerShell runs the next command even if the previous one fails

## Conventional Commits

When making commits, follow the [Conventional Commits](https://www.conventionalcommits.org/) specification to ensure consistent and meaningful commit messages. This helps with automated versioning, changelog generation, and better project history.

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Examples
- `feat: add user authentication`
- `fix: resolve memory leak in data processing`
- `docs: update README with installation instructions`

Always use lowercase for types and scopes. Keep descriptions concise but descriptive.

## Гілки: git flow

Гілки ведуться за git flow; інструмент — git-flow-next (`git flow version`).

- `main` — лише випущені версії: у неї потрапляють тільки злиття релізів і хотфіксів з анотованим тегом `vX.Y.Z`. Напряму в `main` не комітити.
- `develop` — інтеграційна гілка і гілка за замовчуванням на GitHub. CI запускається на push у `develop` і `main`.
- Будь-яка зміна, навіть документація чи дрібний фікс, робиться у feature-гілці від `develop`: `git flow feature start <назва>`. Для задачі з `docs/tasks/` назва — ім'я файлу задачі без `.md`. Працювати в основному checkout, не у worktree.
- Злиття: `git flow feature finish --no-ff --no-push <назва>`, потім `git push origin develop` — лише на прохання користувача.
- Реліз: `git flow release start vX.Y.Z` → коміт `chore(release): vX.Y.Z` → `git flow release finish --no-ff --no-push -m "PyRetort X.Y.Z" vX.Y.Z`. Finish зливає реліз у `main`, ставить анотований тег із назви релізу і підтягує `main` у `develop`. Префікс `v` у назві релізу дає тег `vX.Y.Z`. Push (`git push origin main develop --follow-tags`) — лише з дозволу користувача.
- Виправлення випущеної версії: `git flow hotfix start vX.Y.Z` від `main`, завершення так само, як у релізу.
- Налаштування git flow живуть у `.git/config`, тож новий клон треба ініціалізувати саме в такому порядку:
  ```
  git branch main origin/main
  git flow init --defaults
  ```
  Без першої команди `init` створить локальну `main` від `develop`.

## Pytest

Use pytest for writing and running unit tests in this Python project. Ensure all new code includes appropriate tests and that existing tests pass before committing changes.

## Запуск тестів з pytest

У цьому проекті використовуються різні типи тестів, які можна запускати за допомогою pytest та uv:

- **Швидкі тести (за замовчуванням):**
  ```
  uv run pytest
  ```
  Запускаються всі тести, крім тих, що позначені маркером `slow`.

- **Повільні тести:**
  ```
  uv run pytest -m slow
  ```
  Запускаються лише тести з маркером `slow`.

- **Наскрізні тести (справжня збірка і запуск exe):**
  ```
  uv run pytest -m e2e
  ```
  `tests/test_e2e_build.py` збирає крихітний проєкт справжнім `pyretort build` і запускає згенерований exe. Потрібні `uv` у PATH та інтернет: збірка завантажує embedded Python з python.org, а uv — бекенд `uv_build`. Щоб не завантажувати архів Python щоразу, вкажи у `PYRETORT_E2E_DOWNLOAD_DIR` теку, де вже лежить `python-3.13.9-embed-amd64.zip`, наприклад `downloads/` будь-якого раніше зібраного проєкту:
  ```
  $env:PYRETORT_E2E_DOWNLOAD_DIR = "examples\Simple RSS\downloads"
  uv run pytest -m e2e
  ```

- **Всі тести (швидкі та повільні):**
  ```
  uv run pytest -m "slow or not slow"
  ```

> **Примітка:** Тести з маркером `slow` автоматично виключаються за замовчуванням завдяки налаштуванню
> `addopts = "-m 'not slow'"`
> у файлі [`pyproject.toml`](pyproject.toml).

## Беклог задач у `docs/tasks/`

Коли просять виконати задачу з `docs/tasks/` (наприклад «виконай задачу docs/tasks/03-...md»): спочатку прочитай [`docs/tasks/README.md`](docs/tasks/README.md) — там спільні правила, TDD-цикл, критерій завершення і таблиця статусів, — потім файл задачі. Працюй за кроками задачі зрізами «червоний → зелений», а наприкінці онови статус задачі в таблиці README тим самим комітом.

## Project Management and Dependencies with uv

Use `uv` for managing Python project dependencies and virtual environments.

### Dependency Management
- Install dependencies from `pyproject.toml`: `uv sync`
- Add a new dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`
- Remove a dependency: `uv remove <package>`
- Update dependencies: `uv sync --upgrade`

### Running Commands
- Run Python scripts: `uv run python script.py`
- Run other tools: `uv run <command>`

Always use `uv` commands instead of direct `pip` or `python` calls to ensure consistency and proper environment isolation.
