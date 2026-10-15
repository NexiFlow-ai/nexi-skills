# Nexi Base — the pack every organization starts from

This directory is a **NexusPack**: the skills, agents, Flows, patterns, policies, sandbox profiles and dashboard templates
Nexi installs into a new organization, published as the reference every pack author can read, copy and learn from.
It is the exportable part of the pack Nexi ships — [`CATALOGUE.md`](./CATALOGUE.md) lists what is here and what is
*coming*, and why.

## What is in a pack

| Directory | Kind | What it is |
|---|---|---|
| `manifest.json` | the manifest | Every file with its sha256 digest, what the pack requires (model roles · sandbox runtimes · platform tools), and one Ed25519 signature by the publisher. A pack is loaded whole or not at all. |
| `blueprints/` | `blueprint` | The defaults — agents, skills and Flows by role, the platform tool allow-list, model policy, sandbox profile, approvals, retention. |
| `agents/<name>.json` + `<name>.md` | `agent` + `prompt` | Who works: a role, a purpose, the skills it applies, its capability card (what it is for, what it may see), and its instructions. |
| `skills/<name>/skill.json` + `SKILL.md` | `skill` + `prompt` | What an agent is taught: `input_schema`, `output_schema`, examples, the human review of this version, and the instruction itself. |
| `flows/` | `flow_template` | How work is orchestrated: triggers, agent and tool nodes, conditions, approvals, loops with a goal and an evaluator, notifications. |
| `patterns/` + `patterns/templates/` | `pattern` + `flow_template` | Named orchestration shapes (sequential chain, plan–execute, ensemble judge, …) over a template each. |
| `policies/` | `policy` | Tool groups · connector kinds · model roles · skill sensitivity · KPIs. |
| `sandbox/` | `sandbox_profile` | Where model-written code runs: no network, bounded time and memory, a classification ceiling. |
| `dashboards/` | `dashboard_template` | Slot structures a BI dashboard draft starts from. |

## Three rules this pack keeps

1. **A skill teaches; it owns nothing.** No tools, no model, no knowledge, no credentials, no permissions — those belong to
   the agent, the Blueprint and the deployment.
2. **The engine, never the model, decides when a goal is done.** Every `loop` node has a `GoalSpec` and an evaluator the
   engine runs; iterations, duration and budget are limits the engine enforces.
3. **Nobody is taught an unreviewed skill.** Every skill carries `evaluation.human_review` naming the reviewer and the
   reviewed version. A skill whose current version nobody reviewed is not published — here or in the platform.

## Read it, then build your own

The guide in [`../../guide/`](../../guide/README.md) walks from these files to your own pack: write a skill, an agent and a
Flow; validate, digest and sign them with `nexi-pack`; bring the pack to a Nexi deployment. The signature on this
manifest is the Nexi publisher's (`publishers.yaml` at the repository root carries the public key); yours will be your own.

Licence: Apache-2.0 (see `LICENSE` at the repository root). *Nexi* and *NexiFlow* are trademarks — see `TRADEMARKS.md`.
