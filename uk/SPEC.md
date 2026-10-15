# Формат пака Nexi

**Пак** (`NexusPack`, `api_version: nexus/v1`) — це каталог. Його `manifest.json` перелічує кожен файл, який пак
постачає, із sha256-дайджестом файлу, оголошує, чого пак вимагає від розгортання, і несе один підпис Ed25519 видавця.
Розгортання завантажує пак цілком або не завантажує зовсім: один відсутній файл, один дайджест, що не збігається, один
невідомий видавець — і з пака не читається нічого.

Схеми: [`toolkit/src/nexi_pack/schemas/`](../toolkit/src/nexi_pack/schemas/) — `nexus-pack-manifest.schema.json` це
маніфест; решта — ресурси. `nexi-pack validate` застосовує їх.

## Маніфест

```json
{
  "api_version": "nexus/v1",
  "kind": "NexusPack",
  "metadata": {
    "name": "my-pack",                    // ^[a-z][a-z0-9-]{1,62}$ — uri пака: nexus://core/pack/<name>
    "version": "0.1.0",                   // semver
    "display_name": "My Pack",
    "publisher": "Olena Co.",
    "description": "…",
    "license": "Apache-2.0",
    "homepage": "https://…",
    "created_at": "2026-10-15T00:00:00Z"
  },
  "layer": "domain",                      // base | domain | organization | project — де стоїть blueprint
  "depends_on": [{ "name": "nexus-base", "version_range": ">=1.0.0 <2.0.0" }],
  "compatibility": {
    "nexus_min_version": "0.4.0",
    "spec_versions": { "workflow-spec": "1.1", "agent-definition": "1.0", "skill-manifest": "1.0", "blueprint": "1.0" },
    "deployment_targets": ["on_prem", "azure", "disconnected"]
  },
  "resources": [
    { "kind": "blueprint", "path": "blueprints/my-pack.json", "uri": "nexus://core/blueprint/my-pack", "name": "My Pack", "version": "0.1.0", "digest": "sha256:…" },
    { "kind": "skill", "path": "skills/brief/skill.json", "uri": "nexus://skill/skl_my_brief", "name": "Brief", "version": "0.1.0", "digest": "sha256:…" },
    { "kind": "prompt", "path": "skills/brief/SKILL.md", "digest": "sha256:…" },
    { "kind": "agent", "path": "agents/assistant.json", "uri": "nexus://agent/agt_my_assistant", "name": "Assistant", "version": "1", "digest": "sha256:…" },
    { "kind": "prompt", "path": "agents/assistant.md", "digest": "sha256:…" },
    { "kind": "flow_template", "path": "flows/weekly-brief.json", "uri": "nexus://workflow/template/flw_tpl_my_weekly_brief", "name": "Weekly brief", "version": "1", "digest": "sha256:…" }
  ],
  "requires": {
    "models": [{ "role": "chat" }, { "role": "extractor", "capabilities": ["structured_output"] }],
    "platform_tools": ["nexus://tool/project.search", "nexus://tool/artifact.create_document"],
    "sandbox_runtimes": ["python"],
    "connections": [{ "name": "crm", "tool_uri": "nexus://tool/crm.search", "description": "…", "optional": true }]
  },
  "contains_secrets": false,              // константа — пак ніколи не містить облікових даних
  "readme_path": "README.md",
  "signature": { "alg": "ed25519", "key_id": "olena-2026", "value": "<base64url>" }
}
```

(У JSON немає коментарів; вони тут лише для читання.)

## Види ресурсів

