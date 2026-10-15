"""`nexi-pack validate` — digests, schemas, then the references between resources.

Every finding is `Finding(level, path, message)`; `error` findings fail validation, `warning` findings do not. The
order is the deployment's: a pack whose files do not match their digests is refused before any content is read.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources as pkg_resources
from pathlib import PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource as RefResource

from .pack import KINDS_WITH_SCHEMA, SKILL_ENTRY, Pack, PackError, check_digests, read_pack

AGENT_REF = re.compile(r"nexus://agent/[a-z0-9_]+")
SKILL_REF = re.compile(r"nexus://skill/[a-z0-9_]+")
SCHEMA_BASE = "https://schemas.nexiflow.ai/v1/"


@dataclass(frozen=True)
class Finding:
    level: str  # "error" | "warning"
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.level}: {self.path}: {self.message}"


@lru_cache(maxsize=1)
def _registry() -> Registry:
    registry = Registry()
    for entry in pkg_resources.files("nexi_pack.schemas").iterdir():
        if entry.name.endswith(".schema.json"):
            doc = json.loads(entry.read_text(encoding="utf-8"))
            resource = RefResource.from_contents(doc)
            registry = registry.with_resource(doc.get("$id", SCHEMA_BASE + entry.name), resource)
            # the schemas reference each other by bare file name; register that spelling too
            registry = registry.with_resource(entry.name, resource)
    return registry


@lru_cache(maxsize=None)
def validator_for(schema_file: str) -> Draft202012Validator:
    doc = json.loads(pkg_resources.files("nexi_pack.schemas").joinpath(schema_file).read_text(encoding="utf-8"))
    return Draft202012Validator(doc, registry=_registry())


def schema_errors(schema_file: str, document: Any) -> list[str]:
    """Human-readable schema violations, most specific first — the field path and what is wrong."""
    out = []
    for err in sorted(validator_for(schema_file).iter_errors(document), key=lambda e: (len(e.path), str(e.path))):
        where = "/".join(str(p) for p in err.absolute_path) or "(root)"
        msg = err.message
        if len(msg) > 220:
            msg = msg[:217] + "…"
        out.append(f"{where}: {msg}")
    return out


def validate_pack(root: str, *, digests: bool = True, strict_refs: bool = False) -> tuple[Pack | None, list[Finding]]:
    """Validate a pack directory. Returns the pack (when the manifest could be read) and every finding."""
    findings: list[Finding] = []
    try:
        pack = read_pack(root)
    except PackError as exc:
        return None, [Finding("error", "manifest.json", f"{exc.code}: {exc.detail}")]

    # 1. the manifest against its schema (a stale or missing signature is reported, not fatal to the rest)
    manifest_for_schema = dict(pack.manifest)
    unsigned = not manifest_for_schema.get("signature")
    if unsigned:
        manifest_for_schema["signature"] = {"alg": "ed25519", "key_id": "unsigned", "value": "unsigned"}
        findings.append(Finding("warning", "manifest.json", "unsigned — run `nexi-pack sign` before you ship it"))
    for msg in schema_errors("nexus-pack-manifest.schema.json", manifest_for_schema):
        findings.append(Finding("error", "manifest.json", msg))
    expected_uri = f"nexus://core/pack/{pack.name}"

    # 2. digests — one mismatch and a deployment refuses the whole pack
    if digests:
        try:
            for path in check_digests(pack):
                findings.append(Finding("error", path, "digest does not match the file — run `nexi-pack digest --write`"))
        except PackError as exc:
            findings.append(Finding("error", exc.detail, exc.code))
            return pack, findings

    # 3. every resource against its schema; collect what the pack declares
    skills: dict[str, dict[str, Any]] = {}
    agents: dict[str, dict[str, Any]] = {}
    flows: dict[str, dict[str, Any]] = {}
    patterns: list[tuple[str, dict[str, Any]]] = []
    blueprints: list[tuple[str, dict[str, Any]]] = []
    listed = {r.path for r in pack.resources}
    for r in pack.resources:
        if not pack.file(r.path).is_file():
            findings.append(Finding("error", r.path, "listed in the manifest but missing"))
            continue
        if r.kind == "prompt":
            continue
        if not r.path.endswith(".json"):
            if r.kind in KINDS_WITH_SCHEMA:
                findings.append(Finding("error", r.path, f"a {r.kind} resource is a JSON file"))
            continue
        try:
            doc = pack.read_json(r.path)
        except PackError as exc:
            findings.append(Finding("error", r.path, exc.detail))
            continue
        if r.kind == "policy":
            if not isinstance(doc.get("kind"), str) or not doc["kind"]:
                findings.append(Finding("error", r.path, "a policy document names its `kind`"))
            continue
        schema_file = KINDS_WITH_SCHEMA.get(r.kind)
        if schema_file is None:
            continue  # ontology · schema · evaluation · tool_* · ui_config · migration — digest-verified, not interpreted
        body = dict(doc)
        if r.kind == "skill":
            entry = str(PurePosixPath(r.path).parent / SKILL_ENTRY)
            if entry not in listed:
                findings.append(Finding("error", r.path, f"no `{entry}` listed as a prompt resource next to the skill"))
            elif not body.get("instructions"):
                body["instructions"] = pack.file(entry).read_text(encoding="utf-8")
        if r.kind == "agent":
            entry = r.path[: -len(".json")] + ".md"
            if entry not in listed:
                findings.append(Finding("warning", r.path, f"no `{entry}` prompt next to the agent — it will work from `instructions` only"))
            elif not body.get("instructions"):
                body["instructions"] = pack.file(entry).read_text(encoding="utf-8")
        for msg in schema_errors(schema_file, body):
            findings.append(Finding("error", r.path, msg))
        declared_uri = doc.get("uri") if isinstance(doc.get("uri"), str) else None
        if r.uri and declared_uri and r.uri != declared_uri:
            findings.append(Finding("error", r.path, f"manifest uri {r.uri} != file uri {declared_uri}"))
        if r.kind == "skill":
            skills[declared_uri or r.path] = doc
            # a skill is an instruction + evaluation package: both schemas, examples — only the platform's own
            # mechanics (`/flow`, `/pin`) are exempt from the schemas
            for field_name in ("input_schema", "output_schema"):
                if not doc.get(field_name):
                    level = "warning" if doc.get("origin") == "platform" else "error"
                    findings.append(Finding(level, r.path, f"`{field_name}` is missing — a skill declares what it reads and what it produces"))
            if not doc.get("examples"):
                findings.append(Finding("warning", r.path, "no `examples` — a reviewer reads the examples first"))
            review = (doc.get("evaluation") or {}).get("human_review") or {}
            if review.get("state") != "approved":
                findings.append(Finding("warning", r.path, f"human_review is {review.get('state', 'missing')!r} — a deployment teaches nobody an unreviewed skill"))
            elif review.get("reviewed_version") not in (None, doc.get("version")):
                findings.append(Finding("warning", r.path, f"reviewed_version {review.get('reviewed_version')} != version {doc.get('version')} — review the current version"))
        elif r.kind == "agent":
            agents[declared_uri or r.path] = doc
        elif r.kind == "flow_template":
            flows[declared_uri or r.path] = doc
            if doc.get("project_id") is not None or not (doc.get("template") or {}).get("is_template"):
                findings.append(Finding("error", r.path, "a pack ships templates: `project_id` null and `template.is_template` true"))
        elif r.kind == "pattern":
            patterns.append((r.path, doc))
        elif r.kind == "blueprint":
            blueprints.append((r.path, doc))

    # 4. references between resources
    if len(blueprints) != 1:
        findings.append(Finding("error", "manifest.json", f"a pack ships exactly one blueprint resource ({len(blueprints)} found)"))
    for path, bp in blueprints:
        if bp.get("source_pack_uri") not in (None, expected_uri):
            findings.append(Finding("error", path, f"source_pack_uri {bp.get('source_pack_uri')} != {expected_uri}"))
        defaults = bp.get("defaults") or {}
        for uri in defaults.get("agents") or []:
            if uri not in agents:
                findings.append(Finding("warning" if not strict_refs else "error", path, f"defaults.agents names {uri}, which this pack does not ship"))
        for uri in defaults.get("skills") or []:
            if uri not in skills:
                findings.append(Finding("warning" if not strict_refs else "error", path, f"defaults.skills names {uri}, which this pack does not ship"))
        for role, uri in (defaults.get("flows") or {}).items():
            if uri not in flows:
                findings.append(Finding("warning" if not strict_refs else "error", path, f"defaults.flows.{role} names {uri}, which this pack does not ship"))
    ref_level = "error" if strict_refs else "warning"
    for uri, agent in agents.items():
        for s in agent.get("skill_refs") or []:
            if s not in skills:
                findings.append(Finding(ref_level, _path_of(pack, "agent", uri), f"applies {s}, which this pack does not ship (a pack it depends on must)"))
    for uri, flow in flows.items():
        text = json.dumps(flow)
        for a in sorted(set(AGENT_REF.findall(text))):
            if a not in agents:
                findings.append(Finding(ref_level, _path_of(pack, "flow_template", uri), f"names {a}, which this pack does not ship"))
        for s in sorted(set(SKILL_REF.findall(text))):
            if s not in skills:
                findings.append(Finding(ref_level, _path_of(pack, "flow_template", uri), f"names {s}, which this pack does not ship"))
    for path, pattern in patterns:
        tpl = (pattern.get("template") or {}).get("workflow_uri")
        flow = flows.get(tpl)
        if flow is None:
            findings.append(Finding("error", path, f"its template {tpl} is not shipped by this pack"))
            continue
        shipped = (flow.get("template") or {}).get("source_template_version")
        if shipped != (pattern.get("template") or {}).get("version"):
            findings.append(Finding("error", path, f"template ships {shipped}, pattern says {(pattern.get('template') or {}).get('version')}"))
        used = sorted({n.get("kind") for n in flow.get("nodes", [])} - {"trigger", "end"})
        declared = sorted((pattern.get("requires") or {}).get("node_types") or [])
        if used != declared:
            findings.append(Finding("error", path, f"requires.node_types {declared} != the template's node kinds {used}"))
    return pack, findings


def _path_of(pack: Pack, kind: str, uri: str) -> str:
    for r in pack.resources:
        if r.kind == kind and r.uri == uri:
            return r.path
    return uri
