"""nexi-pack — the walk-through of AC-2823 · AC-2824 · AC-2825 as tests.

Runs with the toolkit alone (`pip install ./toolkit[dev] && pytest`). The interop test against the platform's verifier
runs only where the platform packages are importable (the monorepo) and is skipped elsewhere.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from nexi_pack.cli import main
from nexi_pack.pack import canonical_payload, read_pack
from nexi_pack.scaffold import scaffold
from nexi_pack.signing import generate_key, load_key, load_publishers, sign_manifest, verify_manifest
from nexi_pack.validate import validate_pack


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    return scaffold(tmp_path / "olena-pack", "olena-pack", publisher="Olena")


def errors(findings):
    return [f for f in findings if f.level == "error"]


def test_scaffold_validates(pack: Path) -> None:
    loaded, findings = validate_pack(str(pack))
    assert loaded is not None and loaded.name == "olena-pack"
    assert errors(findings) == []
    messages = [f.message for f in findings]
    assert any("unsigned" in m for m in messages)
    assert any("human_review is 'pending'" in m for m in messages)


def test_broken_digest_names_the_file(pack: Path) -> None:
    (pack / "agents/olena-pack-assistant.md").write_text("# edited\n", encoding="utf-8")
    _, findings = validate_pack(str(pack))
    bad = errors(findings)
    assert len(bad) == 1 and bad[0].path == "agents/olena-pack-assistant.md" and "digest" in bad[0].message


def test_missing_output_schema_names_the_field(pack: Path) -> None:
    skill = pack / "skills/olena-pack-brief/skill.json"
    doc = json.loads(skill.read_text(encoding="utf-8"))
    del doc["output_schema"]
    skill.write_text(json.dumps(doc), encoding="utf-8")
    _, findings = validate_pack(str(pack), digests=False)
    bad = errors(findings)
    assert len(bad) == 1 and bad[0].path.endswith("skill.json") and "`output_schema`" in bad[0].message


def test_schema_violation_names_the_field(pack: Path) -> None:
    agent = pack / "agents/olena-pack-assistant.json"
    doc = json.loads(agent.read_text(encoding="utf-8"))
    doc["inference"]["role"] = "wizard"
    agent.write_text(json.dumps(doc), encoding="utf-8")
    _, findings = validate_pack(str(pack), digests=False)
    bad = errors(findings)
    assert bad and bad[0].path == "agents/olena-pack-assistant.json" and bad[0].message.startswith("inference/role")


def test_pattern_must_abstract_a_shipped_template(pack: Path) -> None:
    (pack / "patterns").mkdir()
    (pack / "patterns/one.json").write_text(json.dumps({
        "api_version": "nexus/v1", "kind": "FlowPattern",
        "metadata": {"id": "one", "name": "One", "version": "1.0", "category": "orchestration", "layer": "flow_pattern", "human_reviewed_by": "Olena", "reviewed_at": "2026-10-15T00:00:00Z"},
        "description": "x", "use_when": ["x"], "examples": ["x"],
        "characteristics": {"autonomy": "low", "cost": "low", "latency": "low", "reliability": "high"},
        "template": {"workflow_uri": "nexus://workflow/template/missing", "version": "1.0.0", "file": "templates/missing.json"},
        "requires": {"node_types": ["agent"]},
    }), encoding="utf-8")
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    manifest["resources"].append({"kind": "pattern", "path": "patterns/one.json", "digest": "sha256:" + "0" * 64})
    (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    _, findings = validate_pack(str(pack), digests=False)
    assert any(f.path == "patterns/one.json" and "not shipped" in f.message for f in errors(findings))


def test_sign_verify_roundtrip(pack: Path, tmp_path: Path) -> None:
    key, public = generate_key(tmp_path / "k.key")
    assert (tmp_path / "k.key").stat().st_mode & 0o777 == 0o600
    loaded = read_pack(pack)
    signed = sign_manifest(loaded.manifest, key, "olena-2026")
    assert signed["signature"]["alg"] == "ed25519" and signed["signature"]["key_id"] == "olena-2026"
    assert verify_manifest(signed, public)
    tampered = {**signed, "metadata": {**signed["metadata"], "version": "9.9.9"}}
    assert not verify_manifest(tampered, public)
    assert canonical_payload(signed) == canonical_payload({**signed, "signature": {"alg": "ed25519", "key_id": "x", "value": "x"}})


def test_cli_sign_registers_the_public_key_and_verify_accepts(pack: Path, tmp_path: Path, capsys) -> None:
    publishers = tmp_path / "publishers.yaml"
    assert main(["sign", str(pack), "--key", str(tmp_path / "olena.key"), "--key-id", "olena-2026", "--generate-key", "--publishers", str(publishers), "--publisher-name", "Olena"]) == 0
    assert load_publishers(publishers)["olena-2026"].name == "Olena"
    assert main(["verify", str(pack), "--publishers", str(publishers)]) == 0
    assert "valid" in capsys.readouterr().out
    # a stranger's key is refused
    other = tmp_path / "other.yaml"
    other.write_text("version: 1\npublishers:\n- key_id: someone-2026\n  public_key: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n  name: Someone\n", encoding="utf-8")
    assert main(["verify", str(pack), "--publishers", str(other)]) == 1
    assert "unknown publisher" in capsys.readouterr().out


def test_digest_write_drops_a_stale_signature(pack: Path, tmp_path: Path, capsys) -> None:
    assert main(["sign", str(pack), "--key", str(tmp_path / "k.key"), "--key-id", "k", "--generate-key"]) == 0
    (pack / "README.md").write_text("changed\n", encoding="utf-8")  # not a resource — no digest changes
    assert main(["digest", str(pack)]) == 0
    (pack / "agents/olena-pack-assistant.md").write_text("# changed\n", encoding="utf-8")
    assert main(["digest", str(pack)]) == 1
    assert main(["digest", str(pack), "--write"]) == 0
    assert "signature" not in json.loads((pack / "manifest.json").read_text(encoding="utf-8"))


def test_install_is_dry_run_only(pack: Path, capsys) -> None:
    assert main(["install", str(pack)]) == 2
    assert main(["install", "--dry-run", str(pack)]) == 0
    out = capsys.readouterr().out
    assert "UNSIGNED" in out and "platform tools the blueprint allows (2)" in out and "model roles required: chat" in out


def test_toolkit_imports_nothing_from_the_platform() -> None:
    """FIT-2805: the toolkit's import graph stays inside itself and its declared dependencies."""
    import nexi_pack

    src = Path(nexi_pack.__file__).parent
    forbidden = ("nexus_contracts", "nexus_security", "core_api", "chat_api", "nexus_app_kernel", "platform.", "apps.")
    for file in src.rglob("*.py"):
        text = file.read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text and f"from {name}" not in text, f"{file.name} imports {name}"


