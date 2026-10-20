"""Experiment protocols: one Markdown file per release, written before the data is collected.

A protocol has header lines (Status, Rung) and fixed sections. For a confirmatory protocol, `asi lock <release>` records a hash of
the pre-registered text (everything above "## Deviations"), the experiment specs and release.toml (which holds the analysis
parameters). `asi validate` then fails if any of them changes, or if an observation is older than the lock.
"""
from __future__ import annotations

import hashlib
import re
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from .config import Analysis, Workspace

STATUSES = ("pilot", "confirmatory")
RUNGS = ("describe", "explain", "behave", "intervene", "track")
SECTIONS = ("Direction", "Goal", "Hypotheses", "Design", "Controls", "Sample size", "Analysis", "Validity checks",
            "Engineering benefit", "Report", "Deviations")


def _toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def release_spec(ws: Workspace, release_id: str) -> dict:
    return _toml(ws.root / "releases" / release_id / "release.toml")


def parse(text: str) -> tuple:
    """(header, sections): header lines above the first section, then the body of every `## name` section."""
    head, sections, current = {}, {}, None
    for line in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            current = m.group(1)
            sections[current] = []
        elif current is None:
            k = re.match(r"^(Status|Rung|Written)\s*:\s*(.+?)\s*$", line)
            if k:
                head[k.group(1).lower()] = k.group(2)
        else:
            sections[current].append(line)
    return head, {name: "\n".join(lines).strip() for name, lines in sections.items()}


def first_paragraph(body: str) -> str:
    return re.sub(r"\s+", " ", (body or "").strip().split("\n\n")[0]).strip()


def labelled(body: str) -> dict:
    """`Label: text` paragraphs of a section as {label: text}."""
    out = {}
    for para in re.split(r"\n\s*\n", (body or "").strip()):
        m = re.match(r"^([A-Za-z][A-Za-z ]{0,30}):\s*(.+)$", para.strip(), re.S)
        if m:
            out[m.group(1).strip().lower()] = re.sub(r"\s+", " ", m.group(2)).strip()
    return out


def pre_registered(text: str) -> str:
    """The part of a protocol that gets locked: everything above the Deviations section."""
    return re.split(r"^## Deviations\s*$", text, maxsplit=1, flags=re.M)[0]


def load(ws: Workspace, release_id: str) -> dict | None:
    rel = release_spec(ws, release_id).get("protocol")
    path = ws.root / rel if rel else None
    if not path or not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    head, sections = parse(text)
    return {"path": rel, "text": text, "head": head, "sections": sections}


def _locked_files(ws: Workspace, release_id: str) -> list:
    spec = release_spec(ws, release_id)
    files = [ws.root / "releases" / release_id / "release.toml"]
    return files + [ws.root / "experiments" / f"{spec[role]}.toml" for role in ("baseline", "duel") if spec.get(role)]


