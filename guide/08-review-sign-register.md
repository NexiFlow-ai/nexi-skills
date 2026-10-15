# 8 · Review, sign, bring it to a deployment

A pack travels from your repository to an organization's Projects through four doors, each held by a different person
on purpose: the **reviewer** of a skill, the **publisher** who signs, the **operator** who trusts a key, and the **Owner
or Admin** who imports and installs. Nothing you do as the author opens any of them for you.

## 1. Review — the reviewer

Every skill's current version is read by a human before anyone is taught it. The platform enforces it twice: a pack's
`evaluation.human_review` must be `approved` for the version shipped, and the organization that installs the pack
records its own review of each skill before it teaches its agents.

As a publisher, make the review real:

- The reviewer is not the author. They read `SKILL.md`, both schemas, every example, and try at least one example
  through a model of the role the agent uses. They look for: invented facts in the expected outputs; a field the
  instruction never mentions; a missing "when the material is silent"; a missing injection clause; a size the schema
  allows that the instruction contradicts.
- They write it down:

  ```json
  "evaluation": { "human_review": { "state": "approved", "reviewed_by": "Ihor (Olena Co.)", "reviewed_at": "2026-10-15T09:00:00Z", "reviewed_version": "0.1.0" } }
  ```

- Any later change to the instruction or a schema bumps `version` and sets `state` back to `pending`.
  `nexi-pack validate` warns when `reviewed_version` differs from `version`.

The same applies, more lightly, to agents (`governance.state: approved` with `reviewed_at`) and Flows (`governance`,
and `security_review` when a Flow writes outside Nexi or reads above `confidential`).

## 2. Sign — the publisher

```sh
nexi-pack digest . --write
nexi-pack sign . --key ~/.nexi/olena.key --key-id olena-2026
nexi-pack verify . --publishers ./publishers.yaml
```

The signature is over the manifest, and the manifest pins every byte of every file. A deployment that trusts
`olena-2026` therefore trusts exactly these files and nothing else — a changed `SKILL.md` fails the digest, a changed
digest fails the signature.

- **One key per publisher**, rotated by adding a new `key_id` (`olena-2027`) to your `publishers.yaml` and signing new
  releases with it; old releases stay verifiable with the old entry.
- The private key lives where secrets live. If it leaks, publish a new key and tell operators to remove the old entry;
  there is no revocation beyond that, which is why the operator's file is a list they edit by hand.
- Archive the pack for release: `zip -r field-notes-0.1.0.zip field-notes/` (the directory at the root). Tag the
  repository with the same version.

## 3. Trust — the operator

A deployment keeps a publishers file: `key_id` · `public_key` · `name` per publisher it accepts. The operator adds your
entry — from your repository's `publishers.yaml` or from `REGISTRY.md` — and the deployment accepts packs signed by
that key from then on. No central authority, no store, no network call: trust is a line in a file the operator owns.

Until the operator has done this, an import of your pack fails with `PACK_PUBLISHER_UNKNOWN`, and says so.

## 4. Import and install — the Owner or Admin

In **NexCore › Blueprints & Packs**:

1. **Import pack** — upload the archive (`.zip` or `.tar`, up to 64 MiB). The deployment quarantines it, checks every
   digest, verifies the signature against the publishers file, parses every resource with its schema, and places the
   pack in the library. The verdict is shown check by check — ✓ / ✗ / unchecked — never a guess. A failure names one
   reason (`PACK_DIGEST_MISMATCH` · `PACK_PUBLISHER_UNKNOWN` · `PACK_SIGNATURE_INVALID` · `PACK_RESOURCE_INVALID` ·
   `PACK_PATTERN_TEMPLATE_MISSING` · …) and nothing is kept. **Import never installs.**
2. **Install now** — into the current organization. The blueprint layer joins the organization's chain under the base
   (and must tighten it, or the install is refused); agents, skills and Flow templates become available to the
   organization's Projects; Flows the blueprint names by role start where the platform starts them.
3. **Review the skills** — in the organization. A skill the pack brought is installed but inert until a person with the
   right to review records the review of its current version. `install --dry-run` lists these before you ship; the
   Owner sees them after.

Members see the library read-only; Install, Update and Remove are the administrator's. Remove takes the layer out of
the chain and darkens what the pack enabled; content the pack's agents created stays, read-only, in its application.

The same two steps exist as an API for operators who automate: `POST /blueprints/packs/import` (the file) and
`POST /blueprints/packs/{name}/install` (idempotent), with the same checks and the same closed reasons.

## 5. When does the conversation route to your agent?

After install, when:

- the agent's `governance.state` is `approved` and its `capability.routable` is not `false`;
- every skill it applies is reviewed in the organization;
- the person's Project allows the tools the agent needs, and the person holds the classification the ask touches;
- the ask's analysis matches the card better than the alternatives — other agents, a Flow, General answering itself.

Every routing decision is recorded with every candidate and the reasons, so an administrator can see why your agent
was or was not chosen. If it is never chosen, the card is the first thing to read (chapter 3); the second is whether
`intents` and `domains` describe what people actually type.

## 6. Updating

- Bump `metadata.version` (semver) and the versions of what changed (skills semver, agents and Flows integers).
- Re-review what changed. Re-sign. Tag.
- The administrator sees **Update** on the pack in the library; the update replaces the layer and the definitions,
  keeps instantiated Flows on their template version until a person updates them, and re-opens the review of any skill
  whose version changed.
- A breaking change to a skill's `output_schema` is a major version; say so in the release note — every Flow node with
  an `output_schema` over it needs the author's attention.

## 7. Listing it

A row in [`REGISTRY.md`](../REGISTRY.md): pack · publisher · repository · what it is for · the tag the maintainers
verified. The maintainers run `validate` and `verify`, check for secrets and personal data, and read the prompts for the
injection clause. That is the whole bar: the registry says *this exists and verifies*; a deployment's operator decides
whether to trust it.
