# 19. Мертвий код кешу збірки: `build_hash` і `CacheManager`

Залежить від: нічого. Оцінка: S.

## Мета

У пакеті немає коду, який нічого не робить. Поле `BuildConfig.build_hash` і модуль `pyretort.builder.cache_manager` з класом `CacheManager` видалено разом із їхніми тестами; поведінка команд не змінюється.

## Контекст

Номери рядків — станом на коміт `c190f9a`.

- Обидва з'явилися 28 жовтня 2025: `CacheManager` — у коміті `a1fb6a3`, `build_hash` — у `2933cee`. У `a1fb6a3` команда `build` ще тримала в `downloads/python_<хеш>/` підготовлений embedded Python із залежностями і перевикористовувала його, а хеш рахувала через `hash_utils`; `build_hash` мав замінити той хеш, але його ніхто так і не прочитав. `fa94b10` того ж дня переписала `build` на `UVBuilder`, який збирає з нуля, і відтоді `CacheManager` теж ніхто не викликає.
- `BuildConfig.build_hash` у [`src/pyretort/types.py`](../../src/pyretort/types.py):
  - обов'язкове поле (рядки 66-67);
  - `from_pyproject_toml` рахує його як SHA-256 від `python_version|python_architecture|відсортовані залежності` (рядки 293-295) і передає в модель (рядок 378);
  - лише для нього потрібні імпорт `from hashlib import sha256` (рядок 6) і змінна `dependencies` (рядки 278-279).
- [`src/pyretort/builder/cache_manager.py`](../../src/pyretort/builder/cache_manager.py), 68 рядків: клас `CacheManager` для теки кешу з `__contains__`, `get_path`, `cleanup`, `get_size` і `remove`.
- Знайдено 8 жовтня 2026 після задачі 09, коли репозиторій переглядали на зайве. `git grep -nE "build_hash|CacheManager|cache_manager" -- src launcher` знаходить лише самі визначення; жодна задача і жодна ідея після 0.1 їх не згадує. Кеш завантажень Python веде `Downloader` (тека `downloads/`), а не `CacheManager`.
- Тести, які їх зачіпають:
  - `tests/test_cache_manager.py` — увесь файл;
  - `tests/test_integration.py`: імпорт `CacheManager` (рядок 12), клас `TestCacheDownloaderIntegration` (рядки 64-85) і перевірка `len(config.build_hash) == 64` у `test_full_config_flow` (рядок 61);
  - `tests/test_types.py`: аргумент `build_hash="test123"` у конструкторах `BuildConfig` (рядки 53-302), тести `test_build_hash_is_generated` (354-358) і `test_build_hash_changes_with_dependencies` (360-417);
  - аргумент `build_hash` у `sample_build_config` (`tests/conftest.py:76`) і в `make_config` (`tests/test_uv_builder.py:30`).
- Пастка: забутий у тесті `build_hash="..."` не впаде. Перевірено того ж дня: `BuildConfig` з невідомим іменованим аргументом створюється без помилки (pydantic за замовчуванням ігнорує зайві поля), і `mypy` з плагіном pydantic у налаштуваннях проєкту теж мовчить. Тому залишки шукає `git grep` (крок 4).
- `DEFAULT_BLACKLIST` у `src/pyretort/constants.py` теж поки не використовується, але його чекає задача 12, тож він лишається.

## Рішення

1. Видалити `src/pyretort/builder/cache_manager.py` і `tests/test_cache_manager.py`, а з `tests/test_integration.py` — імпорт `CacheManager` і клас `TestCacheDownloaderIntegration`.
2. Видалити з `types.py` поле `build_hash`, його обчислення, імпорт `sha256` і змінну `dependencies`. З тестів прибрати аргументи `build_hash=...`, тести `test_build_hash_is_generated` і `test_build_hash_changes_with_dependencies` та перевірку довжини хешу в `test_full_config_flow`.
3. CHANGELOG не змінюється: це внутрішній код, якого немає в документації і не було в жодному релізі.
4. Якщо колись знадобиться пропускати незмінені збірки, кеш проєктується заново окремою задачею.

## Сіми

Нових тестів немає: це видалення без зміни поведінки, тобто рефакторинг за правилами [README.md](README.md). Сітка безпеки — наявні тести CLI, конфігурації і збірки; вони мають лишитися зеленими.

## Кроки

1. `uv run pytest` зелений до змін.
2. Рішення 1 → `uv run pytest` зелений.
3. Рішення 2 → `uv run pytest` і `uv run mypy src launcher` зелені.
4. `git grep -nE "build_hash|CacheManager|cache_manager" -- src tests launcher` нічого не знаходить.
5. Критерій завершення з [README.md](README.md).

## Критерій завершення

- `src/pyretort/builder/cache_manager.py` і `tests/test_cache_manager.py` видалено; перевірка з кроку 4 нічого не знаходить.
- Чотири команди з [README.md](README.md) — за його правилами.
- Статус задачі в [README.md](README.md) змінено на DONE.

## Поза межами

- Кеш збірки, який пропускає незмінені збірки (рішення 4).
- `DEFAULT_BLACKLIST` (задача 12).

## Коміти

- `refactor(builder): remove the unused CacheManager`
- `refactor(config): remove the unused build_hash`

## Джерела

- Pydantic, `extra` у конфігурації моделі (за замовчуванням `'ignore'`): https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra
- Плагін pydantic для mypy, `init_forbid_extra`: https://docs.pydantic.dev/latest/integrations/mypy/#configuring-the-plugin
