"""Ed25519 signing and verification of a pack manifest — the deployment's exact conventions.

- the private key is a 32-byte seed, kept as standard base64 in a file nobody commits (mode 0600);
- the public key and the signature travel as base64url without padding;
- the signature is over `canonical_payload(manifest)` (see `pack.py`);
- a publishers file (YAML) lists `key_id` · `public_key` · `name` per trusted publisher — public keys only.
"""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .pack import canonical_payload


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64url(text: str) -> bytes:
    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded)


@dataclass
class Publisher:
    key_id: str
    public_key: str
    name: str = ""


def generate_key(path: Path) -> tuple[Ed25519PrivateKey, str]:
    """Write a fresh seed to `path` (0600) and return the key with its base64url public half."""
    key = Ed25519PrivateKey.generate()
    seed = key.private_bytes_raw()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(base64.b64encode(seed).decode("ascii") + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return key, public_key_b64(key)


def load_key(path: Path) -> Ed25519PrivateKey:
    seed = base64.b64decode(path.read_text(encoding="utf-8").strip())
    if len(seed) != 32:
        raise ValueError("an Ed25519 seed is 32 bytes (base64 in the key file)")
    return Ed25519PrivateKey.from_private_bytes(seed)


def public_key_b64(key: Ed25519PrivateKey) -> str:
    return _b64url(key.public_key().public_bytes_raw())


def sign_manifest(manifest: dict[str, Any], key: Ed25519PrivateKey, key_id: str) -> dict[str, Any]:
    """Return the manifest with a fresh `signature` member over everything else."""
    body = {k: v for k, v in manifest.items() if k != "signature"}
    value = _b64url(key.sign(canonical_payload(body)))
    return {**body, "signature": {"alg": "ed25519", "key_id": key_id, "value": value}}


def verify_manifest(manifest: dict[str, Any], public_key: str) -> bool:
    sig = manifest.get("signature") or {}
    if sig.get("alg") != "ed25519" or not sig.get("value"):
        return False
    try:
        Ed25519PublicKey.from_public_bytes(_unb64url(public_key)).verify(_unb64url(sig["value"]), canonical_payload(manifest))
    except (InvalidSignature, ValueError):
        return False
    return True


def load_publishers(path: Path) -> dict[str, Publisher]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, Publisher] = {}
    for item in doc.get("publishers", []):
        if isinstance(item, dict) and item.get("key_id") and item.get("public_key"):
            out[str(item["key_id"])] = Publisher(str(item["key_id"]), str(item["public_key"]), str(item.get("name", "")))
    return out


def save_publisher(path: Path, publisher: Publisher) -> None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
    doc = doc or {"version": 1, "publishers": []}
    doc["publishers"] = [p for p in doc.get("publishers", []) if p.get("key_id") != publisher.key_id]
    doc["publishers"].append({"key_id": publisher.key_id, "public_key": publisher.public_key, "name": publisher.name})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
