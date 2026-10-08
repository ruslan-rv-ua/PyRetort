# 15. Власний лаунчер: без cmd.exe, аргументи дослівно

Залежить від: 05. Оцінка: L.

## Мета

Згенерований `<slug>.exe` запускає вбудований Python напряму, без `cmd.exe`, і передає йому власні аргументи дослівно. Вихідний код лаунчера лежить у репозиторії й відтворювано збирається однією командою. Для `show_console_window = false` лаунчер не відкриває консолі. Лаунчер збігається з архітектурою вбудованого Python (`amd64`, `win32`, `arm64`).

## Контекст

Номери рядків — станом на коміт `362b089` (кінець задачі 05; задача 10 код не змінювала).

### Шаблон gen-exe запускає застосунок через cmd.exe

Знайдено 8 жовтня 2026 під час задачі 10 на прикладі `examples/hello-cli`, далі перевірено пробними лаунчерами з `generate_exe`.

- Шаблон `src/pyretort/builder/exe_generator/genexe_template` (123 392 байти, PE32+ x86-64, підсистема console) походить із gen-exe 0.2.1 (див. задачу 09). `generate_exe` (`src/pyretort/builder/exe_generator/generate_exe.py:24-65`) вписує команду в заповнювач із 259 байтів `X` і прапорця `1`/`0` для консолі.
- Вихідний код шаблону — `exe_template/exe_template.cpp` у gen-exe; файл однаковий на тегу `0.2.1` і в `master`. Наш `genexe_template` побайтно збігається з `genexe/res/template` 0.2.1 (git blob `02bbb68c`). Що робить код:
  - `main(int argc, char** argv)` замінює `{EXE_DIR}` на теку з `GetModuleFileNameA` (буфер `char[MAX_PATH]`);
  - дописує до команди `" " + argv[i]` без лапок;
  - виконує рядок через `system()`, тобто `cmd.exe /c`.
