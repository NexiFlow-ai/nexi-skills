# The Nexi pack format

A **pack** (`NexusPack`, `api_version: nexus/v1`) is a directory. Its `manifest.json` lists every file the pack ships
with the file's sha256 digest, declares what the pack requires from a deployment, and carries one Ed25519 signature by
the publisher. A deployment loads a pack whole or not at all: one missing file, one digest that does not match, one
unknown publisher, and nothing of the pack is read.

The schemas: [`toolkit/src/nexi_pack/schemas/`](./toolkit/src/nexi_pack/schemas/) — `nexus-pack-manifest.schema.json`
is the manifest; the others are the resources. `nexi-pack validate` applies them.

## The manifest

```json
{
  "api_version": "nexus/v1",
  "kind": "NexusPack",
  "metadata": {
    "name": "my-pack",                    // ^[a-z][a-z0-9-]{1,62}$ — the pack's uri is nexus://core/pack/<name>
    "version": "0.1.0",                   // semver
    "display_name": "My Pack",
    "publisher": "Olena Co.",
    "description": "…",
    "license": "Apache-2.0",
    "homepage": "https://…",
    "created_at": "2026-10-15T00:00:00Z"
  },
  "layer": "domain",                      // base | domain | organization | project — where the blueprint sits
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
  "contains_secrets": false,              // a constant — a pack never carries a credential
  "readme_path": "README.md",
  "signature": { "alg": "ed25519", "key_id": "olena-2026", "value": "<base64url>" }
}
```

(JSON has no comments; they are here for reading.)

## Resource kinds

| `kind` | File | Schema | Notes |
|---|---|---|---|
| `blueprint` | `blueprints/<name>.json` | `blueprint.schema.json` | Exactly one per pack. `source_pack_uri` is the pack's own uri. |
| `skill` | `skills/<name>/skill.json` | `skill-manifest.schema.json` | `entry: SKILL.md`; the instruction is the `prompt` next to it. |
| `agent` | `agents/<name>.json` | `agent-definition.schema.json` | The instruction is `agents/<name>.md` (a `prompt`), or inline `instructions`. |
| `prompt` | any `.md` | — | Digest-verified, never interpreted by itself. |
| `flow_template` | `flows/<name>.json`, `patterns/templates/<name>.json` | `workflow-spec.schema.json` | `project_id: null`, `template.is_template: true`. |
| `pattern` | `patterns/<name>.json` | `pattern-definition.schema.json` | An authoring abstraction over one shipped template; `requires.node_types` equals the template's node kinds. |
| `sandbox_profile` | `sandbox/<name>.json` | `sandbox-profile.schema.json` | Where model-written code runs. |
| `policy` | `policies/<name>.json` | — | A JSON document with a `kind`: tool groups · connector kinds · model roles · skill sensitivity · KPIs. |
| `dashboard_template` | `dashboards/<name>.json` | `bi-dashboard-template.schema.json` | Slot structures for BI dashboards. |
| `ontology` · `schema` · `evaluation` · `tool_*` · `ui_config` · `migration` | — | — | Verified, carried, interpreted by the application they belong to. |
| `module` · `tasks.project_template` · `sales.field_preset` | `module/` · `projects/` · `fields/` | — | Suite-module packs; see the deployment's documentation. |

Every `path` is relative, inside the pack, without `..`. Every `uri` in the manifest equals the `uri` inside the file.

## Digests

`digest` is `sha256:<64 hex>` of the file's bytes exactly as shipped. `nexi-pack digest --write` recomputes them; any
change to a file invalidates the signature, which `digest --write` therefore removes.

## The signature

The publisher signs the **canonical payload**: the manifest without `signature`, serialised as JSON with keys sorted,
no whitespace, UTF-8, non-ASCII characters kept as they are — in Python,
`json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`. Write no `null` members
into the manifest: the deployment canonicalises from a parsed model that drops them, and the two forms must agree byte
for byte.

- `alg` is `ed25519`; `value` is the 64-byte signature as base64url without padding.
- `key_id` names an entry of the deployment's **publishers file** (`key_id` · `public_key` as base64url of the 32 raw
  bytes · `name`). The operator of a deployment decides whom to trust by editing that file; nothing else grants trust.
- A private key is a 32-byte seed. `nexi-pack sign --generate-key` writes it base64-encoded with mode 0600. It never
  enters a repository, a pack, a prompt or a log.

## What a deployment does with a pack

1. **Import** — an Owner or Admin uploads the archive. The deployment reads the manifest, checks every digest, verifies
   the signature against its publishers file, parses every resource with its schema, and places the pack in the
   library. Any failure names its reason (`PACK_DIGEST_MISMATCH`, `PACK_PUBLISHER_UNKNOWN`, `PACK_SIGNATURE_INVALID`,
   `PACK_RESOURCE_INVALID`, …) and nothing of the pack is kept.
2. **Install** — into one organization: the blueprint layer is applied (defaults, tool allow-list, model policy,
   approvals), agents and skills become available to that organization's Projects, Flow templates become
   instantiable, routable agents join the conversation's capability routing.
3. **Review** — a skill nobody reviewed at its current version is installed but **teaches nobody** until a human in
   that organization records the review. The pack's `evaluation.human_review` is the publisher's review; the
   organization's is its own.

`nexi-pack install --dry-run` prints what step 2 would apply.
