# 4 · Flows

Flow — це оркестрація: тригер, граф вузлів, ребра між ними й політика. Рушій виконує граф; повторює те, що ви сказали
повторювати, дедуплікує те, що ви позначили ключем, чекає на людину, яку ви назвали, застосовує межі, які ви встановили,
— і нічого не знає про ваш домен. Усе доменне — в агентах та інструментах, які викликають вузли.

Пак постачає Flows як **шаблони**: `project_id` дорівнює `null`, `template.is_template` — `true`, і людина створює
екземпляр у Проєкті (з `parameters` шаблону) — або blueprint називає його під роллю, і платформа запускає його сама.

Еталон: [`flows/document-review.json`](../../packs/nexus-base/flows/document-review.json) — прочитати, класифікувати,
перевірити, погодити, якщо конфіденційно, зберегти, повідомити.

## Форма

```json
{
  "spec_version": "1.1",
  "workflow_id": "flw_tpl_document_review",
  "uri": "nexus://workflow/template/flw_tpl_document_review",
  "tenancy": { "enterprise_id": "nexus", "tenant_id": "platform" },
  "project_id": null,
  "name": "Document review",
  "description": "…",
  "version": 1,
  "status": "published",
  "classification": "confidential",
  "template": { "is_template": true, "source_pack_uri": "nexus://core/pack/nexus-base", "source_template_version": "1.0.0", "parameters": [] },
  "requires": { "models": [{ "role": "extractor" }, { "role": "reasoner" }], "tools": ["nexus://tool/project.file_read", "nexus://tool/artifact.create_document"] },
  "trigger": { "kind": "manual" },
  "inputs": [{ "name": "document", "type": "file", "required": true, "description": "The Project attachment to review" }],
  "outputs": [{ "name": "review", "type": "resource_uri" }],
  "nodes": [ … ],
  "edges": [ … ],
  "policy": {
    "approval_for_external_writes": false,
    "max_run_duration_s": 604800,
    "allowed_tool_uris": ["nexus://tool/project.file_read", "nexus://tool/artifact.create_document"],
    "run_as": "initiator",
    "sensitive_outputs": [],
    "max_loop_depth": 1,
    "sandbox_profile_uri": "nexus://sandbox/profile/public-dev"
  },
  "governance": { "state": "approved", "reviewed_at": "2026-09-17T00:00:00Z" },
  "security_review": { "state": "not_required" },
  "created_by": "pack:nexus-base",
  "created_at": "2026-09-17T00:00:00Z"
}
```

## Тригери

| `trigger.kind` | Спрацьовує, коли | Приклад |
|---|---|---|
| `manual` | Людина запускає з треду або зі сторінки Flow, з `inputs`. | Document review |
| `schedule` | `schedule_cron` у `schedule_timezone`. | Тижневий дайджест: `0 8 * * 1`, `Europe/Kyiv` |
| `event` | Подія платформи на `event_subject`, за потреби звужена `event_filter` (вираз над `$.event`). | Онбординг учасника на `nexus.core.organization.membership.granted.v1`; BI-сповіщення на `nexus.bi.dataset_version.published.v1`, відфільтроване до одного датасету |
| `webhook` · `subflow` | Зовнішній виклик через підключення; інший Flow. | |

У запуску від події немає треду: його результат — вихід запуску, видимий на сторінці запуску; вузол `notify` у
`{{run.thread_id}}` там нічого не робить. Онбординг учасника в Nexi Base каже це у власному описі.

## Вузли

Кожен вузол має `id`, `kind`, `label` і може мати `timeout_s`, `retry`, `idempotency`, `policy` (`pep_action`,
`purpose` — слова, які бачить точка прийняття політики), `on_failure`, `compensation_node_id`, `input_mapping`.

| `kind` | Навантаження | Що робить |
|---|---|---|
| `trigger` · `end` | — | Кожен Flow починається з одного тригера й закінчується в `end`. |
| `agent` | `agent.agent_uri` · `skill_uris` · `context_scope` (`project` · `thread` · `none`) · `output_schema` | Викликає агента на один крок. **Завжди давайте `output_schema`**: рушій валідує відповідь, і наступний вузол читає іменовані поля, а не прозу. |
| `tool` | `tool.tool_uri` · `operation` · `mutating` | Викликає платформний або підключений інструмент. `mutating: true` — те, на що спираються погодження та `approval_for_external_writes`; мутуючий вузол несе `idempotency`. |
| `condition` | `condition.language: nexus-expr-v1` · `source` | Булевий вираз над станом запуску: `$.node.classify.output.classification != 'public'`. Ребра з нього несуть `when: "true"` / `"false"`. |
| `approval` | `approval.approver` (`{ "relation": "owner" }` …) · `title_template` · `on_timeout` | Чекає на людину. Ребра несуть `when: "approved"` / `"rejected"`. Погодження — задача, яку людина бачить у своїй скриньці. |
| `human_task` | означення задачі | Робота для людини всередині запуску. |
| `loop` | `loop.entry_node_id` · `body_node_ids` · `until` · `max_iterations` · `max_duration_s` · `budget` · `on_no_progress` · `no_progress_after` | Нижче. |
| `evaluator` | `evaluator.kind` (`deterministic` · `model`) · `criteria_source` · `metrics_path` | Суддя циклу. |
| `parallel` · `join` | гілки | Розгалужити, дочекатися всіх. |
| `notify` | `notify.channel_uri` · `template` · `channel` | Повідомлення в тред (`nexus://chat/thread/{{run.thread_id}}`) або подія. |
| `integration` · `data_query` · `transform` · `wait` · `subflow` · `skill` | | Підключена система; запит до датасету; мапінг; затримка або зовнішній сигнал; інший Flow; навичка, застосована без власного агента. |