- Прапорець консолі `0` викликає `ShowWindow(GetConsoleWindow(), SW_HIDE)`: консольне вікно спершу з'являється, потім ховається. Якщо запустити такий exe з термінала, він, імовірно, сховає вікно самого термінала. Це висновок із коду, не перевірено.
- Скрипта збірки в gen-exe немає. За заголовками бінарника його збирали MSVC з VS2019 16.8 зі статичним CRT.
- Дерево процесів під час роботи: `<app>.exe` → `C:\Windows\System32\cmd.exe` → `python.exe`. Перевірено: пробний скрипт друкує образ свого батьківського процесу.
- Що отримує Python (команда `"{EXE_DIR}\py\python.exe" -m probe_argv`, тека з пробілом; аргументи передано через `subprocess.run([exe, *args])`):

  | Аргументи лаунчера | Результат |
  |---|---|
  | `arg1`, `two words` | `['arg1', 'two', 'words']` |
  | `""` (порожній) | `[]` |
  | `say "hi"` | Python не стартує: `The filename, directory name, or volume label syntax is incorrect.`, код 1 |
  | `a&b` | `['a']`, далі cmd: `'b' is not recognized as an internal or external command`, код 1 |
  | `x\|y` | вивід Python іде в команду `y`, код 255 |
  | `a>out.txt` | cmd створює файл `out.txt` з виводом |
  | `^x` | `['x']` |
  | `%USERNAME%` | ім'я користувача замість тексту |
  | `日本`, `😀` | `['??']` |
  | `é ü ß` | `['e', 'u', '?']` |
  | лаунчер у теці `...\日本\` | Python не стартує: `The system cannot find the path specified.`, код 1 |

  Без змін проходять шлях із пробілом, код виходу (3 → 3) і stdin. Кирилиця в аргументах і в шляху працює лише тому, що на машині розробника ANSI-кодова сторінка 1251: шаблон працює з вузькими рядками (`argv`, `GetModuleFileNameA`), і все, чого немає в цій сторінці, губиться.
- **Безпека.** Аргументи інтерпретує `cmd.exe`. Застосунок, який запускають з недовіреними аргументами, може виконати сторонню команду: наприклад, через асоціацію файлів `"app.exe" "%1"` з іменем файлу, що містить `&` (у назвах файлів Windows `&`, `^`, `%` дозволені).
- **Шаблон команди.** У шаблоні може бути в лапках лише перший токен. `"{EXE_DIR}\py\python.exe" "{EXE_DIR}\probe_argv.py"` не стартує з тією ж помилкою cmd. Саме такий формат запланувала задача 12 (рішення 6: `"{EXE_DIR}\<slug-dash>\python.exe" "{EXE_DIR}\app\<main_file>"`).
- **ASCII.** `generate_exe` кодує команду в ASCII (рядок 59): не-ASCII символ у команді дає `UnicodeEncodeError`. Команда збірки відносна (`{EXE_DIR}` розгортається під час запуску), тож обмеження стосується лише самого шаблонного рядка, наприклад імені модуля.
- **Архітектура.** Шаблон є лише x86-64. Для `python_architecture = "win32"` збірка кладе 32-бітний Python поруч із 64-бітним лаунчером, і на 32-бітній Windows лаунчер не запуститься. На arm64 x64-лаунчер працює через емуляцію.
- Довжина команди обмежена 259 символами (`MAX_CMD_LENGTH`, рядок 20; перевірка з задачі 05, рядки 50-54).

### Прототип (8 жовтня 2026)

Одноразовий прототип у scratchpad підтвердив підхід. У репозиторій він не потрапив; рішення нижче описують, що з нього взяти.

- Близько 150 рядків C: точки входу `wmain` / `wWinMain` (прапорець `-municode`), команда в масиві `wchar_t` з рядком-маркером, розгортання `{EXE_DIR}` у теку з `GetModuleFileNameW`, хвіст `GetCommandLineW` без `argv[0]`, `CreateProcessW` без `cmd.exe`, успадковані std-хендли, job object, у GUI-варіанті `CREATE_NO_WINDOW`.
- Тулчейн: `zig cc` з пакета PyPI `ziglang` 0.16.0 (колесо 94,1 МБ), команда `uv run --no-project --with ziglang python -m ziglang cc`.
  - Пакет збирається в організації ziglang (`codeberg.org/ziglang/zig-pypi`) з офіційних архівів Zig.
  - Версія 0.17.0 з'явилася 8 жовтня 2026 ще без коліс для Windows, тому версію треба закріпити.
  - Перша збірка повільніша: Zig компілює й кешує частини рантайму.
  - Цілі: `x86_64-windows-gnu`, `x86-windows-gnu`, `aarch64-windows-gnu`.
  - Прапорці: `-municode -Os -s -Wl,--subsystem,console` або `-Wl,--subsystem,windows`. На `-mwindows` zig не зважає: підсистема лишається 3 (console).
  - Розміри: amd64 61 440 байтів, win32 72 704, arm64 20 480 (console) і 20 992 (GUI).
  - Дві збірки поспіль дали побайтно однакові файли.
- Перевірено для обох варіантів, для amd64 і для win32 (через WOW64), лаунчер у теці `dir with space тест`:
  - усі аргументи з таблиці вище доходять дослівно, разом із `"`, `\` у кінці, порожніми, кириличними, `日本`, `😀` і `é ü ß`;
  - з теки `...\日本\` прототип запускає справжню збірку hello-cli: `Arguments: ['arg1', 'two words', '日本']`;
  - `out.txt` не з'являється;
  - код виходу 3 → 3, stdin проходить;
  - другий токен у лапках у шаблоні працює;
  - батьківський процес Python — сам лаунчер.
- `add_icon_to_exe` (`generate_exe.py:222-255`) працює з новим exe без змін: група іконок додається, exe запускається, аргументи цілі.
- Відомі лаунчери роблять так само.
  - distlib (`simple_launcher`, BSD-2-Clause; його лаунчери ставить pip) і uv trampoline (MIT або Apache-2.0) дописують сирий хвіст командного рядка після `argv[0]`. distlib бере його з `GetCommandLineW`, uv — з `GetCommandLineA`, коли маніфест вмикає кодову сторінку UTF-8.
  - Обидва запускають Python через `CreateProcessW`, кладуть дочірній процес у job object, ігнорують Ctrl+C і повертають його код виходу.
- Чому не беремо їх готовими:
  - distlib запускає `python "<exe>"` і виконує `__main__.py` з zip, дописаного після shebang, а не `python -m <module>`;
  - формат uv trampoline внутрішній (уже змінювався між uv 0.9 і 0.10), а для збірки потрібен nightly Rust;
  - власний лаунчер — близько 150 рядків, зберігає поточну семантику `-m` і механізм заповнювача, з яким уже працюють іконки.
- Перевірено заодно: вбудований Python з `._pth` не додає поточну теку в `sys.path` для `-m`, тож модуль із теки, звідки запускають exe, не може підмінити застосунок. Лаунчер це не змінює.
- На машині розробника є й інші тулчейни: gcc 15.2 (MinGW-w64, scoop), clang (scoop), VS Build Tools 2026. Прототип збирався і gcc: console 18 944 байти, GUI 19 456 байтів.
- `uv build` кладе файли без розширення з теки пакета в колесо (зараз `pyretort/builder/exe_generator/genexe_template`).

### Код, який змінюється

- `generate_exe.py`: `EXE_TEMPLATE_FILE` (рядок 19), `MAX_CMD_LENGTH` і `REPLACE_SIGNATURE` (20-21), функція `generate_exe` (24-65).
- `uv_builder.py:66-76`: рядок команди й виклик `generate_exe`.
- Тести: `tests/test_generate_exe.py`, де перевіряються ASCII-байти команди, розмір, що дорівнює шаблону, і ліміт 259. Підміна `generate_exe` у `tests/conftest.py:50-53`, тести команди в `tests/test_uv_builder.py:38-68`.
- `examples/hello-cli/README.md`: застереження «Known limitation: the current launcher passes them through `cmd.exe`...».

## Рішення

1. **Вихідний код.** `launcher/launcher.c` у корені репозиторію, поза пакетом. Один файл на обидва варіанти: консольний (`wmain`) і GUI (`wWinMain`, макрос `PYRETORT_GUI`). Коментар на початку файлу пояснює формат заповнювача й правило для `argv[0]`.
2. **Збірка.**
   - Група залежностей у `pyproject.toml`: `launcher = ["ziglang==0.16.0"]`. Вона не входить у `dev`, тож `uv sync` її не ставить.
   - Скрипт `launcher/build.py`, запуск `uv run --group launcher python launcher/build.py`. Він компілює шість шаблонів `src/pyretort/builder/exe_generator/templates/launcher-<arch>-<console|gui>` (без розширення, як `genexe_template`), де `<arch>` — значення `PythonArchitecture`. Компілятор: `sys.executable -m ziglang cc` з цілями й прапорцями з прототипу.
   - Режим `--check` збирає в тимчасову теку й порівнює побайтно із закомміченими файлами; при розбіжності код 1 і список файлів.
3. **Поведінка лаунчера.**
   - Шаблон команди: масив `wchar_t` на 1024 елементи з маркером `PYRETORT-LAUNCHER-COMMAND-PLACEHOLDER`, далі нулі. Маркер трапляється у файлі рівно один раз.
   - `{EXE_DIR}` розгортається в теку лаунчера (`GetModuleFileNameW` без останнього компонента, буфер росте для довгих шляхів), усі входження.
   - Якщо в лаунчера є аргументи, до розгорнутої команди дописується пробіл і **сирий хвіст** `GetCommandLineW` після `argv[0]`. `argv[0]` пропускається за правилом CRT для імені програми: лапки перемикають стан, ім'я закінчується на першому пробілі чи табуляції поза лапками; далі пропускаються пробіли й табуляції. Ніякого повторного розбору чи взяття в лапки:

     ```c
     static const wchar_t *arguments_tail(const wchar_t *p) {
         BOOL quoted = FALSE;
         for (; *p; p++) {
             if (*p == L'"') quoted = !quoted;
             else if (!quoted && (*p == L' ' || *p == L'\t')) break;
         }
         while (*p == L' ' || *p == L'\t') p++;
         return p;
     }
     ```
   - `CreateProcessW(NULL, command_line, NULL, NULL, TRUE, CREATE_SUSPENDED [| CREATE_NO_WINDOW у GUI], NULL, NULL, &si, &pi)`. Std-хендли, які існують, позначаються успадковуваними (`SetHandleInformation`) і передаються через `STARTF_USESTDHANDLES`.
   - Job object з `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK`. Дочірній процес призначається в нього, якщо це вдалося, далі `ResumeThread`. Коли лаунчер убивають, Python не лишається сиротою.
   - Консольний варіант: `SetConsoleCtrlHandler` з обробником, що повертає `TRUE`. Ctrl+C отримує дочірній процес, а лаунчер чекає його завершення.
   - Лаунчер чекає дочірній процес і завершується з його кодом виходу.
   - Помилка запуску: повідомлення `Cannot start <command line>: <текст FormatMessageW>`, код 1. Консольний варіант пише в stderr (`WriteConsoleW`, а при перенаправленні — UTF-8 через `WriteFile`), GUI-варіант показує `MessageBoxW`.
4. **`generate_exe`.**
   - Сигнатура: `generate_exe(target, command, icon_file=None, show_console=True, architecture=PythonArchitecture.AMD64)`.
   - Шаблон обирається за `architecture` і `show_console`. Команда записується в UTF-16LE на місце маркера й доповнюється нулями до 1024 елементів.
   - `MAX_CMD_LENGTH = 1023`. Довша команда дає той самий `ValueError`, що й у задачі 05 (`Launcher command is N characters long; the limit is 1023: ...`), і файл не створюється.
   - Не-ASCII команди дозволені.
   - Якщо маркер у шаблоні не знайдено рівно один раз — `RuntimeError`.
   - Іконка, як і раніше, додається після запису (`add_icon_to_exe`).
   - `genexe_template`, `REPLACE_SIGNATURE` і прапорець `1`/`0` видаляються.
5. **`UVBuilder`** передає `architecture=self.config.python_architecture`. Формат команди не змінюється.
6. **Документація.** З `examples/hello-cli/README.md` прибрати застереження про лапки. Якщо задача 09 ще не виконана, звірити її пункт «Походження лаунчера» з тим, що вийшло.

## Сіми

- `generate_exe(...)` з `tmp_path`: байти результату (команда в UTF-16LE, PE-заголовок: `Machine` і `Subsystem`).
- Справжній запуск згенерованого лаунчера через `subprocess.Popen`/`run`:
  - команда `"<sys._base_executable>" "{EXE_DIR}\probe.py"`;
  - `_base_executable`, а не `sys.executable`, бо `python.exe` з `.venv` — перенаправлювач, який сам стартує базовий інтерпретатор дочірнім процесом;
  - `probe.py` лежить поруч із лаунчером і друкує JSON з `sys.argv[1:]`, `os.getppid()` і, на запит, stdin.
- `UVBuilder(config).build()` з підміненими `PydistManager`, `subprocess.run` і `generate_exe`, як у `tests/test_uv_builder.py`.

## Кроки

1. Вихідний код і збірка (рішення 1-3), без змін у Python:
   - `uv run --group launcher python launcher/build.py` створює шість шаблонів;
   - друга збірка з `--check` завершується з кодом 0;
   - `uv lock` оновлює `uv.lock`.
2. `tests/test_launcher.py` (маркер `windows`; кожен запуск триває десятки мілісекунд, тож тести не `slow`):
   - `test_launcher_passes_arguments_verbatim`, параметризований рядками таблиці з контексту плюс `["C:\\Program Files\\"]`, `["x\\\\", "y z\\"]`, `["привіт", "світ"]`. Очікується `argv == args`. У таблиці є `日本`, `😀` і `é ü ß`: вони ловлять повернення до вузьких рядків навіть на машині з кодовою сторінкою 1251.
   - Червоний етап: зі старим шаблоном команда з двома токенами в лапках не стартує взагалі, а локально з кириличним шляхом до інтерпретатора `generate_exe` падає з `UnicodeEncodeError`.
   - Зміна: рішення 4 для `amd64` і консольного варіанта.
3. `test_launcher_returns_child_exit_code` (проба завершується з кодом 3), `test_launcher_passes_stdin`, `test_launcher_starts_python_directly` (`os.getppid()` у пробі дорівнює `Popen.pid` лаунчера), `test_launcher_expands_exe_dir_with_spaces_and_non_ascii` (лаунчер у `tmp_path / "dir with space тест 日本"`).
4. `tests/test_generate_exe.py`:
   - `test_generate_exe_embeds_command_as_utf16` (команда з кирилицею, розмір дорівнює шаблону);
   - `test_generate_exe_picks_template_for_console_and_architecture`, параметризований шістьма парами, очікування `Machine` 0x8664 / 0x14C / 0xAA64 і `Subsystem` 3 / 2;
   - `test_generate_exe_rejects_command_longer_than_limit` перевести на 1100 символів (у повідомленні `1100` і `1023`).
5. GUI-варіант і `win32`: `test_launcher_passes_arguments_verbatim` і `test_launcher_returns_child_exit_code` параметризувати ще й за `(architecture, show_console)` для `amd64`/`win32` × console/GUI. `win32` на x64 працює через WOW64. `arm64` запускається лише на ARM64-машині (`pytest.mark.skipif(platform.machine() != "ARM64")`); на x64 його покриває крок 4.
6. `test_build_uses_launcher_for_python_architecture` (`tests/test_uv_builder.py`): конфігурація `win32` → `generate_exe` отримав `architecture=PythonArchitecture.WIN32`.
7. Прибрати `genexe_template` і застереження з `examples/hello-cli/README.md`; звірити задачу 09 (рішення 6).
8. CI (`.github/workflows/ci.yml`): крок `uv run --group launcher python launcher/build.py --check` після `uv sync --locked`.
9. Ручна перевірка:
   - `uv run pyretort build -p examples/hello-cli/pyproject.toml`; з іншої теки `examples\hello-cli\build\hello-cli-0.1.0-amd64\hello-cli.exe arg1 "two words" "a&b"` → `Arguments: ['arg1', 'two words', 'a&b']`; потім `uv run pyretort cleanup -p examples/hello-cli/pyproject.toml`.
   - `uv run pyretort build -p "examples/Simple RSS/pyproject.toml"`; подвійний клік на `simple-rss.exe` відкриває вікно без консолі.
   - `uv build` → у колесі шість файлів `pyretort/builder/exe_generator/templates/launcher-*` і немає `genexe_template`.
10. Критерій завершення з [README.md](README.md).

## Критерій завершення

- Тести з кроків 2-6 існують і проходять. `uv run pytest` і чотири команди з [README.md](README.md) зелені. `launcher/build.py --check` дає 0 локально і в CI.
- Ручні перевірки з кроку 9 виконано.
- У репозиторії немає `genexe_template`; у README hello-cli немає «Known limitation».
- Статус у [README.md](README.md) → DONE.

## Поза межами

- Підпис лаунчерів (Authenticode) — ні.
- Ресурс версії (VERSIONINFO) — ні.
- Зміни в `add_icon_to_exe` — ні.
- Standalone-режим — задача 12, але її формат команди з двома токенами в лапках після цієї задачі працює.

## Коміти

- `feat(exe): add launcher source with a reproducible zig build`
- `fix(exe): start the app without cmd.exe and pass arguments verbatim`
- `feat(exe): pick the launcher for the console flag and python architecture`
- `ci: check that launcher templates match their source`
- `docs(examples): drop the quoting limitation from hello-cli`

## Джерела

- `CreateProcessW`: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw
- Правила розбору командного рядка, `argv[0]`: https://learn.microsoft.com/en-us/cpp/c-language/parsing-c-command-line-arguments
- `GetCommandLineW`: https://learn.microsoft.com/en-us/windows/win32/api/processenv/nf-processenv-getcommandlinew
- Job objects, `JOBOBJECT_EXTENDED_LIMIT_INFORMATION`: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information
- `SetConsoleCtrlHandler`: https://learn.microsoft.com/en-us/windows/console/setconsolectrlhandler
- `ziglang` на PyPI: https://pypi.org/project/ziglang/ ; репозиторій пакування: https://codeberg.org/ziglang/zig-pypi
- `zig cc`, огляд: https://andrewkelley.me/post/zig-cc-powerful-drop-in-replacement-gcc-clang.html ; `-municode` у zig: https://github.com/ziglang/zig/pull/19399
- Вихідний код шаблону gen-exe: https://github.com/silvandeleemput/gen-exe/blob/0.2.1/exe_template/exe_template.cpp
- `system()` і правила лапок `cmd /c`: https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/system-wsystem ; https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd
- Лаунчер distlib: https://github.com/vsajip/simple_launcher/blob/master/launcher.c ; uv trampoline: https://github.com/astral-sh/uv/blob/main/crates/uv-trampoline/src/bounce.rs
- Чому повторне взяття аргументів у лапки ненадійне: https://learn.microsoft.com/en-us/archive/blogs/twistylittlepassagesallalike/everyone-quotes-command-line-arguments-the-wrong-way
