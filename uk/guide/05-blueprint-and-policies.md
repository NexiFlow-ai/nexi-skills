# 5 · Шар blueprint і політики

Blueprint — це шар, який встановлює пак: що організація отримує типово, чим можуть користуватися її агенти, які моделі
що можуть бачити, коли людина має погоджувати, як довго речі зберігаються. Кожен пак постачає рівно один. Політики
поруч із ним — прості документи, які читають blueprint і застосунки.

Еталон: [`blueprints/nexus-base.json`](../../packs/nexus-base/blueprints/nexus-base.json) та
[`policies/`](../../packs/nexus-base/CATALOGUE.md#blueprint-policies-sandbox-profiles-dashboard-templates).

## Blueprint

```json
{
  "blueprint_id": "nexus-base",
  "uri": "nexus://core/blueprint/nexus-base",
  "name": "Nexi Base",
  "layer": "base",
  "version": "1.12.0",
  "status": "published",
  "source_pack_uri": "nexus://core/pack/nexus-base",
  "deployment_targets": ["on_prem", "azure", "disconnected"],
  "defaults": {
    "agents": ["nexus://agent/agt_general", "nexus://agent/agt_analyst", "…"],
    "skills": ["nexus://skill/skl_summarize_sources", "…"],
    "flows": { "document_review": "nexus://workflow/template/flw_tpl_document_review", "weekly_digest": "…", "member_onboarding": "…", "admin_governance": "…" },
    "general_agent_uri": "nexus://agent/agt_general",
    "suggested_capabilities": ["Summarize a document", "Analyse a spreadsheet", "Extract a table from a contract", "…"],
    "projects": [{ "role": "data_science", "name": "Data science", "description": "…", "flows": ["ads"] }]
  },
  "tool_policy": { "allowlist": ["nexus://tool/project.search", "nexus://tool/project.file_read", "nexus://tool/artifact.create_document", "…"], "side_effect_requires_approval": true },
  "model_policy": {
    "allowed_endpoint_kinds": ["local", "contour", "cloud"],
    "max_classification_for_cloud": "confidential",
    "max_tier": 3,
    "allow_explicit_model": false,
    "default_quality_min": { "reasoner": 0.6, "extractor": 0.6, "classifier": 0.5, "chat": 0.5, "coder": 0.6, "planner": 0.6, "evaluator": 0.6 }
  },
  "sandbox_profile_uri": "nexus://sandbox/profile/public-dev",
  "approvals": { "external_write_threshold": "confidential", "goal_completion_requires_human": true, "capability_request_approver": "owner", "package_request_approver": "owner", "allow_self_approval": false },
  "retention": { "artifact_days": 730, "run_days": 365, "sandbox_output_days": 90 },
  "tuning": { "auto": { "…": "…" } },
  "governance": { "state": "approved" },
  "created_at": "2026-09-17T00:00:00Z"
}
```

| Блок | Що вирішує |
|---|---|
| `layer` · `parent_uri` | `base` · `domain` · `organization` · `project`. Доменний шар називає базовий як `parent_uri` і **посилює** його. Нічого з того, що каже дитина, не може послабити батька. |
| `defaults.agents` · `skills` | Що активне в новій організації. Усе назване має постачати цей пак або пак, від якого він залежить — інакше тулкіт попереджає. |
| `defaults.flows` | Шаблони Flow за **роллю** (`document_review`, `weekly_digest`, `member_onboarding`, `admin_governance`, …). Платформа запускає Flow за роллю: ваш `admin_governance` замінює базовий для організацій на вашому шарі. |
| `defaults.general_agent_uri` | Хто відповідає, коли нічого не маршрутизується. Лишіть базовому, якщо ваш шар не *є* іншим видом організації. |
| `defaults.suggested_capabilities` | Речення, які нова людина бачить як підказки — словами людини, дієслово спершу. |
| `defaults.projects` | Наперед визначені Проєкти, які отримує нова організація, із Flow, які в них запускати. |
| `tool_policy.allowlist` | **Стеля для кожного агента й Flow в організації.** Інструмента, якого тут немає, для них не існує. `side_effect_requires_approval` ставить людину перед будь-яким мутуючим інструментом. `builder_only` називає інструменти, якими може користуватися лише резолвер. |
| `model_policy` | Які види ендпоїнтів (`local` · `contour` · `cloud`) і до якої класифікації дані можуть іти в хмару; стеля рівня; чи може людина обрати модель за назвою (`allow_explicit_model: false` — ролі, не вендори); нижня межа якості на роль. |
| `sandbox_profile_uri` | Де типово виконується код, написаний моделлю. |
| `approvals` | `external_write_threshold` — від якої класифікації зовнішній запис потребує погодження; `goal_completion_requires_human`; хто погоджує запити можливостей і пакетів; `allow_self_approval: false`. |
| `retention` | Як довго живуть артефакти, запуски й вихід пісочниці. |
| `tuning` | Ручки поведінок платформи, які шару дозволено налаштовувати (пороги маршрутизації розмови, бюджети дослідження). Рідко ваші. |
| `guardrails` · `evaluations` · `modules` · `analysis` | Набори guardrail, набори оцінок, модулі suite, які вмикає модульний пак, налаштування аналізу. |

### Шари посилюють

Припустімо, Nexi Base дозволяє `cloud`-ендпоїнти до `confidential`. Ваш доменний шар для юридичної практики може
сказати `allowed_endpoint_kinds: ["local", "contour"]` — тоді кожна організація на вашому шарі тримає все всередині.
Він *не* може сказати `max_classification_for_cloud: secret`; розгортання відмовляє дитині, яка послаблює батька. Так
само для allow-list інструментів (підмножина), погоджень (нижчий поріг), стель класифікації (нижчі), зберігання
(коротше).

## Політики

Ресурс `policy` — JSON-документ із `kind`. Базовий пак постачає п'ять; ваш може постачати власні тих самих видів або
нових видів, які читають ваші застосунки.

| `kind` | Що містить | Хто читає |
|---|---|---|
| `tool_groups` | Платформні інструменти, згруповані так, як їх бачить людина — *Документи · читання й розбір*, *Артефакти*, *Дані*, … — з `enabled` (постачається увімкненим у цьому шарі) та `available` (платформний інструмент справді його виконує — *чесно, не приховано*). | Сторінка інструментів NexCore; пояснення маршрутизації можливостей. |
| `connector_kinds` | **Види** підключень, які організація може створювати — PostgreSQL, REST/OpenAPI, MCP, файли, вебхуки — з протоколом і типом облікових даних. *Без екземплярів, без ендпоїнтів, без облікових даних.* | NexCore › Connections. |
| `model_roles` | Ролі, на які маршрутизує пак, які агенти використовують кожну, найвища класифікація, яку може бачити модель ролі, потрібні можливості. *Без ідентифікаторів вендорів.* | Сторінка прив'язок шлюзу моделей. |
| `skill_sensitivity` | `max_input_classification` на навичку; `recommended` навички. | Розмова, перед застосуванням навички. |
| `kpis` | Що організація вимірює про власне використання. | Платформні дашборди NexBI. |

Патерн щоразу той самий: **пак називає вид, розгортання прив'язує екземпляр.** Пак ніколи не знає hostname,
ідентифікатора моделі, API-ключа чи тенанта.

## Що має містити ваш шар

Для доменного пака зазвичай:

- `defaults.agents` і `skills`: ваші агенти й навички плюс базові, на які ви спираєтеся (General базового лишається
  General).
- `defaults.flows`: ваші Flow за роллю; перекривайте базову роль лише тоді, коли ваш — кращий типовий для вашої галузі.
- `tool_policy.allowlist`: **підмножина** базового — рівно те, що використовують ваші агенти й Flow. Тулкіт друкує
  список в `install --dry-run`; порівняйте з `requires.platform_tools` у маніфесті; вони мають збігатися.
- `model_policy`: посильте, якщо галузь вимагає; інакше успадкуйте, повторивши базове.
- `approvals`: посильте, якщо ваші Flow пишуть поза Nexi.
- Політика `skill_sensitivity` для ваших навичок; політика `model_roles`, якщо ви додаєте ролі; політика
  `connector_kinds`, якщо вашим Flow потрібен вид підключення (`requires.connections` у маніфесті називає uri
  інструмента; політика виду називає протокол).