| `kind` | Файл | Схема | Примітки |
|---|---|---|---|
| `blueprint` | `blueprints/<name>.json` | `blueprint.schema.json` | Рівно один на пак. `source_pack_uri` — uri самого пака. |
| `skill` | `skills/<name>/skill.json` | `skill-manifest.schema.json` | `entry: SKILL.md`; інструкція — `prompt` поруч. |
| `agent` | `agents/<name>.json` | `agent-definition.schema.json` | Інструкція — `agents/<name>.md` (`prompt`) або вбудоване `instructions`. |
| `prompt` | будь-який `.md` | — | Перевіряється за дайджестом, сам по собі не інтерпретується. |
| `flow_template` | `flows/<name>.json`, `patterns/templates/<name>.json` | `workflow-spec.schema.json` | `project_id: null`, `template.is_template: true`. |
| `pattern` | `patterns/<name>.json` | `pattern-definition.schema.json` | Абстракція авторства над одним постаченим шаблоном; `requires.node_types` дорівнює видам вузлів шаблону. |
| `sandbox_profile` | `sandbox/<name>.json` | `sandbox-profile.schema.json` | Де виконується код, написаний моделлю. |
| `policy` | `policies/<name>.json` | — | JSON-документ із `kind`: групи інструментів · види конекторів · ролі моделей · чутливість навичок · KPI. |
| `dashboard_template` | `dashboards/<name>.json` | `bi-dashboard-template.schema.json` | Структури слотів для дашбордів BI. |
| `ontology` · `schema` · `evaluation` · `tool_*` · `ui_config` · `migration` | — | — | Перевіряються, переносяться, інтерпретуються застосунком, якому належать. |
| `module` · `tasks.project_template` · `sales.field_preset` | `module/` · `projects/` · `fields/` | — | Паки модулів набору; див. документацію розгортання. |

Кожен `path` відносний, усередині пака, без `..`. Кожен `uri` у маніфесті дорівнює `uri` всередині файлу.

## Дайджести

`digest` — це `sha256:<64 hex>` байтів файлу саме таким, яким він постачається. `nexi-pack digest --write`
перераховує їх; будь-яка зміна файлу робить підпис недійсним, тому `digest --write` його прибирає.

## Підпис

Видавець підписує **канонічний payload**: маніфест без `signature`, серіалізований як JSON із відсортованими ключами,
без пробілів, UTF-8, не-ASCII символи як є — у Python
`json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`. Не пишіть у маніфест
членів `null`: розгортання канонізує з розібраної моделі, яка їх відкидає, і обидві форми мають збігатися байт у байт.

- `alg` — `ed25519`; `value` — 64-байтовий підпис як base64url без доповнення.
- `key_id` називає запис у **файлі видавців** розгортання (`key_id` · `public_key` як base64url 32 сирих байтів ·
  `name`). Оператор розгортання вирішує, кому довіряти, редагуючи цей файл; ніщо інше довіри не дає.
- Приватний ключ — 32-байтовий seed. `nexi-pack sign --generate-key` записує його в base64 із режимом 0600. Він ніколи
  не потрапляє в репозиторій, пак, промпт чи лог.

## Що розгортання робить із паком

1. **Імпорт** — Owner або Admin завантажує архів. Розгортання читає маніфест, перевіряє кожен дайджест, звіряє підпис
   із файлом видавців, розбирає кожен ресурс за його схемою і кладе пак у бібліотеку. Будь-яка невдача називає причину
   (`PACK_DIGEST_MISMATCH`, `PACK_PUBLISHER_UNKNOWN`, `PACK_SIGNATURE_INVALID`, `PACK_RESOURCE_INVALID`, …), і з пака
   не зберігається нічого.
2. **Встановлення** — в одну організацію: застосовується шар blueprint (defaults, allow-list інструментів, політика
   моделей, погодження), агенти й навички стають доступними Проєктам цієї організації, шаблони Flow можна
   інстанціювати, маршрутизовані агенти долучаються до маршрутизації можливостей у розмові.
3. **Рецензія** — навичка, чию поточну версію ніхто не рецензував, встановлюється, але **нікого не навчає**, доки людина
   в цій організації не зафіксує рецензію. `evaluation.human_review` у паку — рецензія видавця; рецензія організації
   — її власна.

`nexi-pack install --dry-run` друкує, що застосував би крок 2.
