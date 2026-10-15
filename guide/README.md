# Building for Nexi — the guide

How agents, skills and Flows are made for Nexi, how the platform's own packs are built, and how yours gets from a
directory on your machine to an organization's Projects. Everything here is proven on the reference pack next to this
guide: every file it names is in [`../packs/nexus-base/`](../packs/nexus-base/README.md).

## Part I — How Nexi thinks

| | Chapter | What you take from it |
|---|---|---|
| 1 | [What a pack is](./01-what-a-pack-is.md) | The nine kinds of things a pack ships and the one sentence that holds them together: *Skill teaches. Agent works. Tool acts. Flow orchestrates. Goal directs. Evaluator judges. Sandbox executes code. Synapse connects. Core governs.* |
| 2 | [Skills](./02-skills.md) | An instruction plus an evaluation package — schemas, examples, a human review — that owns nothing. |
| 3 | [Agents](./03-agents.md) | Who works: role, purpose, the skills it applies, the capability card that lets the conversation route to it, what it may see. |
| 4 | [Flows](./04-flows.md) | Triggers, nodes, edges, policy; loops with a goal the **engine** judges; patterns. |
| 5 | [The blueprint layer and policies](./05-blueprint-and-policies.md) | Defaults, the tool allow-list, model roles instead of vendors, approvals, retention; how layers stack. |
| 6 | [Sandbox and tools](./06-sandbox-and-tools.md) | Where model-written code runs; what a tool is and what an agent may never do. |

## Part II — Building your own

| | Chapter | What you take from it |
|---|---|---|
| 7 | [Your first pack](./07-your-first-pack.md) | `nexi-pack new` to a signed, valid pack, file by file. |
| 8 | [Review, sign, bring it to a deployment](./08-review-sign-register.md) | The review a skill needs, the signature, the publishers file, import and install, when the conversation starts routing to your agent, how to update. |
| 9 | [Best practices — the rules the platform's packs keep](./09-best-practices.md) | Forty-odd rules, each with the reason and the file that shows it. |
| 10 | [Testing](./10-testing.md) | Examples as tests, the dry run, scenario thinking, what to measure before you ship a new version. |

## Conventions

- `nexus://…` is a resource uri; `nexi-pack` is the toolkit in [`../toolkit/`](../toolkit/README.md).
- *Project* with a capital P is a Nexi Project — the unit of membership, files and threads an agent works inside.
- A **deployment** is one installation of Nexi; an **organization** is a tenant of it; an **operator** runs the
  deployment, an **Owner** or **Admin** governs an organization.