def fingerprint(ws: Workspace, release_id: str) -> str:
    digest = hashlib.sha256(pre_registered(load(ws, release_id)["text"]).encode("utf-8"))
    for path in _locked_files(ws, release_id):
        digest.update(path.relative_to(ws.root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def lock_path(ws: Workspace, release_id: str) -> Path:
    return (ws.root / release_spec(ws, release_id)["protocol"]).with_suffix(".lock")


def read_lock(ws: Workspace, release_id: str) -> dict | None:
    path = lock_path(ws, release_id)
    return _toml(path) if path.exists() else None


def structure_problems(ws: Workspace, release_id: str) -> list:
    tag = f"release {release_id}"
    spec = release_spec(ws, release_id)
    if not spec.get("protocol"):
        return [f'{tag}: release.toml needs `protocol = "protocols/<id>.md"`']
    proto = load(ws, release_id)
    if proto is None:
        return [f"{tag}: protocol {spec['protocol']} not found"]
    out, head, sections = [], proto["head"], proto["sections"]
    if head.get("status") not in STATUSES:
        out.append(f"{tag}: protocol needs `Status: pilot` or `Status: confirmatory`")
    if head.get("rung") not in RUNGS:
        out.append(f"{tag}: protocol needs `Rung:` one of {', '.join(RUNGS)}")
    for name in SECTIONS:
        body = sections.get(name)
        if body is None:
            out.append(f"{tag}: protocol section '## {name}' is missing")
        elif name != "Deviations" and (not body or "TODO" in body):
            out.append(f"{tag}: protocol section '{name}' is empty or still has a TODO")
    if "analysis" not in spec:
        out.append(f"{tag}: release.toml needs an [analysis] table")
    else:
        try:
            Analysis(**spec["analysis"])
        except TypeError as err:
            out.append(f"{tag}: [analysis] {err}")
    return out


def _observations(ws: Workspace, release_id: str) -> list:
    from . import store

    spec = release_spec(ws, release_id)
    ids = {spec[role] for role in ("baseline", "duel") if spec.get(role)}
    return list(store.read(ws.root, ids)) if ids else []


def lock_problems(ws: Workspace, release_id: str) -> list:
    proto = load(ws, release_id)
    if not proto or proto["head"].get("status") != "confirmatory":
        return []
    tag = f"release {release_id}"
    lk = read_lock(ws, release_id)
    if lk is None:
        return [f"{tag}: confirmatory protocol is not locked; run `asi lock {release_id}` before collecting data"]
    if lk.get("sha") != fingerprint(ws, release_id):
        return [f"{tag}: protocol, experiment specs or [analysis] changed after the lock; record the change under "
                f"'## Deviations' (allowed) or, before any data exists, lock again"]
    early = [r for r in _observations(ws, release_id) if r.get("ts", "") < lk["locked_at"]]
    return [f"{tag}: {len(early)} observations are older than the lock ({lk['locked_at']})"] if early else []


def problems(ws: Workspace, release_id: str) -> list:
    return structure_problems(ws, release_id) or lock_problems(ws, release_id)


def lock(ws: Workspace, release_id: str) -> Path:
    bad = structure_problems(ws, release_id)
    if bad:
        raise SystemExit("cannot lock:\n  " + "\n  ".join(bad))
    if load(ws, release_id)["head"]["status"] != "confirmatory":
        raise SystemExit("only a confirmatory protocol is locked")
    if _observations(ws, release_id):
        raise SystemExit("observations already exist; locking now would not pre-register anything (record changes under '## Deviations')")
    path = lock_path(ws, release_id)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(f'sha = "{fingerprint(ws, release_id)}"\nlocked_at = "{stamp}"\n', encoding="utf-8")
    return path


def release_of(ws: Workspace, experiment_id: str) -> str | None:
    for path in sorted((ws.root / "releases").glob("*/release.toml")):
        spec = _toml(path)
        if experiment_id in (spec.get("baseline"), spec.get("duel")):
            return path.parent.name
    return None


def run_gate(ws: Workspace, experiment_id: str) -> str | None:
    """Why this experiment must not run yet (no protocol, unfinished protocol, or not locked), or None."""
    rid = release_of(ws, experiment_id)
    if rid is None:
        return None
    bad = structure_problems(ws, rid)
    if bad:
        return "; ".join(bad)
    if load(ws, rid)["head"]["status"] != "confirmatory":
        return None
    lk = read_lock(ws, rid)
    if lk is None or lk.get("sha") != fingerprint(ws, rid):
        return f"release {rid}: the confirmatory protocol is not locked (or changed since); run `asi lock {rid}`"
    return None


def summary(ws: Workspace, release_id: str) -> dict | None:
    """What the report says about the protocol."""
    proto = load(ws, release_id)
    if proto is None:
        return None
    locked = read_lock(ws, release_id) if proto["head"].get("status") == "confirmatory" else None
    sections = proto["sections"]
    return {"path": proto["path"], "status": proto["head"].get("status"), "rung": proto["head"].get("rung"),
            "goal": first_paragraph(sections.get("Goal", "")), "benefit": labelled(sections.get("Engineering benefit", "")),
            "sha": fingerprint(ws, release_id)[:12], "locked_at": locked["locked_at"] if locked else None}
