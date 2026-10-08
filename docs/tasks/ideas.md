# Ідеї

Ідеї для PyRetort, для яких ще немає задачі. Розділ — одна ідея, заголовок розділу — її slug, тож посилання на ідею має вигляд `ideas.md#<slug>`.

**Slug** — малі латинські літери, цифри й дефіси. Перше слово — команда чи частина PyRetort, якої стосується ідея: `build`, `check`, `cleanup`, `init`… Розділи впорядковано за slug, тож ідеї однієї команди стоять поруч.

**Від ідеї до задачі.** Роботу над ідеєю починають із задачі: файл `NN-<slug>.md` у форматі [беклогу](README.md). Тоді ідею з цього файлу видаляють, а посилання на неї (їх знаходить пошук за slug) переводять на задачу.

## build-from-uv-lock

Збірка за `uv.lock`, наприклад через `uv export`. Зараз обидва режими ставлять найновіші сумісні версії залежностей, а не ті, з якими застосунок перевіряли.

## build-smaller-dist

Зменшення розміру дистрибутива: видалення `tests/`, `*.dist-info`, `__pycache__` із site-packages, компіляція в байткод.

## build-standalone-excludes

Власні шаблони виключень для копіювання джерел у standalone-режимі.

## check-project-name

Перевірка `[project].name` за PEP 508 у `check`. Ім'я з пробілом (`System Monitor`) зараз проходить `check`, а збірка падає вже на кроці uv (`Not a valid package or extra name`) — в обох режимах; див. задачу 12, факт 6.

## check-python-version-exists

Перевірка, що обрана `python_version` існує на python.org, під час `check`.

## cleanup-dry-run

`cleanup --dry-run`: показати теки, які буде видалено, нічого не видаляючи.

## init-after-plain-uv-init

`init` для проєкту після простого `uv init`. З uv 0.12 це пакет `src/<slug>/` без `__main__.py`, з `main()` в `__init__.py` і `[project.scripts]` (`my-app = "my_app:main"`), тож `init` лише попереджає про `__main__.py`. Варіанти: підказати вміст `__main__.py` або запускати точку входу з `[project.scripts]`. Див. задачу 21, «Контекст».

## init-finds-icon

Автопошук `.ico` у проєкті під час `init`.

## init-respects-requires-python

`init` пише в `python_version` версію Python, на якому працює PyRetort, а `uv init` пише в `requires-python` нижню межу за версією свого Python. Коли вони розходяться (наприклад, PyRetort на 3.13, а `requires-python = ">=3.14"`), `check` у standalone-режимі падає одразу після `init`. Попереджати про це в `init` або брати версію, що задовольняє `requires-python`.
