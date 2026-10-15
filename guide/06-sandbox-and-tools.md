# 6 · Sandbox and tools

Two places where an agent touches the world outside the conversation: a **tool** (an action with a contract) and the
**sandbox** (where code a model wrote may run). Both are the platform's; a pack names what it needs and sets the
bounds.

## Tools

A tool is a uri with a contract — an operation, an input schema, an output schema, a `mutating` flag, a required
classification ceiling. Three families:

| Family | Examples | Where it comes from |
|---|---|---|
| **Platform tools** | `nexus://tool/project.search` · `project.file_read` · `blob.read_text` · `knowledge.search` · `artifact.create_document` · `artifact.create_table` · `artifact.create_chart` · `artifact.publish` · `dataset.query` · `dataset.describe` · `sandbox.run_python` · `task.create` · `flow.run` · `web.map` · `web.fetch` · `web.extract` · `capability.inventory` · `rights.dryrun` · … | The deployment. [`policies/tool-groups.json`](../packs/nexus-base/policies/tool-groups.json) groups them as a person sees them. |
| **Connected tools** | `nexus://tool/<connection>.<operation>` — a CRM search, a ticket read, a SQL query | A connection an Admin created in NexCore › Connections from a `connector_kind`. A pack says `requires.connections: [{ name, tool_uri, optional }]`; the deployment binds. |
| **Builder tools** | `state.read` · `plan.step` · … | Only the platform's resolver may use them (`tool_policy.builder_only`). Never yours. |

What an agent gets for a turn or a node is the intersection of: the blueprint's `tool_policy.allowlist` → the Flow's
`policy.allowed_tool_uris` (or, in the conversation, the Project's tool policy) → the agent's own `tools` bindings →
**the person's permissions and connections**, because every call runs as the person (`run_as: initiator`). A tool a
pack names but the deployment does not serve is *unavailable*, and says so — `tool-groups.json` marks `available:
false` for exactly that reason. An agent that lacks a tool does not pretend; it answers with a capability need (chapter 3).

### Tool node discipline

- `mutating: true` on anything that creates, changes, sends or deletes. It is what approvals key on.
- `idempotency.key_template` on every mutating node — `"document-review:{{run_id}}"` — with a `dedupe_window_s`. A
  retried node must not create a second document.
- `retry` with a bounded `max_attempts` and a backoff; `timeout_s` always.
- `policy.purpose` says *why* in one word the policy decision point can reason about (`read`, `save`, `classification`,
  `weekly_brief`).
- Never a credential in a mapping, a template or an instruction. There is nowhere in a pack a secret belongs; the
  manifest says so (`contains_secrets: false`) and the guard that publishes packs looks for them.

## The sandbox

Model-written code runs **only** in the sandbox, through `sandbox.run_python`, under a **profile**. No host shell, no
credentials, no direct network. A notebook is an artifact format, not an execution boundary.

Reference: [`sandbox/public-dev.json`](../packs/nexus-base/sandbox/public-dev.json).

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

| Block | What it bounds |
|---|---|
| `network.policy` | `none` in every profile Nexi ships. A profile with egress is a deployment decision, never a pack's default. |
| `packages` | `allowlist_only` with the packages baked into the image. Code may import these and nothing else. |
| `limits` | CPU, memory, wall time, output size, artifact count, concurrency — per run. |
| `isolation` | No host filesystem, no credentials, datasets read-only, one writable artifact directory, ephemeral, a seccomp-confined container. |
| `classification_max` | The highest data the profile may receive. Nexi Base's `confidential-analytics` profile exists for the next level up, with tighter limits. |
| `audit` | Code and stdout are kept for the audit window. |

A Flow names its profile in `policy.sandbox_profile_uri`; a node may name a tighter one in `sandbox_profile_uri`; the
blueprint names the default. The same rule as everywhere: **a child may tighten, never loosen.**

### When a pack ships a profile

When your Flows run analyses that need a package the base image lacks, or a different ceiling. Ship the profile with
an honest `classification_max` and the smallest `limits` that do the job, and know that a deployment may not have the
image you name — `image.ref` is a request the operator fulfils or declines.

## What never ships in a pack

- Executable code of any kind — no scripts, no tool implementations, no notebooks as runtimes.
- A URL, a hostname, a connection string, a key, a token, a certificate — even a placeholder that looks like one.
- A model id. A role, with capabilities and a quality floor, is the whole vocabulary.
- A permission grant. A pack *asks* (tools, connections, roles); the deployment and the person *grant*.
