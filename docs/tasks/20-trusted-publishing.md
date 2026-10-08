# 20. Публікація на PyPI без токенів: trusted publishing з GitHub Actions

Залежить від: 08, 09. Оцінка: S.

## Мета

Push тегу `vX.Y.Z` збирає пакет на GitHub Actions і після підтвердження користувачем публікує його на PyPI через trusted publishing: ні в репозиторії, ні в GitHub, ні на машині розробника немає жодного токена PyPI. Увесь шлях перевірено на TestPyPI до першого справжнього релізу (задача 11).

## Контекст

Перевірено 8 жовтня 2026.

- **Чому так.** Користувач хоче публікувати без токенів. Задача 11 спершу планувала `uv publish` з токеном у `UV_PUBLISH_TOKEN` і виключала публікацію з CI; тепер публікацію переносить сюди, а задача 11 лише робить перший справжній запуск.
- **Trusted publishing.** PyPI довіряє OIDC-токену, який GitHub видає конкретному workflow-файлу конкретного репозиторію (і, якщо задано, конкретному environment). Job отримує такий токен лише з дозволом `id-token: write`. `uv publish` у GitHub Actions сам обмінює його на короткоживучий токен PyPI.
- **Репозиторій** `github.com/ruslan-rv-ua/PyRetort` з 8 жовтня 2026 публічний (`gh repo view --json visibility` → `PUBLIC`). Лише для публічних репозиторіїв на безкоштовному тарифі GitHub працюють обов'язкові reviewers в environment і обмеження environment за гілками й тегами. Environments у репозиторії ще немає (`gh api repos/ruslan-rv-ua/PyRetort/environments` порожній). Числовий id користувача `ruslan-rv-ua` — `57788420` (`gh api users/ruslan-rv-ua --jq .id`).
- **PyPI і TestPyPI.**
  - У користувача є акаунт PyPI `ruslan.rv.ua` (https://pypi.org/user/ruslan.rv.ua/). TestPyPI — окремий сайт з окремим акаунтом; чи є він, невідомо.
  - Назва `pyretort` вільна на обох (`https://pypi.org/pypi/pyretort/json` і `https://test.pypi.org/pypi/pyretort/json` → 404).
  - Проєкту ще немає, тому trusted publisher додається як **pending publisher** у налаштуваннях акаунта (Account settings → Publishing): назва проєкту, owner, repository, workflow filename, environment. Pending publisher назву не резервує: якщо хтось зареєструє `pyretort` раніше, він стає недійсним. Після першої публікації він стає звичайним trusted publisher проєкту.
  - PyPI ніколи не приймає вдруге файл з тим самим ім'ям, навіть після видалення. Тому репетиція на TestPyPI публікує dev-версії (`0.1.0.dev1`, `0.1.0.dev2`, …), а не `0.1.0`.
- **Обмеження trusted publishing.** Reusable workflow (`workflow_call`) не може бути workflow trusted publisher'а (документація PyPI, warehouse#11096). Тому job-и публікації живуть у самому `release.yml`; перевірки можна викликати з `ci.yml`, бо вони нічого не публікують.
- **Події GitHub.**
  - `workflow_dispatch` спрацьовує, лише якщо workflow-файл є в гілці за замовчуванням (`develop`). Тому репетицію на TestPyPI можна запустити лише після злиття цієї задачі в `develop` і push.
  - Для тегів подія не створюється, якщо за раз запушено більше трьох тегів. `git push origin main develop --follow-tags` із задачі 11 пушить один анотований тег.
  - У reusable workflow контекст `github` належить викликачу: `github.workflow` у викликаному `ci.yml` дорівнює `Release`, а `github.ref` — ref викликача.
- **`ci.yml`** ([.github/workflows/ci.yml](../../.github/workflows/ci.yml)) запускається на push у `develop` і `main`, на pull request і вручну; `workflow_call` немає. Група concurrency — `ci-${{ github.ref }}` з `cancel-in-progress: true`. Якщо викликати `ci.yml` з `release.yml`, запущеного вручну на `develop`, група збігається з групою звичайного прогону CI на `develop`, і один прогін скасовує інший.
- **Збірка — лише на Windows.** `pyretort` перевіряє платформу при запуску і залежить від `pywin32`, тож smoke test (`pyretort version` з колеса і sdist) можливий лише на `windows-latest`. Публікація лише завантажує готові файли, тому її job працює на `ubuntu-latest`. Shell для `run` на Windows-runner — PowerShell: збій нативної команди посеред скрипту сам не зупиняє крок, тому `$LASTEXITCODE` перевіряється явно.
- **Чистий checkout.** CI збирає з чистого checkout, тому пастка з `.kilo/` у sdist (контекст задачі 11) тут не виникає.
- **uv 0.12.23.**
  - `uv publish` за замовчуванням бере `dist/*`, відбирає лише колеса, sdist і їхні атестації; `--trusted-publishing always` вимагає trusted publishing і падає, якщо OIDC недоступний; `--publish-url` задає адресу завантаження (для TestPyPI — `https://test.pypi.org/legacy/`).
  - `uv version --frozen <версія>` змінює версію в `pyproject.toml` без перебудови `uv.lock` (`uv version 0.1.0.dev1 --frozen --dry-run` → `pyretort 0.1.0 => 0.1.0.dev1`).
  - `uv version --short` друкує лише версію. `uv run pyretort version` друкує `PyRetort 0.1.0`.
- **Атестації PEP 740.** Приклад workflow з документації uv генерує їх кроком `astral-sh/attest-action` у job публікації, а `uv publish` завантажує їх разом із файлами. PyPI приймає атестації лише від trusted publishing.
- **Версії дій** (SHA перевірено через `gh api repos/<repo>/git/ref/tags/<тег>`):
  - `actions/checkout` v7.0.1 — `3d3c42e5aac5ba805825da76410c181273ba90b1`;
  - `astral-sh/setup-uv` v10.2.0 — `c18668ad3cf93ea998bef934396af7bb5c839dc7` (той самий, що в `ci.yml`);
  - `actions/upload-artifact` v7.0.1 — `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (є v7.0.2 від 7 жовтня 2026);
  - `actions/download-artifact` v8.0.1 — `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` (є v8.0.2 від 7 жовтня 2026);
  - `astral-sh/attest-action` v0.0.6 — `f589a42a7efb6fe400b4f400de60b4bc90390027`.
- Створення environments, push і публікація — зовнішні дії: лише з явної згоди користувача в поточній сесії. Акаунти й pending publishers на PyPI і TestPyPI користувач додає сам у браузері.

## Рішення

1. **`ci.yml`:** додати `workflow_call:` до `on` і змінити групу concurrency на `${{ github.workflow }}-${{ github.ref }}`. Для звичайних прогонів група стає `CI-<ref>`, для викликаних із `release.yml` — `Release-<ref>`, і вони більше не скасовують одна одну.
2. **Новий `.github/workflows/release.yml`:**

   ```yaml
   name: Release

   on:
     push:
       tags:
         - "v[0-9]+.[0-9]+.[0-9]+"
     workflow_dispatch:
       inputs:
         version:
           description: "Version for TestPyPI, for example 0.1.0.dev1"
           required: true
           type: string

   permissions: {}

   concurrency:
     group: publish-${{ github.ref }}
     cancel-in-progress: false

   jobs:
     checks:
       uses: ./.github/workflows/ci.yml
       permissions:
         contents: read

     build:
       needs: checks
       runs-on: windows-latest
       permissions:
         contents: read
       steps:
         - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
           with:
             persist-credentials: false
         - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
           with:
             python-version: "3.13"
             enable-cache: false
         - name: Set the TestPyPI version
           if: github.event_name == 'workflow_dispatch'
           env:
             VERSION: ${{ inputs.version }}
           run: uv version --frozen "$env:VERSION"
         - name: Check that the tag matches the version
           if: github.event_name == 'push'
           run: |
             $version = uv version --short
             if ("v$version" -ne $env:GITHUB_REF_NAME) {
               throw "Tag $env:GITHUB_REF_NAME does not match version $version in pyproject.toml"
             }
         - run: uv build --no-sources
         - name: Smoke test the wheel and the sdist
           run: |
             $expected = "PyRetort $(uv version --short)"
             $dists = @(Get-ChildItem dist -File | Where-Object Name -Match '\.(whl|tar\.gz)$')
             if ($dists.Count -ne 2) { throw "Expected a wheel and an sdist, got: $($dists.Name)" }
             Push-Location $env:RUNNER_TEMP
             foreach ($dist in $dists) {
               $out = uv run --isolated --no-project --with $dist.FullName -- pyretort version
               if ($LASTEXITCODE -ne 0 -or $out -ne $expected) {
                 throw "$($dist.Name): expected '$expected', got '$out'"
               }
             }
             Pop-Location
         - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
           with:
             name: dist
             path: dist/

     publish-testpypi:
       if: github.event_name == 'workflow_dispatch'
       needs: build
       runs-on: ubuntu-latest
       environment:
         name: testpypi
         url: https://test.pypi.org/project/pyretort/
       permissions:
         id-token: write
       steps:
         - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
           with:
             enable-cache: false
         - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
           with:
             name: dist
             path: dist/
         - uses: astral-sh/attest-action@f589a42a7efb6fe400b4f400de60b4bc90390027 # v0.0.6
         - run: uv publish --trusted-publishing always --publish-url https://test.pypi.org/legacy/

     publish-pypi:
       if: github.event_name == 'push'
       needs: build
       runs-on: ubuntu-latest
       environment:
         name: pypi
         url: https://pypi.org/project/pyretort/
       permissions:
         id-token: write
       steps:
         - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
           with:
             enable-cache: false
         - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
           with:
             name: dist
             path: dist/
         - uses: astral-sh/attest-action@f589a42a7efb6fe400b4f400de60b4bc90390027 # v0.0.6
         - run: uv publish --trusted-publishing always
   ```

   - Вхід `version` потрапляє в скрипт лише через змінну середовища, а не через `${{ }}` у тексті скрипту: так рядок із форми не стає кодом PowerShell.
   - Права: на рівні workflow — жодних; `contents: read` для перевірок і збірки; `id-token: write` лише в job-ах публікації, які нічого не збирають (рекомендація uv і PyPI).
   - Групи concurrency `publish-<ref>` і `Release-<ref>` (з рішення 1) різні, тож викликаний `ci.yml` не чекає на свого викликача.
   - Дії закріплено за SHA з контексту. Новіший патч дії можна взяти, перевіривши SHA тим самим `gh api`.
3. **Environments у GitHub:**
   - `pypi`: обов'язковий reviewer — `ruslan-rv-ua`, `prevent_self_review: false` (користувач працює сам і підтверджує власні запуски); розгортання лише з тегів `v*`;
   - `testpypi`: без reviewers, розгортання лише з гілки `develop`.
4. **Pending publishers** (додає користувач): PyPI project name `pyretort`, owner `ruslan-rv-ua`, repository `PyRetort`, workflow `release.yml`, environment `pypi`; на TestPyPI — те саме з environment `testpypi`. Значення мають збігатися з workflow і environments дослівно.
5. **Атестації** генеруються в обох job-ах публікації, щоб репетиція перевірила той самий шлях. Якщо TestPyPI їх відхилить, крок `attest-action` прибирається лише з `publish-testpypi`, а причина записується в цю задачу.
6. **GitHub-реліз** workflow не створює: задача 11 робить його вручну, прикріплюючи файли з артефакту `dist` цього прогону, тобто ті самі, що пішли на PyPI.
7. **AGENTS.md**, розділ «Гілки: git flow», пункт «Реліз»: дописати, що push тегу `vX.Y.Z` запускає `.github/workflows/release.yml`, а публікацію на PyPI користувач підтверджує в GitHub (environment `pypi`, Review deployments). Токенів PyPI проєкт не використовує.

## Сіми

Тестів немає. Перевірки: синтаксис workflow локально, команди job-а `build` локально, справжній прогін на TestPyPI.

## Кроки

1. Перевірити, що назва досі вільна: `https://pypi.org/pypi/pyretort/json` і `https://test.pypi.org/pypi/pyretort/json` → 404. Якщо ні — зупинитися й спитати користувача.
2. Попросити користувача додати pending publishers (рішення 4) і дочекатися підтвердження. Якщо акаунта на test.pypi.org немає, його треба зареєструвати й увімкнути двофакторну автентифікацію.
3. `git flow feature start 20-trusted-publishing`. Рішення 1 і 2. Перевірити:
   - YAML: `uv run --no-project --with pyyaml python -c "import yaml; [yaml.safe_load(open(f)) for f in ('.github/workflows/ci.yml', '.github/workflows/release.yml')]"`;
   - вирази й права: `uvx --from actionlint-py actionlint` (обгортка над actionlint); якщо вона не встановлюється — пропустити й сказати про це.
4. Локально повторити кроки job-а `build` у PowerShell:
   - `uv version 0.1.0.dev1 --frozen --dry-run` показує `0.1.0 => 0.1.0.dev1`;
   - `uv build --no-sources -o <scratchpad>\dist`;
   - скрипт smoke test з рішення 2 (з `dist` у scratchpad) нічого не кидає.

   `pyproject.toml` і `uv.lock` після цього не змінені (`git status`).
5. Рішення 7 (AGENTS.md).
6. Показати користувачу команди для environments (рішення 3) і виконати після згоди:
   - `gh api -X PUT repos/ruslan-rv-ua/PyRetort/environments/pypi --input <json>` з `{"reviewers":[{"type":"User","id":57788420}],"prevent_self_review":false,"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}`, потім `gh api -X POST repos/ruslan-rv-ua/PyRetort/environments/pypi/deployment-branch-policies -f name="v*" -f type=tag`;
   - `testpypi`: той самий PUT без `reviewers` і `prevent_self_review`, політика `-f name=develop -f type=branch`;
   - перевірка: `gh api repos/ruslan-rv-ua/PyRetort/environments --jq '.environments[] | {name, protection_rules}'`.
7. Статус задачі → DONE тим самим комітом, що й рішення 7. Тут перевірка на GitHub можлива лише після злиття (див. «Контекст», `workflow_dispatch`), тому статус ставиться до репетиції, як у задачі 08.
8. Спитати користувача про `git flow feature finish --no-ff --no-push 20-trusted-publishing` і `git push origin develop`; виконати після згоди.
9. Репетиція:
   - `gh workflow run release.yml --ref develop -f version=0.1.0.dev1`, потім `gh run watch` (або `gh run view --log-failed` при збої);
   - сторінка https://test.pypi.org/project/pyretort/0.1.0.dev1/: опис із README з логотипом, посилання з `[project.urls]` відкриваються;
   - встановлення: URL колеса з `https://test.pypi.org/pypi/pyretort/0.1.0.dev1/json` (поле `urls`, `packagetype` = `bdist_wheel`), далі `uv run --isolated --no-project --with <URL> -- pyretort version` → `PyRetort 0.1.0.dev1`. Колесо береться за прямим URL, а залежності — з PyPI: з `--index https://test.pypi.org/simple/` uv за стратегією `first-index` брав би залежності з TestPyPI;
   - атестація: `GET https://test.pypi.org/integrity/pyretort/0.1.0.dev1/pyretort-0.1.0.dev1-py3-none-any.whl/provenance` → 200.
10. Якщо прогін червоний — виправлення в новій feature-гілці від `develop` і повтор з `0.1.0.dev2`.

## Критерій завершення

- `ci.yml` і `release.yml` у `develop` за рішеннями 1 і 2; перевірки з кроку 3 проходять.
- Environments `pypi` (reviewer `ruslan-rv-ua`, лише теги `v*`) і `testpypi` (лише `develop`) існують.
- На TestPyPI є `pyretort` з dev-версією: колесо, sdist і атестація; колесо встановлюється й друкує свою версію.
- На PyPI проєкту `pyretort` досі немає: перша справжня публікація — задача 11.
- AGENTS.md описує публікацію через `release.yml`.
- Чотири команди з [README.md](README.md) — за його правилами. Статус задачі в [README.md](README.md) — DONE.

## Поза межами

- Перша публікація на PyPI і GitHub-реліз — задача 11.
- Створення GitHub-релізу в workflow (рішення 6).
- Пре-релізні теги (`v0.2.0rc1`, `v0.2.0a1`): шаблон тегу додається, коли знадобиться перший такий реліз.
- Правила захисту тегів (rulesets): писати в репозиторій може лише його власник.

## Коміти

- `ci: let the release workflow reuse the ci checks`
- `ci: publish releases to pypi with trusted publishing`
- `docs(agents): describe publishing through the release workflow`

## Джерела

- PyPI, trusted publishers: https://docs.pypi.org/trusted-publishers/
- PyPI, створення проєкту через pending publisher: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
- PyPI, модель безпеки trusted publishing: https://docs.pypi.org/trusted-publishers/security-model/
- PyPI, обмеження (reusable workflows): https://docs.pypi.org/trusted-publishers/troubleshooting/
- PyPI, атестації та Integrity API: https://docs.pypi.org/attestations/producing-attestations/ ; https://docs.pypi.org/api/integrity/
- uv, публікація з GitHub Actions: https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi
- uv, build & publish: https://docs.astral.sh/uv/guides/package/
- GitHub, environments і правила розгортання: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- GitHub, події `workflow_dispatch` і `push`: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- GitHub, reusable workflows (контекст `github` викликача, concurrency, права `GITHUB_TOKEN`): https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
- GitHub REST, environments: https://docs.github.com/en/rest/deployments/environments ; політики гілок і тегів: https://docs.github.com/en/rest/deployments/branch-policies
- actionlint-py: https://github.com/Mateusz-Grzelinski/actionlint-py
