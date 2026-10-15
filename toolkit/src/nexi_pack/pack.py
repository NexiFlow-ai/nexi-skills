"""Reading a pack directory: the manifest, the files, their digests, the canonical signing payload.

These rules are the deployment's rules, written once more without the platform's models so a pack author needs no
Nexi service to check a pack:

- a resource `path` is relative, inside the pack, never `..`;
- `digest` is `sha256:<hex>` of the file's bytes — one mismatch and the whole pack is refused;
- the signing payload is the manifest without `signature`, as canonical JSON: keys sorted, no whitespace, UTF-8,
  non-ASCII kept as is (`json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`). Write no `null`
  members into a manifest — the deployment canonicalises from a parsed model that drops them, and the two forms must
  agree byte for byte.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MANIFEST_FILE = "manifest.json"
SKILL_ENTRY = "SKILL.md"

#: Resource kinds a pack may list, as the deployment names them.
KINDS_WITH_SCHEMA = {
    "blueprint": "blueprint.schema.json",
    "agent": "agent-definition.schema.json",
    "skill": "skill-manifest.schema.json",
    "flow_template": "workflow-spec.schema.json",
    "sandbox_profile": "sandbox-profile.schema.json",
    "pattern": "pattern-definition.schema.json",
    "dashboard_template": "bi-dashboard-template.schema.json",
}


class PackError(Exception):
    """The pack cannot be read. `code` is stable; `detail` names the file or field."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass
class Resource:
    kind: str
    path: str
    digest: str | None
    uri: str | None
    name: str | None
    version: str | None
    raw: dict[str, Any]


@dataclass
class Pack:
    root: Path
    manifest: dict[str, Any]
    resources: list[Resource] = field(default_factory=list)

    @property
    def name(self) -> str:
        return str(self.manifest.get("metadata", {}).get("name", "?"))

    @property
    def version(self) -> str:
        return str(self.manifest.get("metadata", {}).get("version", "?"))

    def by_kind(self, kind: str) -> list[Resource]:
        return [r for r in self.resources if r.kind == kind]

    def file(self, rel: str) -> Path:
        target = (self.root / rel).resolve()
        if self.root.resolve() not in target.parents:
            raise PackError("PACK_PATH_ESCAPES", rel)
        return target

    def read_json(self, rel: str) -> dict[str, Any]:
        data = self.file(rel).read_text(encoding="utf-8")
        try:
            doc = json.loads(data)
        except ValueError as exc:
            raise PackError("PACK_RESOURCE_INVALID", f"{rel}: not JSON ({exc})") from exc
        if not isinstance(doc, dict):
            raise PackError("PACK_RESOURCE_INVALID", f"{rel}: not a JSON object")
        return doc


def sha256_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_payload(manifest: dict[str, Any]) -> bytes:
    """What the publisher signs — identical to the deployment's `signing_payload`."""
    body = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def read_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_FILE
    if not path.is_file():
        raise PackError("PACK_MANIFEST_MISSING", str(path))
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise PackError("PACK_MANIFEST_INVALID", f"{path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise PackError("PACK_MANIFEST_INVALID", f"{path}: not a JSON object")
    return doc


def read_pack(root: str | Path) -> Pack:
    """Read the manifest and list its resources. Digests are *not* checked here — see `check_digests`."""
    base = Path(root)
    manifest = read_manifest(base)
    resources: list[Resource] = []
    for item in manifest.get("resources", []):
        if not isinstance(item, dict) or "path" not in item or "kind" not in item:
            raise PackError("PACK_MANIFEST_INVALID", f"resource without kind/path: {item!r}"[:200])
        resources.append(
            Resource(
                kind=str(item["kind"]),
                path=str(item["path"]),
                digest=item.get("digest"),
                uri=item.get("uri"),
                name=item.get("name"),
                version=item.get("version"),
                raw=item,
            )
        )
    return Pack(root=base, manifest=manifest, resources=resources)


def compute_digests(pack: Pack) -> dict[str, str]:
    """{path: sha256 digest} of every listed file as it is on disk."""
    out: dict[str, str] = {}
    for r in pack.resources:
        file = pack.file(r.path)
        if not file.is_file():
            raise PackError("PACK_RESOURCE_MISSING", r.path)
        out[r.path] = sha256_digest(file.read_bytes())
    return out


def check_digests(pack: Pack) -> list[str]:
    """The paths whose digest in the manifest does not match the file — empty when the pack is whole."""
    actual = compute_digests(pack)
    return [r.path for r in pack.resources if r.digest != actual[r.path]]


def write_manifest(pack: Pack, manifest: dict[str, Any] | None = None) -> None:
    doc = manifest if manifest is not None else pack.manifest
    (pack.root / MANIFEST_FILE).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
