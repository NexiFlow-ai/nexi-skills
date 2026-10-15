# 1 · What a pack is

Nexi is a governed runtime for agentic systems. The rule that shapes everything you will build: **no professional
capability needs its own code path if it can be expressed as agents, skills, tools, Flows, a sandbox, policies and
artifacts.** Such capabilities ship as *packs* — directories of JSON and Markdown a deployment installs — never as
changes to the platform.

A pack is what you build. This chapter is the map; the chapters after it are the territory.

## The composition sentence

> *Skill teaches. Agent works. Tool acts. Flow orchestrates. Goal directs. Evaluator judges. Sandbox executes code.
> Synapse connects. Core governs.*

Every word is a different kind of thing, and the platform keeps them apart on purpose:

| Word | What it is | What it is **not** |
|---|---|---|
| **Skill** | A portable instruction with an `input_schema`, an `output_schema`, examples and a human review. | A tool, a model choice, a credential, a knowledge base, a permission — a skill owns none of these. |
| **Agent** | Someone who works: a purpose, a model role, the skills it applies, what it may see, how the conversation routes to it. | A Flow, a loop, a script. |
| **Tool** | An action with a contract — search a Project, read a file, create a document, call a connected system. Platform tools come with the deployment; connected systems come through Synapse. | Something a pack adds: a pack *names* tools it needs; it never ships executable code for one. |
| **Flow** | Orchestration: a trigger, nodes (agent · tool · condition · approval · loop · notify · …), edges, a policy. | Business logic in the engine. The engine runs the graph; it knows nothing of your domain. |
| **Goal** | What a loop is for: an objective, success criteria, limits on iterations, time and budget. | A hope. The engine, never the model, decides whether a goal is met. |
| **Evaluator** | The judge of a loop iteration — deterministic over the criteria, or an evaluator model whose opinion is a *feature*, never the verdict. | A model saying "done". |
| **Sandbox** | Where model-written code runs: no host shell, no credentials, no direct network, a profile that bounds it. | A notebook as a runtime; a shell. |
| **Synapse** | Connections to external systems, owned by the deployment, bound by an Admin. | Something a pack configures with a URL and a key. |
| **Core** | Governance: who may do what, the policy bundle, the import and install of packs, the trust in publishers. | Something the UI decides. Authorization is server-side, always. |

## What a pack ships

Open [`../packs/nexus-base/`](../packs/nexus-base/README.md) and you see the whole vocabulary:

```
manifest.json                 every file + digest, requires, one signature
blueprints/nexus-base.json    the layer: defaults · tool allow-list · model policy · approvals · retention
agents/general.json + .md     an agent and its instructions
skills/summarize/skill.json   a skill: schemas, examples, review
skills/summarize/SKILL.md       … and its instruction
flows/weekly-digest.json      a Flow template
patterns/sequential-chain.json         a named orchestration shape …
patterns/templates/sequential-chain.json … over this template
policies/tool-groups.json     tool groups · connector kinds · model roles · skill sensitivity · KPIs
sandbox/public-dev.json       a sandbox profile
dashboards/executive_overview.json     a BI dashboard template
CATALOGUE.md                  generated: what is here, what is coming
```

Three things are worth noticing before you read a single file:

1. **Everything is data.** There is no code in a pack. An agent is a JSON document and a Markdown instruction; a Flow is
   a JSON graph. What *runs* is the platform; what you ship is what it runs.
2. **Everything is reviewed.** A skill's current version carries the name of the human who read it. An agent's
   `governance.state` is a review. A pattern names who reviewed it. Nothing teaches, routes or runs on nobody's word.
3. **Everything is signed.** The manifest's digests pin every byte; the signature pins the manifest to a publisher the
   deployment chose to trust. A pack is whole or nothing.

## Layers

A deployment stacks blueprint layers: **base** (Nexi Base — what every organization starts from) → **domain** (a
profession, an industry: yours) → **organization** (what one tenant tightens) → **project** (what one Project tightens
further). A lower layer can tighten what a higher one allows; it can never loosen it. Your pack is almost always a
*domain* layer that `depends_on` Nexi Base: it adds agents and Flows for a field of work and inherits the base's tool
groups, model roles and policies.

## How a person meets your work

Nobody "runs an agent". A person writes in the conversation, or an event happens, or a schedule fires:

- In the conversation, **Auto** — the capability routing — reads the ask and the capability cards of the routable
  agents the organization installed, and routes to one, or to a Flow, or answers itself. Your agent is a candidate the
  moment it is installed and approved; the card you write (chapter 3) is what it is judged by.
- A person can address a skill directly by its shortcut (`/summary`), or an agent by name.
- A Flow runs when its trigger fires: a schedule, an event, a person starting it from a thread, another Flow.
- What an agent produces is an **artifact** (a document, a table, a chart), a message in the thread, a task, or a
  proposal that waits for a human. What it changed is recorded — every app emits typed audit events.

The rest of the guide follows this order: the skill (2), the agent that applies it (3), the Flow that schedules it
(4), the layer that governs it (5), the sandbox and the tools it may use (6) — then yours (7–10).
