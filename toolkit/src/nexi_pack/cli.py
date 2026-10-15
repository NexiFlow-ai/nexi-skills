"""The `nexi-pack` command line.

    nexi-pack validate <pack> [--no-digests] [--strict]
    nexi-pack digest <pack> [--write]
    nexi-pack sign <pack> --key <file> --key-id <id> [--generate-key] [--publishers <yaml>]
    nexi-pack verify <pack> --publishers <yaml>
    nexi-pack install --dry-run <pack>
    nexi-pack new <name> [--dir <path>] [--publisher <name>]

Exit codes: 0 fine · 1 a finding or a failed check · 2 usage.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .pack import PackError, check_digests, compute_digests, read_pack, write_manifest
from .scaffold import scaffold
from .signing import (
    Publisher,
    generate_key,
    load_key,
    load_publishers,
    public_key_b64,
    save_publisher,
    sign_manifest,
    verify_manifest,
)
from .validate import validate_pack


def cmd_validate(args: argparse.Namespace) -> int:
    pack, findings = validate_pack(args.pack, digests=not args.no_digests, strict_refs=args.strict)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    for f in findings:
        print(f)
    if pack is not None:
        kinds: dict[str, int] = {}
        for r in pack.resources:
            kinds[r.kind] = kinds.get(r.kind, 0) + 1
        summary = " · ".join(f"{n} {k}" for k, n in sorted(kinds.items()))
        print(f"{pack.name} {pack.version}: {summary}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s) — {'not valid' if errors else 'valid'}")
    return 1 if errors else 0


def cmd_digest(args: argparse.Namespace) -> int:
    pack = read_pack(args.pack)
    actual = compute_digests(pack)
    changed = [r.path for r in pack.resources if r.digest != actual[r.path]]
    for path in changed:
        print(f"{path}: {pack.manifest and next(r.digest for r in pack.resources if r.path == path)} → {actual[path]}")
    if not changed:
        print(f"{len(actual)} digest(s) match the files")
        return 0
    if args.write:
        manifest = dict(pack.manifest)
        for item in manifest["resources"]:
            item["digest"] = actual[item["path"]]
        if "signature" in manifest:
            del manifest["signature"]
            print("signature removed — the manifest changed; sign it again")
        write_manifest(pack, manifest)
        print(f"{len(changed)} digest(s) updated")
        return 0
    print(f"{len(changed)} digest(s) differ — run with --write to update the manifest")
    return 1


def cmd_sign(args: argparse.Namespace) -> int:
    key_path = Path(args.key)
    if args.generate_key:
        if key_path.exists():
            print(f"{key_path} exists — not overwriting a key", file=sys.stderr)
            return 1
        key, public = generate_key(key_path)
        print(f"generated {key_path} (private, keep it out of the repository) — public key {public}")
        if args.publishers:
            save_publisher(Path(args.publishers), Publisher(args.key_id, public, args.publisher_name or args.key_id))
            print(f"registered {args.key_id} in {args.publishers}")
    key = load_key(key_path)
    pack = read_pack(args.pack)
    manifest = dict(pack.manifest)
    actual = compute_digests(pack)
    for item in manifest["resources"]:
        item["digest"] = actual[item["path"]]
    signed = sign_manifest(manifest, key, args.key_id)
    write_manifest(pack, signed)
    _, findings = validate_pack(args.pack)
    errors = [f for f in findings if f.level == "error"]
    for f in errors:
        print(f)
    print(f"signed {pack.name} {pack.version} with {args.key_id} ({len(actual)} resources)" + (" — but it is not valid" if errors else ""))
    return 1 if errors else 0


def cmd_verify(args: argparse.Namespace) -> int:
    pack = read_pack(args.pack)
    bad = check_digests(pack)
    for path in bad:
        print(f"digest mismatch: {path}")
    sig = pack.manifest.get("signature") or {}
    publishers = load_publishers(Path(args.publishers))
    pub = publishers.get(str(sig.get("key_id")))
    if not sig:
        print("unsigned")
        return 1
    if pub is None:
        print(f"unknown publisher {sig.get('key_id')!r} — not in {args.publishers}")
        return 1
    ok = verify_manifest(pack.manifest, pub.public_key)
    print(f"signature by {pub.key_id} ({pub.name or 'no name'}): {'valid' if ok else 'INVALID'}")
    return 0 if ok and not bad else 1


def cmd_install(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("nexi-pack never installs: a pack is imported and installed by an Owner or Admin in NexCore › Blueprints & Packs. Use --dry-run to see what that install would apply.", file=sys.stderr)
        return 2
    pack, findings = validate_pack(args.pack)
    if pack is None:
        for f in findings:
            print(f)
        return 1
    errors = [f for f in findings if f.level == "error"]
    print(f"{pack.name} {pack.version} — what an install into an organization would apply")
    print(f"  signature: {pack.manifest.get('signature', {}).get('key_id') or 'UNSIGNED — a deployment refuses it'}")
    print(f"  layer: {pack.manifest.get('layer')}")
    for dep in pack.manifest.get("depends_on") or []:
        print(f"  depends on: {dep.get('name')} {dep.get('version_range')}")
    by_kind: dict[str, list[str]] = {}
    for r in pack.resources:
        if r.kind == "prompt":
            continue
        by_kind.setdefault(r.kind, []).append(f"{r.name or r.path}" + (f" {r.version}" if r.version else ""))
    for kind, items in sorted(by_kind.items()):
        print(f"  {kind} ({len(items)}): " + " · ".join(items))
    for r in pack.by_kind("blueprint"):
        bp = pack.read_json(r.path)
        defaults = bp.get("defaults") or {}
        if defaults.get("flows"):
            print("  flow roles: " + " · ".join(f"{role} → {uri.split('/')[-1]}" for role, uri in defaults["flows"].items()))
        allow = (bp.get("tool_policy") or {}).get("allowlist") or []
        print(f"  platform tools the blueprint allows ({len(allow)}): " + " · ".join(u.split('/')[-1] for u in allow))
    req = pack.manifest.get("requires") or {}
    if req.get("models"):
        print("  model roles required: " + " · ".join(m.get("role", "?") for m in req["models"]))
    if req.get("connections"):
        print("  connections required: " + " · ".join(f"{c.get('name')} ({c.get('tool_uri')})" for c in req["connections"]))
    if req.get("sandbox_runtimes"):
        print("  sandbox runtimes: " + " · ".join(req["sandbox_runtimes"]))
    pending = [r.path for r in pack.by_kind("skill") if ((pack.read_json(r.path).get("evaluation") or {}).get("human_review") or {}).get("state") != "approved"]
    if pending:
        print(f"  skills nobody would be taught (review not approved): " + " · ".join(pending))
    if errors:
        print(f"  {len(errors)} validation error(s) — the import would be refused:")
        for f in errors:
            print(f"    {f}")
        return 1
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    target = Path(args.dir or args.name)
    try:
        scaffold(target, args.name, publisher=args.publisher or "Your name")
    except (ValueError, FileExistsError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"created {target} — now: nexi-pack validate {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nexi-pack", description="Validate, digest, sign, verify and scaffold Nexi packs.")
    p.add_argument("--version", action="version", version=f"nexi-pack {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="schemas · digests · references")
    v.add_argument("pack")
    v.add_argument("--no-digests", action="store_true", help="skip the digest check (while editing)")
    v.add_argument("--strict", action="store_true", help="a reference to content this pack does not ship is an error, not a warning")
    v.set_defaults(func=cmd_validate)

    d = sub.add_parser("digest", help="compare, or rewrite, the digests in the manifest")
    d.add_argument("pack")
    d.add_argument("--write", action="store_true")
    d.set_defaults(func=cmd_digest)

    s = sub.add_parser("sign", help="fill the digests and sign the manifest with your Ed25519 key")
    s.add_argument("pack")
    s.add_argument("--key", required=True, help="file holding the base64 seed (created with --generate-key)")
    s.add_argument("--key-id", required=True)
    s.add_argument("--generate-key", action="store_true")
    s.add_argument("--publishers", help="register the public key in this publishers file (with --generate-key)")
    s.add_argument("--publisher-name")
    s.set_defaults(func=cmd_sign)

    vf = sub.add_parser("verify", help="check the digests and the signature against a publishers file")
    vf.add_argument("pack")
    vf.add_argument("--publishers", required=True)
    vf.set_defaults(func=cmd_verify)

    i = sub.add_parser("install", help="--dry-run: what an install would apply (nexi-pack never installs)")
    i.add_argument("pack")
    i.add_argument("--dry-run", action="store_true")
    i.set_defaults(func=cmd_install)

    n = sub.add_parser("new", help="scaffold a minimal pack: one skill, one agent, one Flow, a blueprint layer")
    n.add_argument("name")
    n.add_argument("--dir")
    n.add_argument("--publisher")
    n.set_defaults(func=cmd_new)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except PackError as exc:
        print(f"{exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
