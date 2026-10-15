"""Vendor-facing audit: where one vendor stands in a release, and a re-test plan for engagements.

This is the commercial engine on top of the public data. Client-specific runs and reports belong in
a private repository; this module only reads public releases and writes experiment specs.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import Workspace
from .release import latest_release, release_dir
from .report import name, pct

CHECKLIST = [
    "Agent-readable docs: an llms.txt index plus Markdown versions of the quickstart, pricing and API reference.",
    "Be retrievable where agents look: a Context7 listing, an MCP server for setup tasks, docs that fetch cleanly without JavaScript.",
    "A copy-paste quickstart for the stacks agents actually build (Next.js + TypeScript, FastAPI) with current package names.",
    "Honest comparison pages for the default pick in your category, so retrieval finds your side of the trade-off.",
    "Public example repos and templates that agents imitate when they scaffold.",
]


def snapshot(ws: Workspace, vendor_id: str, release_id: str | None = None) -> str:
    vendor = ws.vendors[vendor_id]
    release_id = release_id or latest_release(ws)
    result = json.loads((release_dir(ws, release_id) / "results.json").read_text(encoding="utf-8"))
    base, duel = result.get("baseline") or {}, result.get("duel") or {}
    out = [f"# Agent-readiness snapshot: {vendor.name}", "",
           f"From public Agent Stack Index release {release_id}. Shares are of each model's picks, models weighted equally.", ""]
    measured = [c for c in vendor.categories if c in base]
    if not measured:
        out.append("This vendor's categories are not measured in this release; run a custom audit (`asi audit --plan`).")
    for cat in measured:
        r = base[cat]
        named = [k for k in r["pooled"] if not k.startswith("_")]
        rank = named.index(vendor_id) + 1 if vendor_id in named else None
        tops = sum(1 for m in r["models"].values() if m["top"] == vendor_id)
        out += [f"## {r['label']}", "",
                f"- Your pooled share: **{pct(r['pooled'].get(vendor_id, 0))}**" + (f" (rank {rank} of {len(named)} named tools)." if rank else " (never picked)."),
                f"- Default in this category: {name(ws, r['top'], cat)} at {pct(r['top_share'])}; {r['models_agree']}/{r['models_total']} models agree.",
                f"- Models that pick you first: {tops}/{r['models_total']}.", "",
                "| Model | Your share | Their top pick |", "|---|---|---|"]
        for model_id, m in r["models"].items():
            share = (m["counts"].get(vendor_id, 0) / m["n"]) if m["n"] else 0
            label = result["manifest"]["models"].get(model_id, {}).get("label", model_id)
            out.append(f"| {label} | {pct(share)} | {name(ws, m['top'], cat)} |")
        out.append("")
        if cat in duel and vendor_id in duel[cat]["vendors"]:
            d = duel[cat]
            out += ["When your notes are in context:", "",
                    f"- no notes {pct(d['arms'].get('none', {}).get(vendor_id))} → all candidates' notes {pct(d['arms'].get('trio', {}).get(vendor_id))} → "
                    f"your notes alone **{pct(d['solo_win'][vendor_id])}**.", ""]
    out += ["## What usually moves this", ""] + [f"{i}. {item}" for i, item in enumerate(CHECKLIST, 1)]
    out += ["", "## Re-test plan", "",
            "Run the same tasks before and after changes, against the category default and runner-up, with notes in and out of context.",
            f"`asi audit --vendor {vendor_id} --plan` writes the experiment spec.", ""]
    return "\n".join(out)


def plan_spec(ws: Workspace, vendor_id: str, release_id: str | None = None, tag: str = "baseline", out: Path | None = None) -> Path:
    """Write an audit duel spec against the measured default and runner-up.

    Client audits should pass `out` pointing into a private workspace, together with its contexts."""
    vendor = ws.vendors[vendor_id]
    release_id = release_id or latest_release(ws)
    result = json.loads((release_dir(ws, release_id) / "results.json").read_text(encoding="utf-8"))
    base = result.get("baseline") or {}
    lines = [f'id = "audit-{vendor_id}-{tag}"', 'probe = "duel"', f'title = "Audit {vendor.name} ({tag})"',
             'models = ["*"]', 'variants = ["notes"]', "", "[arms]", "none = 4", "trio = 6", "solo = 4", ""]
    for cat in vendor.categories:
        if cat not in base:
            continue
        task = next((t for t in ws.tasks.values() if t.items == (cat,)), None) or next(t for t in ws.tasks.values() if cat in t.items)
        rivals = [k for k in base[cat]["pooled"] if not k.startswith("_") and k != vendor_id][:2]
        lines += ["[[duel]]", f'task = "{task.id}"', f'category = "{cat}"', f"vendors = {json.dumps([vendor_id, *rivals])}", ""]
    path = out or ws.root / "experiments" / f"audit-{vendor_id}-{tag}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
