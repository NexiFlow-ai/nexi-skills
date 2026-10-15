"""nexi-pack — validate, digest, sign, verify and scaffold Nexi packs.

A pack is a directory with a `manifest.json` that lists every file with its sha256 digest and carries one Ed25519
signature by the publisher. This toolkit reads a pack the way a Nexi deployment does — digests first, then every
resource against its JSON Schema, then the references between resources — so what passes here is what NexCore
accepts. It imports nothing from the platform; the schemas it validates with are bundled.
"""

__version__ = "0.1.0"
