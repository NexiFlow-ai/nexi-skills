# 4 · Flows

A Flow is orchestration: a trigger, a graph of nodes, the edges between them, and a policy. The engine runs the graph;
it retries what you told it to retry, deduplicates what you keyed, waits for the human you named, enforces the limits
you set — and knows nothing about your domain. Everything domain-specific is in the agents and tools the nodes call.

A pack ships Flows as **templates**: `project_id` is `null`, `template.is_template` is `true`, and a person instantiates
one into a Project (with the template's `parameters`) — or the blueprint names it under a role so the platform starts it.

Reference: [`flows/document-review.json`](../packs/nexus-base/flows/document-review.json) — read, classify, review,
approve when confidential, save, notify.

## The shape

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

## Triggers

| `trigger.kind` | Fires when | Example |
|---|---|---|
| `manual` | A person starts it from a thread or the Flow's page, with `inputs`. | Document review |
| `schedule` | `schedule_cron` in `schedule_timezone`. | Weekly digest: `0 8 * * 1`, `Europe/Kyiv` |
| `event` | A platform event on `event_subject`, optionally narrowed by `event_filter` (an expression over `$.event`). | Member onboarding on `nexus.core.organization.membership.granted.v1`; a BI alert on `nexus.bi.dataset_version.published.v1` filtered to one dataset |
| `webhook` · `subflow` | An external call through a connection; another Flow. | |

An event-triggered run has no thread: its result is the run's output, visible on the run page — a `notify` node into
`{{run.thread_id}}` does nothing there. Nexi Base's member onboarding says so in its own description.

## Nodes

Every node has `id`, `kind`, `label`, and may have `timeout_s`, `retry`, `idempotency`, `policy` (`pep_action`,
`purpose` — the words the policy decision point sees), `on_failure`, `compensation_node_id`, `input_mapping`.

| `kind` | Payload | What it does |
|---|---|---|
| `trigger` · `end` | — | Every Flow starts with one trigger and ends in `end`. |
| `agent` | `agent.agent_uri` · `skill_uris` · `context_scope` (`project` · `thread` · `none`) · `output_schema` | Invokes an agent for one step. **Always give an `output_schema`**: the engine validates the reply and the next node reads named fields, not prose. |
| `tool` | `tool.tool_uri` · `operation` · `mutating` | Calls a platform or connected tool. `mutating: true` is what approvals and `approval_for_external_writes` key on; a mutating tool node carries `idempotency`. |
| `condition` | `condition.language: nexus-expr-v1` · `source` | A boolean over the run state: `$.node.classify.output.classification != 'public'`. Edges leaving it carry `when: "true"` / `"false"`. |
| `approval` | `approval.approver` (`{ "relation": "owner" }` …) · `title_template` · `on_timeout` | Waits for a human. Edges carry `when: "approved"` / `"rejected"`. The approval is a task the person sees in their inbox. |
| `human_task` | a task definition | Work for a person inside the run. |
| `loop` | `loop.entry_node_id` · `body_node_ids` · `until` · `max_iterations` · `max_duration_s` · `budget` · `on_no_progress` · `no_progress_after` | Below. |
| `evaluator` | `evaluator.kind` (`deterministic` · `model`) · `criteria_source` · `metrics_path` | The judge of a loop. |
| `parallel` · `join` | branches | Fan out, wait for all. |
| `notify` | `notify.channel_uri` · `template` · `channel` | A message into the thread (`nexus://chat/thread/{{run.thread_id}}`) or an event. |
| `integration` · `data_query` · `transform` · `wait` · `subflow` · `skill` | | A connected system; a dataset query; a mapping; a delay or an external signal; another Flow; a skill applied without an agent of its own. |

### Mappings

`input_mapping` builds a node's input from the run: `$.inputs.document`, `$.node.read.output.text`,
`$.run.scheduled_for`, `$.event.payload.…`. A literal string is quoted inside the string: `"query": "'activity since
last week'"`. Templates (`{{run_id}}`, `{{inputs.document}}`, `{{node.classify.output.classification}}`) live in
`template`, `title_template` and `key_template` fields.

### Edges

`{ "id": "e-a-b", "source": "a", "target": "b" }`, with `when` on edges leaving a `condition` or an `approval`, and an
optional `label` the editor shows. Every node except `end` has a way out; every node except `trigger` has a way in.

## Loops: the goal and the evaluator

The one rule the platform will not let you break: **the engine, never the model, decides when a goal is done.** A loop
is a generic node with a goal and an evaluator, from Nexi Base's
[`goal-evaluator-loop`](../packs/nexus-base/patterns/templates/goal-evaluator-loop.json):

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

- The **goal** (`GoalSpec`: `objective`, `success_criteria[]`, `max_iterations`, `max_runtime_s`, `required_outputs`,
  `budget`, `on_no_progress`, `human_review_required`, `classification_max`) is data the engine reads. Criteria are
  checks over the work node's output — a metric path and a threshold, a required field, a schema — not sentences.
- A `deterministic` evaluator applies the criteria. A `model` evaluator's verdict is recorded as a *feature* of the
  iteration — the engine still applies the criteria and the limits; an evaluator model saying "done" ends nothing.
- `max_iterations`, `max_duration_s`, `budget` are hard limits the engine enforces. `on_no_progress` (`ask_human` ·
  `stop`) with `no_progress_after` is what happens when two iterations change nothing.
- `human_review_required: true` on the goal, or the blueprint's `goal_completion_requires_human`, puts a person
  between "criteria met" and "done".

## Policy

The Flow's `policy` is the ceiling for every node: `allowed_tool_uris` (a node may call nothing else), `run_as`
(`initiator` — as the person who started it, under *their* permissions), `max_run_duration_s`, `max_loop_depth`,
`sandbox_profile_uri` for any model-written code, `approval_for_external_writes`, `sensitive_outputs`. The blueprint's
`tool_policy.allowlist` is the ceiling over that; the organization's and the Project's layers over that.

## Patterns

A **pattern** is a named orchestration shape over one template: *sequential chain*, *route to specialist*,
*plan–execute*, *parallel workers*, *ensemble judge*, *model cascade*, *goal–evaluator loop*, *execute–test–repair*,
*human review gate*. The pattern says when to use it (`use_when`), what it costs (`characteristics`), which node kinds
it needs (`requires.node_types` — exactly the template's) and how to draw it (`diagram`). A person picks a pattern; the
platform gives them the template; the blueprint can allow or forbid node kinds and so patterns.

Ship a pattern when your Flow is a *shape others will reuse*; ship a plain template when it is a *job*.

## Four Flows to read

| Flow | Shows |
|---|---|
| [`document-review`](../packs/nexus-base/flows/document-review.json) | Manual trigger with typed inputs · agent nodes with strict `output_schema` · a condition on a classification · an approval with `on_timeout` · an idempotent mutating tool · notify. |
| [`weekly-digest`](../packs/nexus-base/flows/weekly-digest.json) | Schedule · `$.run.scheduled_for` · a quoted literal in a mapping. |
| [`member-onboarding`](../packs/nexus-base/flows/member-onboarding.json) | Event trigger · a run with no thread. |
| [`bi-metric-alert`](../packs/nexus-base/flows/bi-metric-alert.json) | Event filter bound to a template parameter · a tool that decides, an agent that only phrases. |
