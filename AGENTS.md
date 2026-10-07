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
- Remember that the default shell is cmd.exe
- Use `&&` for command chaining in cmd.exe, `;` in PowerShell

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
