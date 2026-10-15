# Registry

Packs published for Nexi, by whom, under which key. A deployment trusts a publisher only when its operator adds the
publisher's key to the deployment's publishers file — a row here is a pointer, never a grant.

## Publishers

| Publisher | `key_id` | Public key | Packs |
|---|---|---|---|
| Nexi | `nexus-base-2026` | see [`publishers.yaml`](./publishers.yaml) | [Nexi Base](./packs/nexus-base/README.md) |

## Community packs

*None yet — be the first.*

| Pack | Publisher | Repository | What it is for | Verified with |
|---|---|---|---|---|

## Listing a pack

A pull request to this file with one row in *Community packs* and, if you are new, one in *Publishers*. The review
checks:

1. `nexi-pack validate` and `nexi-pack verify` pass on the repository's tagged release, with the publishers entry you
   provide — the maintainers run both.
2. The pack carries no credential, endpoint, tenant data or personal data; `contains_secrets` is `false` and true.
3. Every skill's current version has a `human_review` naming a reviewer; every prompt says that content is data, never
   instruction (chapter 9 of the guide).
4. The licence is named in the manifest and compatible with being read and reused (Apache-2.0, MIT, BSD, …).
5. The row says what the pack is *for* in one sentence a reader can judge — not what it is made of.

A listed pack is removed on a security report the publisher does not answer within 14 days, or at the publisher's
request. The maintainers do not review a pack's quality beyond these checks; a deployment's operator does.
