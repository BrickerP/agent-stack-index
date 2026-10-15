"""Cut a release: restrict observations to the current plan, analyze, and write derived artifacts.

Releases are derived, never hand-edited. `--check` regenerates in memory and fails on any drift,
so a catalog change shows up as a reviewable diff in every affected release.
"""
from __future__ import annotations

import csv
import io
import json
import tomllib
from pathlib import Path

from . import __version__, store
from .analyze import baseline, duel
from .config import Workspace, load_experiment
from .normalize import Matcher, unmatched
from .plan import plan


def release_dir(ws: Workspace, release_id: str) -> Path:
    return ws.root / "releases" / release_id


def spec(ws: Workspace, release_id: str) -> dict:
    with (release_dir(ws, release_id) / "release.toml").open("rb") as handle:
        return tomllib.load(handle)


def _records(ws: Workspace, exp):
    planned = {t.trial_id for t in plan(ws, exp)}
    latest = store.latest_ok(store.read(ws.root, {exp.id}))
    kept = [r for tid, r in latest.items() if tid in planned]
    return kept, len(planned)


def build(ws: Workspace, release_id: str) -> dict:
    s = spec(ws, release_id)
    matcher = Matcher(ws)
    exps, data, records_all = {}, {}, []
    for role in ("baseline", "duel"):
        if not s.get(role):
            continue
        exp = load_experiment(ws.root / "experiments" / f"{s[role]}.toml")
        records, planned = _records(ws, exp)
        records_all += records
        exps[role] = {"id": exp.id, "title": exp.title, "planned": planned, "observed": len(records),
                      "coverage": round(len(records) / planned, 4) if planned else 0.0}
        data[role] = baseline(ws, records, matcher) if role == "baseline" else duel(ws, records, exp.duels, matcher)
    models = {}
    for rec in records_all:
        m = models.setdefault(rec["model_id"], {"reported": set(), "answers": 0})
        m["reported"].add(rec.get("reported_model") or "")
        m["answers"] += 1
    stamps = sorted(r["ts"] for r in records_all)
    misses = unmatched(ws, records_all, limit=60)
    total_items = sum(len(r.get("items", [])) for r in records_all) or 1
    manifest = {
        "release": release_id,
        "title": s.get("title", release_id),
        "harness": __version__,
        "catalog_sha": ws.catalog_sha(),
        "data_window": [stamps[0][:10], stamps[-1][:10]] if stamps else [],
        "experiments": exps,
        "answers": len(records_all),
        "models": {
            mid: {"label": ws.models[mid].label, "lab": ws.models[mid].lab, "route": ws.models[mid].route,
                  "reported": sorted(x for x in v["reported"] if x), "answers": v["answers"], "notes": ws.models[mid].notes}
            for mid, v in sorted(models.items())
        },
        "unmatched_rate": round(sum(n for (_c, _r, how, _v), n in misses if how == "unmatched") / total_items, 4),
        "unmatched_top": [{"category": c, "raw": r, "how": how, "count": n} for (c, r, how, _v), n in misses[:30]],
    }
    return {"manifest": manifest, **data}


def to_csv(result: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["experiment", "category", "arm", "model", "vendor", "count", "share"])
    for cat, row in (result.get("baseline") or {}).items():
        for model_id, m in row["models"].items():
            for vendor, count in m["counts"].items():
                w.writerow(["baseline", cat, "", model_id, vendor, count, round(count / m["n"], 4) if m["n"] else 0])
        for vendor, share in row["pooled"].items():
            w.writerow(["baseline", cat, "", "_pooled", vendor, "", share])
    for cat, row in (result.get("duel") or {}).items():
        for arm, table in row["arms"].items():
            for vendor, share in table.items():
                w.writerow(["duel", cat, arm, "_pooled", vendor, "", share])
    return buf.getvalue()


def artifacts(ws: Workspace, release_id: str) -> dict:
    from .report import markdown

    result = build(ws, release_id)
    return {
        "results.json": json.dumps(result, indent=1, ensure_ascii=False, sort_keys=False) + "\n",
        "picks.csv": to_csv(result),
        "REPORT.md": markdown(ws, result),
    }


def write(ws: Workspace, release_id: str, check: bool = False) -> list:
    out_dir = release_dir(ws, release_id)
    drift = []
    for name, content in artifacts(ws, release_id).items():
        path = out_dir / name
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(name)
        else:
            path.write_text(content, encoding="utf-8")
    return drift


def latest_release(ws: Workspace) -> str:
    ids = sorted(p.parent.name for p in (ws.root / "releases").glob("*/release.toml"))
    if not ids:
        raise SystemExit("no releases yet")
    return ids[-1]
