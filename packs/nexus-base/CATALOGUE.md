# Catalogue — Nexi Base 1.34.1

Generated from the pack at export time. A skill appears here only when a human reviewed its current version; an agent only
when its governance review is approved and every skill it applies is here; a Flow only when every agent and skill it names
is here. What is held back is listed by name under *Coming* — the name, never the content.

## Skills (18)

| Skill | Version | Shortcut | What it does |
|---|---|---|---|
| [Assess governance risk](skills/assess-governance-risk/SKILL.md) | 1.0.0 | — | Reads one governance event (a join, an invitation, a suspension, a tool-policy change, a model or credential registration, a pack install) and proposes the ris… |
| [Answer from sources](skills/answer-from-sources/SKILL.md) | 1.0.0 | `/ask` | Grounded Q&A over the given sources only — every statement cited, coverage and gaps declared, conflicts reported instead of resolved. |
| [Classify sensitivity](skills/classify-sensitivity/SKILL.md) | 1.0.1 | `/classify` | Proposes the Nexi data classification (public · confidential · dsk · secret · top_secret) of a text with reasons, signals and suggested redactions. |
| [Compare documents](skills/compare-documents/SKILL.md) | 1.0.0 | `/compare` | Meaningful differences between two documents or versions — kind, quotes, locations, materiality — plus the key terms that stayed the same. |
| [Create Flow](skills/create-flow/SKILL.md) | 1.0.0 | `/flow` | Turn a natural-language automation request into a WorkflowSpec draft you can review in Flow Studio. |
| [Draft and rewrite](skills/draft-and-rewrite/SKILL.md) | 1.0.0 | `/draft` | Writes a text from a brief or rewrites a given one under tone, length, audience and format controls; keeps every fact, marks placeholders. |
| [Extract structured data](skills/extract-structured-data/SKILL.md) | 1.0.0 | `/extract` | Records out of documents into a target JSON Schema, with a quote and location for every field and an explicit list of what was missing. |
| [Meeting notes → actions](skills/meeting-notes-to-actions/SKILL.md) | 1.0.0 | `/actions` | Turns raw notes or a transcript into decisions, owned actions with due dates as stated, open points and the follow-up. |
| [Pin to context](skills/pin-context/SKILL.md) | 1.0.0 | `/pin` | Pin a source, artifact or chat into the Project context. |
| [Recommend pattern](skills/recommend-pattern/SKILL.md) | 1.0.0 | — | Ranks the platform's candidate agentic patterns for a described Flow and says why in the closed use_when vocabulary — reorders or drops candidates, never adds… |
| [Summarize](skills/summarize/SKILL.md) | 1.0.0 | `/summary` | Faithful summary of a text or the pinned sources: summary, key points, action items, open questions — with length and audience controls. |
| [Translate](skills/translate/SKILL.md) | 1.0.0 | `/translate` | Faithful translation into a target language preserving structure and register, with a glossary of domain terms and notes on ambiguities. |
| [Dataset profile](skills/dataset-profile/SKILL.md) | 1.0.2 | — | Ingest a tabular file with pandas and profile every field — type, missing share, distinct count, sample values — as a table, metrics and a Parquet copy; never… |
| [Analysis plan](skills/eda-plan/SKILL.md) | 1.1.1 | — | From a dataset profile and a question, plan the stages this dataset's values support — a technique and a why per stage — the indices worth computing and the me… |
| [Chart recommendation](skills/chart-recommendation/SKILL.md) | 1.0.0 | — | Choose the ChartSpec kind and series for a finding — the nearest native kind when the asked one does not exist — and say so honestly. |
| [Analysis report](skills/analysis-report/SKILL.md) | 1.1.1 | — | Write the report of an analysis run from its plan, metrics and artifacts — it leads with what stands out, every claim cites an artifact uri; 'possible' and 'no… |
| [Web source curation](skills/web-source-curation/SKILL.md) | 1.2.0 | — | From web.map's candidate list (the delta — new and maybe-changed pages, noise dropped, ≤ 80) and the person's goal, choose the pages worth fetching this run, m… |
| [Mail triage](skills/mail-triage/SKILL.md) | 1.0.0 | — | From a window of the person's mail (read through the Gmail read-only tools), name what needs their attention — by whom, about what, by when — and draft replies… |

## Agents (7)

| Agent | Version | Role | Routable | Skills | Purpose |
|---|---|---|---|---|---|
| [General](agents/general.json) | 4 | reasoner | yes | 11 | Everyday knowledge work in the Project |
| [Analyst](agents/analyst.json) | 2 | extractor | yes | 3 | Extraction, classification and comparison with provenance |
| [Writer](agents/writer.json) | 1 | chat | yes | 4 | Drafting, rewriting, translation and summaries |
| [Reviewer](agents/reviewer.json) | 1 | reasoner | yes | 2 | Grounded answers and comparisons — citations mandatory |
| [Governance](agents/governance.json) | 2 | classifier | yes | 3 | Assesses governance events for the administrators' flow and proposes risks; never decides |
| [Analysis planner](agents/ds-planner.json) | 8 | planner | no — a step agent | 2 | Turns a dataset profile and a question into stages, candidate indices and criteria |
| [Web source curator](agents/web-source-curator.json) | 1 | classifier | yes | 1 | Decides which pages of a web source are knowledge worth keeping — never fetches, never signs in |

