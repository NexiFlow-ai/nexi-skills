# Nexi Skills

The open pack commons of Nexi: the Nexi Base pack as a reference (its reviewed skills, agents, Flows, patterns and policies), the nexi-pack toolkit, the pack format with its schemas, and the guide to building your own agents and bringing them to a Nexi deployment.

## This repository is a publication

Every file here was exported from the Nexi source repository at tag **`public/skills/v0.1.0`** (commit `5d56559a47e57efc65ce5e3b2fdf03720c02f71b`) by a
publication pipeline that runs a guard over the whole export before anything is pushed. The export is reproducible:
`PROVENANCE.json` lists every file with its sha256 and the digest of the whole; the same tag yields the same digest.

- Changes land in the source first; this copy is regenerated on the next export. A pull request here is answered
  and closed with the tag that carried the change — see `CONTRIBUTING.md` in the organization's `.github` repository.
- The canonical site is https://docs.nexiflow.ai/docs/build/packs/; the GitHub Pages branch of this repository mirrors the same export.
- Version: **0.1.0** · unit: `skills` · licence: **Apache-2.0** (LICENSE) · third-party notices: NOTICE ·
  names: TRADEMARKS.md.

## Reporting a problem

A mistake in the content: open an issue here. A security concern: use the private vulnerability reporting of this
repository (Security → Report a vulnerability) — never a public issue.

## What is here

| Path | What it is |
|---|---|
| [`guide/`](./guide/README.md) | **The guide** — from what a pack is to your own agents running in a Nexi deployment: skills, agents, Flows, the blueprint layer, the sandbox, the best practices the platform itself follows, review, signing, registration. Ukrainian: [`uk/guide/`](./uk/guide/README.md). |
| [`packs/nexus-base/`](./packs/nexus-base/README.md) | **Nexi Base**, the reference pack — the reviewed skills, agents, Flows, patterns, policies, sandbox profiles and dashboard templates every organization starts from. Its [`CATALOGUE.md`](./packs/nexus-base/CATALOGUE.md) lists what is published and what is *coming*. Signed by the Nexi publisher; verify it yourself with `nexi-pack verify`. |
| [`toolkit/`](./toolkit/README.md) | **`nexi-pack`** — validate · digest · sign · verify · `install --dry-run` · `new`. `pip install ./toolkit`. The JSON Schemas of the pack format are bundled under `toolkit/src/nexi_pack/schemas/`. |
| [`SPEC.md`](./SPEC.md) | The pack format: the manifest, the resource kinds, digests, the signature, the canonical payload. |
| [`publishers.yaml`](./publishers.yaml) | The Nexi publisher's public key — the entry a deployment operator adds to trust Nexi Base. |
| [`REGISTRY.md`](./REGISTRY.md) | The community registry: packs others published, with their publisher key — and how to list yours. |

## Start here

```sh
pip install ./toolkit
nexi-pack verify packs/nexus-base --publishers publishers.yaml   # the reference pack, as a deployment sees it
nexi-pack new my-pack                                              # your own: one skill, one agent, one Flow
nexi-pack validate my-pack
```

Then read the guide — [chapter 7](./guide/07-your-first-pack.md) walks the scaffold to a signed pack,
[chapter 8](./guide/08-review-sign-register.md) brings it to a deployment, [chapter 9](./guide/09-best-practices.md) is
the list of rules the platform's own packs keep.

## What this repository is not

It is not the platform. The services that run a pack — the conversation, the Flow engine, the sandbox, the policy
enforcement — are Nexi, a commercial product (see the organization's profile). Everything here is Apache-2.0 so that a
pack you write is yours, runs on any Nexi deployment that trusts your key, and can be read, reviewed and reused by anyone.