### Мапінги

`input_mapping` будує вхід вузла з запуску: `$.inputs.document`, `$.node.read.output.text`, `$.run.scheduled_for`,
`$.event.payload.…`. Літеральний рядок беруть у лапки всередині рядка: `"query": "'activity since last week'"`.
Шаблони (`{{run_id}}`, `{{inputs.document}}`, `{{node.classify.output.classification}}`) живуть у полях `template`,
`title_template` і `key_template`.

### Ребра

`{ "id": "e-a-b", "source": "a", "target": "b" }`, з `when` на ребрах, що виходять із `condition` або `approval`, і
необов'язковим `label`, який показує редактор. Із кожного вузла, крім `end`, є вихід; у кожен вузол, крім `trigger`, є
вхід.

## Цикли: мета й оцінювач

Єдине правило, яке платформа не дозволить порушити: **рушій, а не модель, вирішує, коли мету досягнуто.** Цикл — це
загальний вузол із метою та оцінювачем, із
[`goal-evaluator-loop`](../../packs/nexus-base/patterns/templates/goal-evaluator-loop.json) Nexi Base:

```json
{
  "id": "iterate", "kind": "loop", "label": "Until goal complete",
  "loop": {
    "entry_node_id": "work",
    "body_node_ids": ["work", "evaluate"],
    "until": { "kind": "goal", "evaluator_node_id": "evaluate" },
    "max_iterations": 6,
    "max_duration_s": 1800,
    "budget": { "max_tokens": 600000 },
    "on_no_progress": "ask_human",
    "no_progress_after": 2,
    "iteration_context": "summarize"
  }
},
{
  "id": "evaluate", "kind": "evaluator", "label": "Goal evaluator", "timeout_s": 60,
  "evaluator": { "kind": "deterministic", "criteria_source": "goal", "metrics_path": "$.node.work.output" }
}
```

- **Мета** (`GoalSpec`: `objective`, `success_criteria[]`, `max_iterations`, `max_runtime_s`, `required_outputs`,
  `budget`, `on_no_progress`, `human_review_required`, `classification_max`) — це дані, які читає рушій. Критерії —
  перевірки над виходом робочого вузла: шлях метрики й поріг, обов'язкове поле, схема — не речення.
- `deterministic`-оцінювач застосовує критерії. Вердикт `model`-оцінювача записується як *ознака* ітерації — рушій
  усе одно застосовує критерії й межі; модель-оцінювач, яка каже «готово», нічого не завершує.
- `max_iterations`, `max_duration_s`, `budget` — жорсткі межі, які застосовує рушій. `on_no_progress` (`ask_human` ·
  `stop`) з `no_progress_after` — те, що стається, коли дві ітерації нічого не змінюють.
- `human_review_required: true` на меті або `goal_completion_requires_human` у blueprint ставить людину між
  «критерії виконано» та «готово».

## Політика

`policy` Flow — стеля для кожного вузла: `allowed_tool_uris` (вузол не може викликати нічого іншого), `run_as`
(`initiator` — від імені людини, яка запустила, під *її* дозволами), `max_run_duration_s`, `max_loop_depth`,
`sandbox_profile_uri` для будь-якого коду, написаного моделлю, `approval_for_external_writes`, `sensitive_outputs`.
`tool_policy.allowlist` blueprint — стеля над цим; шари організації та Проєкту — над тим.

## Патерни

**Патерн** — іменована форма оркестрації над одним шаблоном: *послідовний ланцюг*, *маршрут до спеціаліста*,
*план–виконання*, *паралельні працівники*, *ансамбль-суддя*, *каскад моделей*, *цикл мета–оцінювач*,
*виконати–перевірити–виправити*, *шлюз людської перевірки*. Патерн каже, коли його використовувати (`use_when`), чого він
коштує (`characteristics`), які види вузлів йому потрібні (`requires.node_types` — рівно ті, що в шаблоні) і як його
намалювати (`diagram`). Людина обирає патерн; платформа дає їй шаблон; blueprint може дозволити або заборонити види
вузлів, а отже й патерни.

Постачайте патерн, коли ваш Flow — *форма, яку інші використають повторно*; постачайте простий шаблон, коли це
*робота*.

## Чотири Flow, які варто прочитати

| Flow | Показує |
|---|---|
| [`document-review`](../../packs/nexus-base/flows/document-review.json) | Ручний тригер із типізованими входами · вузли агентів зі строгою `output_schema` · умова на класифікації · погодження з `on_timeout` · ідемпотентний мутуючий інструмент · notify. |
| [`weekly-digest`](../../packs/nexus-base/flows/weekly-digest.json) | Розклад · `$.run.scheduled_for` · літерал у лапках у мапінгу. |
| [`member-onboarding`](../../packs/nexus-base/flows/member-onboarding.json) | Тригер від події · запуск без треду. |
| [`bi-metric-alert`](../../packs/nexus-base/flows/bi-metric-alert.json) | Фільтр події, прив'язаний до параметра шаблону · інструмент, який вирішує, агент, який лише формулює. |
