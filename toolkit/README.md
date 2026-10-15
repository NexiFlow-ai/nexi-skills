# nexi-pack

Validate, digest, sign, verify and scaffold **Nexi packs** — the skills, agents, Flows and blueprint layer a
Nexi deployment installs into an organization. No Nexi service is needed: the toolkit reads a pack the way the
platform does and validates against the same JSON Schemas, bundled.

```sh
pip install nexi-pack            # or: pip install ./toolkit  from the nexi-skills repository
nexi-pack new my-pack            # a minimal pack: one skill, one agent, one Flow, a blueprint layer
nexi-pack validate my-pack       # schemas · digests · references
nexi-pack sign my-pack --key ~/.nexi/my.key --key-id my-pack-2026 --generate-key --publishers my-publishers.yaml
nexi-pack verify my-pack --publishers my-publishers.yaml
nexi-pack install --dry-run my-pack
```

## Commands

| Command | What it does | Exit 1 when |
|---|---|---|
| `validate <pack> [--no-digests] [--strict]` | The manifest against its schema; every listed file present and matching its digest; every resource against the schema of its kind (skill · agent · flow template · blueprint · sandbox profile · pattern · dashboard template; a policy names its `kind`); the references between them — an agent's skills, a Flow's agents and skills, a pattern's template, the one blueprint. A reference to content the pack does not ship is a warning (a pack it depends on must ship it) — `--strict` makes it an error. A skill whose current version is not `approved` is a warning: a deployment teaches nobody an unreviewed skill. | any error |
| `digest <pack> [--write]` | Compares the digests in the manifest with the files. `--write` updates them and removes a signature that no longer holds. | digests differ (without `--write`) |
| `sign <pack> --key <file> --key-id <id> [--generate-key] [--publishers <yaml>] [--publisher-name <name>]` | Fills the digests and writes one Ed25519 signature over the canonical manifest. `--generate-key` creates the key file (a base64 32-byte seed, mode 0600 — never commit it) and, with `--publishers`, registers the *public* half under `key-id`. Validates afterwards. | the signed pack is not valid |
| `verify <pack> --publishers <yaml>` | Checks the digests and the signature against a publishers file (`key_id` · `public_key` · `name` per publisher — public keys only). This is what a deployment does before it imports a pack. | unsigned · unknown publisher · invalid · a digest differs |
| `install --dry-run <pack>` | What an install into an organization would apply: the resources by kind, the Flow roles, the platform tools the blueprint allows, the model roles, connections and sandbox runtimes required, the skills nobody would be taught. `nexi-pack` never installs — an Owner or Admin does, in NexCore › Blueprints & Packs. | validation errors |
| `new <name> [--dir <path>] [--publisher <name>]` | Scaffolds a pack that validates: one skill with schemas and an example, one agent applying it, one scheduled Flow, a blueprint layer on Nexi Base, the manifest with digests filled (unsigned). | name taken or invalid |

## The rules it checks (and a deployment enforces)

- **Whole or nothing.** Every file is listed with its sha256; one mismatch refuses the pack.
- **One signature, one publisher.** The manifest without `signature`, as canonical JSON (keys sorted, no whitespace,
  UTF-8, no `null` members), signed with Ed25519; the signature and the public key travel as base64url without padding.
  A deployment accepts only publishers its operator listed.
- **A skill teaches; it owns nothing.** `input_schema`, `output_schema`, examples, `evaluation.human_review` — no tools,
  no model, no credentials.
- **A Flow template is a template.** `project_id` null, `template.is_template` true; agents and skills by uri.
- **A pattern abstracts a shipped template** and names exactly the node kinds that template uses.
- **Exactly one blueprint** per pack, whose `source_pack_uri` is the pack's own uri.

## Python API

```python
from nexi_pack.validate import validate_pack
from nexi_pack.signing import load_key, sign_manifest, verify_manifest

pack, findings = validate_pack("my-pack")
errors = [f for f in findings if f.level == "error"]
```

Licence: Apache-2.0. The schemas under `nexi_pack/schemas/` are the platform's contracts, published with the toolkit.