## Flows (19)

| Flow | Version | Trigger | Nodes | Agents | What it does |
|---|---|---|---|---|---|
| [Admin governance](flows/admin-governance.json) | 2 | event | 6 | agt_governance | every governance event of the organization (a person joined, an invitation or a join request was created, a member was suspended or deactivated, the tool polic… |
| [Data extraction](flows/data-extraction.json) | 1 | manual | 8 | agt_analyst | Sources → extract records into a target schema with provenance → validate against the schema → a table artifact; anything the schema could not be filled from i… |
| [Document review](flows/document-review.json) | 1 | manual | 9 | agt_analyst, agt_reviewer | Upload → classify sensitivity → review (summary, key points, open questions) → the Project owner approves when the document is confidential or above → the revi… |
| [Member onboarding](flows/member-onboarding.json) | 2 | event | 4 | agt_writer | When a person joins (invitation accepted), the Writer agent posts a welcome in the General project's thread with what the organization's projects are and the t… |
| [Weekly digest](flows/weekly-digest.json) | 1 | schedule | 6 | agt_writer | Every Monday 08:00: search the Project for the week's activity, summarize it for an executive reader, save the digest as a document and post it to the thread.… |
| [Mail triage](flows/mail-triage.json) | 1 | schedule | 7 | agt_general | Every Monday 08:00: read the past week's mail through the person's Gmail connection (read-only), name what needs their attention, draft replies as a document a… |
| [Sequential chain](patterns/templates/sequential-chain.json) | 1 | manual | 5 | agt_general, agt_writer | Three steps in a fixed order; each step works on the previous step's result. |
| [Route to specialist](patterns/templates/route-to-specialist.json) | 1 | manual | 8 | agt_governance, agt_analyst, agt_writer, agt_general | A classifier decides the category; the matching specialist handles the request. Never a keyword match (FR-PAT-017). |
| [Plan & execute](patterns/templates/plan-execute.json) | 1 | manual | 8 | agt_general, agt_reviewer | A planner writes a bounded, structured plan; an executor works through it; a reviewer checks the result. |
| [Parallel workers](patterns/templates/parallel-workers.json) | 1 | manual | 6 | agt_general, agt_writer | Independent workers run at the same time; a join waits for all; one step combines the results. |
| [Ensemble & judge](patterns/templates/ensemble-judge.json) | 1 | manual | 10 | agt_general, agt_analyst, agt_writer, agt_reviewer | Several candidates solve the same task; a judge picks or merges the best answer. Economical models by default. |
| [Model cascade](patterns/templates/model-cascade.json) | 1 | manual | 7 | agt_general | Try the smallest qualified model first; escalate to a stronger one only when the check says the result is not good enough. |
| [Goal loop](patterns/templates/goal-evaluator-loop.json) | 1 | manual | 6 | agt_general | Work, evaluate, repeat until the goal's criteria are met — the engine, never the model, decides completion. |
| [Execute, test, repair](patterns/templates/execute-test-repair.json) | 1 | manual | 7 | agt_general | Generate, run it in the sandbox, validate deterministically; on failure diagnose and repair — never the same model approving itself (FR-PAT-008). |
| [Human review gate](patterns/templates/human-review-gate.json) | 1 | manual | 6 | agt_writer | An agent prepares a candidate result; a person approves, rejects or sends it back for revision — a bounded number of times. |
| [BI refresh](flows/bi-refresh.json) | 1 | schedule | 4 | — | On the schedule the owner chose: read the dashboard's freshness as the initiator (NexBI decides what they may see), post a short note to the Project thread. Ne… |
| [BI metric alert](flows/bi-metric-alert.json) | 1 | event | 5 | — | When a new version of the alert's dataset is published: NexBI runs the metric as the initiator, compares it with the threshold and counts consecutive versions;… |
| [BI subscription](flows/bi-subscription.json) | 1 | schedule | 4 | — | On the schedule the subscriber chose: read the dashboard's published version as the initiator and deliver its KPIs and link to the Project thread. Members only… |
| [Web source](flows/web-source.json) | 2 | event | 12 | agt_web_source_curator | When a web source of this Project is due (its schedule, or *Check now*): map the site politely — robots first, then sitemaps, then one link pass inside the con… |

## Patterns (9)

| Pattern | Template | What it does |
|---|---|---|
| [Sequential chain](patterns/sequential-chain.json) | `nexus://workflow/template/sequential-chain` | Steps in a fixed order; each one works on the result of the previous. |
| [Route to specialist](patterns/route-to-specialist.json) | `nexus://workflow/template/route-to-specialist` | A classifier decides which kind of request this is; the matching specialist handles it. |
| [Plan & execute](patterns/plan-execute.json) | `nexus://workflow/template/plan-execute` | A planner writes a bounded plan; an executor works through it; a reviewer checks the result. |
| [Parallel workers](patterns/parallel-workers.json) | `nexus://workflow/template/parallel-workers` | Run independent analyses at the same time and combine their results. |
| [Ensemble & judge](patterns/ensemble-judge.json) | `nexus://workflow/template/ensemble-judge` | Several candidates answer the same question; a judge picks the best or asks a person when they disagree. |
| [Model cascade](patterns/model-cascade.json) | `nexus://workflow/template/model-cascade` | Try the smallest qualified model first; escalate to a stronger one only when the check says it is not good enough. |
| [Goal loop](patterns/goal-evaluator-loop.json) | `nexus://workflow/template/goal-evaluator-loop` | Work, evaluate, repeat until the goal is met — with limits on iterations, time and budget. |
| [Execute, test, repair](patterns/execute-test-repair.json) | `nexus://workflow/template/execute-test-repair` | Generate, run it in the sandbox, validate with tests; on failure diagnose and repair — a few times, then ask a person. |
| [Human review gate](patterns/human-review-gate.json) | `nexus://workflow/template/human-review-gate` | An agent prepares a result; a person approves, rejects or sends it back — at most three rounds. |

## Blueprint, policies, sandbox profiles, dashboard templates

- **blueprint** (1): [Nexi Base](blueprints/nexus-base.json)
- **sandbox_profile** (4): [public-dev](sandbox/public-dev.json) · [dsk-analytics](sandbox/dsk-analytics.json) · [confidential-analytics](sandbox/confidential-analytics.json) · [skill-trial](sandbox/skill-trial.json)
- **policy** (5): [skill-sensitivity](policies/skill-sensitivity.json) · [tool-groups](policies/tool-groups.json) · [connector-kinds](policies/connector-kinds.json) · [model-roles](policies/model-roles.json) · [kpis](policies/kpis.json)
- **dashboard_template** (10): [Data overview](dashboards/data_overview.json) · [Executive overview](dashboards/executive_overview.json) · [Operational control](dashboards/operational_control.json) · [Performance vs target](dashboards/performance_vs_target.json) · [Risk & exceptions](dashboards/risk_exceptions.json) · [Nexi quality](dashboards/nexus_quality.json) · [Nexi people & activity](dashboards/nexus_usage.json) · [Nexi infrastructure](dashboards/nexus_infrastructure.json) · [NexGraph knowledge](dashboards/nexus_graph.json) · [Vibeban work](dashboards/nexus_vibeban.json)

## Coming (32)

Content that exists in the platform but is not published yet. It appears here the day its review is complete.

| Kind | Name | Version | Why not yet |
|---|---|---|---|
| skill | Technique — structure | 1.0.0 | review pending |
| skill | Technique — distributions | 1.0.0 | review pending |
| skill | Technique — integrity | 1.0.0 | review pending |
| skill | Technique — synthesis | 1.0.0 | review pending |
| skill | Need analysis | 0.1.0 | review pending |
| skill | Resolution planning | 0.2.0 | review pending |
| skill | Resolution report | 0.1.0 | review pending |
| skill | Web research planning | 0.1.0 | review pending |
| skill | Web page reading | 0.1.0 | review pending |
| skill | Research report | 0.1.0 | review pending |
| skill | Goal planning | 0.5.0 | review pending |
| skill | Goal verification | 0.1.0 | review pending |
| skill | Goal challenge | 0.4.0 | review pending |
| skill | Goal code | 0.1.0 | review pending |
| skill | Goal recovery analysis | 0.1.0 | review pending |
| agent | Data scientist | 12 | waits for 4 skill(s) |
| agent | Need analyst | 1 | governance not_reviewed |
| agent | Resolution planner | 1 | governance not_reviewed |
| agent | Resolution narrator | 1 | governance not_reviewed |
| agent | Research planner | 1 | waits for 1 skill(s) |
| agent | Web researcher | 1 | waits for 1 skill(s) |
| agent | Research narrator | 1 | waits for 1 skill(s) |
| agent | Goal planner | 3 | governance not_reviewed |
| agent | Goal verifier | 1 | governance not_reviewed |
| agent | Goal challenger | 3 | governance not_reviewed |
| agent | Goal coder | 1 | governance not_reviewed |
| agent | Goal recovery analyst | 1 | governance not_reviewed |
| flow | Agentic Data Scientist | 1 | names 5 held resource(s) |
| flow | Nexi Auto resolver | 1 | names 6 held resource(s) |
| flow | Web research | 1 | names 6 held resource(s) |
| flow | Nexi Goal resolution | 7 | names 10 held resource(s) |
| pattern | Agentic data scientist | — | its template is held |
