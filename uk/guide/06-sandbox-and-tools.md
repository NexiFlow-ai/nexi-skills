# 6 · Пісочниця та інструменти

Два місця, де агент торкається світу поза розмовою: **інструмент** (дія з контрактом) і **пісочниця** (де може
виконуватися код, який написала модель). Обидва належать платформі; пак називає, що йому потрібно, і встановлює межі.

## Інструменти

Інструмент — це uri з контрактом: операція, схема входу, схема виходу, прапорець `mutating`, обов'язкова стеля
класифікації. Три родини:

| Родина | Приклади | Звідки |
|---|---|---|
| **Платформні інструменти** | `nexus://tool/project.search` · `project.file_read` · `blob.read_text` · `knowledge.search` · `artifact.create_document` · `artifact.create_table` · `artifact.create_chart` · `artifact.publish` · `dataset.query` · `dataset.describe` · `sandbox.run_python` · `task.create` · `flow.run` · `web.map` · `web.fetch` · `web.extract` · `capability.inventory` · `rights.dryrun` · … | Розгортання. [`policies/tool-groups.json`](../../packs/nexus-base/policies/tool-groups.json) групує їх так, як бачить людина. |
| **Підключені інструменти** | `nexus://tool/<connection>.<operation>` — пошук у CRM, читання тікета, SQL-запит | Підключення, яке Адміністратор створив у NexCore › Connections із `connector_kind`. Пак каже `requires.connections: [{ name, tool_uri, optional }]`; розгортання прив'язує. |
| **Інструменти будівельника** | `state.read` · `plan.step` · … | Ними може користуватися лише резолвер платформи (`tool_policy.builder_only`). Ніколи не ваші. |

Те, що агент отримує на хід чи вузол, — перетин: `tool_policy.allowlist` blueprint → `policy.allowed_tool_uris` Flow
(або, у розмові, політика інструментів Проєкту) → власні прив'язки `tools` агента → **дозволи та підключення людини**,
бо кожен виклик виконується від її імені (`run_as: initiator`). Інструмент, який пак називає, а розгортання не
обслуговує, — *недоступний*, і так і каже: `tool-groups.json` позначає `available: false` саме з цієї причини. Агент,
якому бракує інструмента, не вдає; він відповідає потребою в можливості (розділ 3).

### Дисципліна вузла інструмента

- `mutating: true` на всьому, що створює, змінює, надсилає чи видаляє. Саме на це спираються погодження.
- `idempotency.key_template` на кожному мутуючому вузлі — `"document-review:{{run_id}}"` — з `dedupe_window_s`.
  Повторений вузол не має створити другий документ.
- `retry` з обмеженим `max_attempts` і backoff; `timeout_s` завжди.
- `policy.purpose` каже *чому* одним словом, про яке точка прийняття політики може міркувати (`read`, `save`,
  `classification`, `weekly_brief`).
- Ніколи облікових даних у мапінгу, шаблоні чи інструкції. У паку немає місця, де секрет доречний; маніфест так і
  каже (`contains_secrets: false`), а guard, який публікує паки, їх шукає.

## Пісочниця

Код, написаний моделлю, виконується **лише** в пісочниці, через `sandbox.run_python`, під **профілем**. Без хостової
оболонки, без облікових даних, без прямої мережі. Ноутбук — формат артефакту, а не межа виконання.

Еталон: [`sandbox/public-dev.json`](../../packs/nexus-base/sandbox/public-dev.json).

```json
{
  "profile_id": "public-dev",
  "uri": "nexus://sandbox/profile/public-dev",
  "name": "Public dev sandbox",
  "layer": "base",
  "runtimes": ["python"],
  "network": { "policy": "none" },
  "packages": { "policy": "allowlist_only", "allowlist": ["numpy", "pandas", "scipy", "scikit-learn", "pyarrow", "openpyxl"] },
  "limits": { "cpu_millicores": 1000, "memory_mb": 512, "timeout_s": 120, "max_output_mb": 8, "max_artifacts": 10, "max_concurrent_per_run": 1 },
  "isolation": { "host_filesystem": "none", "credentials": "none", "input_datasets": "read_only", "artifact_dir": "writable", "ephemeral": true, "isolation_backend": "container-seccomp" },
  "classification_max": "confidential",
  "image": { "ref": "nexus-sandbox-python:0.6" },
  "audit": { "enabled": true, "retain_stdout_days": 30, "retain_code_days": 30 },
  "version": "1.1.3",
  "created_at": "2026-09-10T00:00:00Z"
}
```

| Блок | Що обмежує |
|---|---|
| `network.policy` | `none` у кожному профілі, який постачає Nexi. Профіль із вихідним трафіком — рішення розгортання, ніколи не типове значення пака. |
| `packages` | `allowlist_only` з пакетами, вбудованими в образ. Код може імпортувати їх і нічого іншого. |
| `limits` | CPU, пам'ять, час, розмір виходу, кількість артефактів, паралельність — на запуск. |
| `isolation` | Без хостової файлової системи, без облікових даних, датасети лише для читання, один записуваний каталог артефактів, ефемерно, контейнер під seccomp. |
| `classification_max` | Найвищі дані, які профіль може отримати. Профіль `confidential-analytics` у Nexi Base існує для наступного рівня, з жорсткішими межами. |
| `audit` | Код і stdout зберігаються впродовж вікна аудиту. |

Flow називає свій профіль у `policy.sandbox_profile_uri`; вузол може назвати жорсткіший у `sandbox_profile_uri`;
blueprint називає типовий. Правило те саме, що й усюди: **дитина може посилити, ніколи не послабити.**

### Коли пак постачає профіль

Коли ваші Flow виконують аналізи, яким потрібен пакет, якого бракує в базовому образі, або інша стеля. Постачайте
профіль із чесним `classification_max` і найменшими `limits`, які роблять роботу, і знайте, що розгортання може не
мати образу, який ви називаєте: `image.ref` — запит, який оператор задовольняє або відхиляє.

## Що ніколи не постачається в паку

- Виконуваний код будь-якого виду — без скриптів, без реалізацій інструментів, без ноутбуків як середовищ виконання.
- URL, hostname, рядок підключення, ключ, токен, сертифікат — навіть заповнювач, який на них схожий.
- Ідентифікатор моделі. Роль із можливостями та нижньою межею якості — весь словник.
- Надання дозволу. Пак *просить* (інструменти, підключення, ролі); розгортання й людина *надають*.
