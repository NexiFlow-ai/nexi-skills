# 5 · The blueprint layer and policies

The blueprint is the layer a pack installs: what an organization gets by default, what its agents may use, which
models may see what, when a human must approve, how long things are kept. Every pack ships exactly one. The policies
next to it are plain documents the blueprint and the applications read.

Reference: [`blueprints/nexus-base.json`](../packs/nexus-base/blueprints/nexus-base.json) and
[`policies/`](../packs/nexus-base/CATALOGUE.md#blueprint-policies-sandbox-profiles-dashboard-templates).

## The blueprint

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

| Block | What it decides |
|---|---|
| `layer` · `parent_uri` | `base` · `domain` · `organization` · `project`. A domain layer names the base as `parent_uri` and **tightens** it. Nothing a child says can loosen a parent. |
| `defaults.agents` · `skills` | What is active in a new organization. Everything named must be shipped by this pack or one it depends on — the toolkit warns otherwise. |
| `defaults.flows` | Flow templates by **role** (`document_review`, `weekly_digest`, `member_onboarding`, `admin_governance`, …). The platform starts a Flow by role: your `admin_governance` replaces the base's for organizations on your layer. |
| `defaults.general_agent_uri` | Who answers when nothing routes. Leave it to the base unless your layer *is* a different kind of organization. |
| `defaults.suggested_capabilities` | The sentences a new person sees as suggestions — in the person's words, verbs first. |
| `defaults.projects` | Predefined Projects a new organization gets, with the Flows to start in them. |
| `tool_policy.allowlist` | **The ceiling for every agent and Flow in the organization.** A tool not here does not exist for them. `side_effect_requires_approval` puts a human before any mutating tool. `builder_only` names tools only the resolver may use. |
| `model_policy` | Which endpoint kinds (`local` · `contour` · `cloud`) and up to which classification data may go to the cloud; a tier ceiling; whether a person may pick a model by name (`allow_explicit_model: false` — roles, not vendors); a quality floor per role. |
| `sandbox_profile_uri` | Where model-written code runs by default. |
| `approvals` | `external_write_threshold` — from which classification an external write needs approval; `goal_completion_requires_human`; who approves capability and package requests; `allow_self_approval: false`. |
| `retention` | How long artifacts, runs and sandbox output live. |
| `tuning` | Knobs of platform behaviours the layer is allowed to tune (the conversation's routing thresholds, research budgets). Rarely yours. |
| `guardrails` · `evaluations` · `modules` · `analysis` | Guardrail sets, evaluation suites, suite modules a module pack enables, the analysis settings. |

### Layers tighten

Suppose Nexi Base allows `cloud` endpoints up to `confidential`. Your domain layer for a legal practice may say
`allowed_endpoint_kinds: ["local", "contour"]` — every organization on your layer then keeps everything in-house. It may
*not* say `max_classification_for_cloud: secret`; a deployment refuses a child that loosens its parent. The same for
the tool allow-list (a subset), approvals (a lower threshold), classification ceilings (lower), retention (shorter).

## Policies

A `policy` resource is a JSON document with a `kind`. The base pack ships five; yours may ship its own of the same
kinds, or new kinds your applications read.

| `kind` | What it holds | Who reads it |
|---|---|---|
| `tool_groups` | Platform tools grouped as a person sees them — *Documents · read & parse*, *Artifacts*, *Data*, … — with `enabled` (shipped on in this layer) and `available` (a platform tool really executes it — *honest, not hidden*). | NexCore's tools page; the capability routing's explanation. |
| `connector_kinds` | The **kinds** of connections an organization may create — PostgreSQL, REST/OpenAPI, MCP, files, webhooks — with protocol and credential type. *No instances, no endpoints, no credentials.* | NexCore › Connections. |
| `model_roles` | The roles the pack routes to, which agents use each, the highest classification the role's model may see, the capabilities required. *No vendor ids.* | The model gateway's binding page. |
| `skill_sensitivity` | `max_input_classification` per skill; `recommended` skills. | The conversation, before applying a skill. |
| `kpis` | What the organization measures about its own use. | NexBI's platform dashboards. |

The pattern is the same every time: **the pack names a kind, the deployment binds an instance.** A pack never knows a
hostname, a model id, an API key or a tenant.

## What your layer should contain

For a domain pack, usually:

- `defaults.agents` and `skills`: your agents and skills, plus the base's you rely on (the base's General stays General).
- `defaults.flows`: your Flows by role; override a base role only when yours is the better default for your field.
- `tool_policy.allowlist`: **a subset** of the base's — exactly what your agents and Flows use. The toolkit prints the
  list in `install --dry-run`; compare it with `requires.platform_tools` in the manifest; they should agree.
- `model_policy`: tighten if your field demands it; otherwise inherit by repeating the base's.
- `approvals`: tighten if your Flows write outside Nexi.
- A `skill_sensitivity` policy for your skills; a `model_roles` policy if you add roles; a `connector_kinds` policy if
  your Flows need a kind of connection (`requires.connections` in the manifest names the tool uri; the kind policy names
  the protocol).