def test_bundled_schemas_are_in_sync_with_the_contracts() -> None:
    """The bundled copy is generated from packages/contracts — drift fails here (monorepo only)."""
    root = Path(__file__).resolve().parents[3]
    sync = root / "packages/nexi-pack/scripts/sync-schemas.mjs"
    if not (root / "packages/contracts/schemas/v1").is_dir() or not sync.is_file():
        pytest.skip("not in the monorepo")
    r = subprocess.run(["node", str(sync), "--check"], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stdout + r.stderr


def test_platform_verifier_accepts_a_toolkit_signature(pack: Path, tmp_path: Path) -> None:
    """AC-2824: the deployment's verifier and the toolkit agree on the canonical payload."""
    try:
        from nexus_contracts.packs import read_pack as platform_read, signing_payload
        from nexus_security import verify_detached
        from nexus_security.session import public_key_from_b64
    except ImportError:
        pytest.skip("platform packages not importable here")
    key, public = generate_key(tmp_path / "k.key")
    loaded = read_pack(pack)
    signed = sign_manifest(loaded.manifest, load_key(tmp_path / "k.key"), "olena-2026")
    (pack / "manifest.json").write_text(json.dumps(signed, indent=2), encoding="utf-8")
    platform_pack = platform_read(pack)  # digests + every resource parses with the platform's models
    assert verify_detached(public_key_from_b64(public), signing_payload(platform_pack.manifest), platform_pack.manifest.signature.value)
    assert platform_pack.counts()["skills"] == 1 and platform_pack.counts()["agents"] == 1 and platform_pack.counts()["flows"] == 1
