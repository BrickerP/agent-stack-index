"""Markdown release report, in the same order as the web report: three findings, then evidence."""
from __future__ import annotations

from .config import Workspace
from .narrative import (TITLE, dek, finding_tags, findings, harness_note, limits, name, names, pct, question, section_contested,
                        section_default, section_duel, section_meaning, section_pilot, status_line)

__all__ = ["markdown", "name", "pct"]

TIER_TITLES = {
    "default": "Settled — every model, at least 95% of answers",
    "leaning": "Leaning — at least 8 of 10 models agree",
    "contested": "Contested",
}


def mark(man: dict, model_id: str) -> str:
    m = man["models"][model_id]
    return m["label"] + ("†" if m.get("injected_prompt") else "")


def runner_up(ws: Workspace, row: dict, cat: str) -> str:
    named = [(k, v) for k, v in row["pooled"].items() if not k.startswith("_")]
    return f"{name(ws, named[1][0], cat)} {pct(named[1][1])}" if len(named) > 1 else "—"


def markdown(ws: Workspace, result: dict) -> str:
    man, st = result["manifest"], result["story"]
    base, duel = result.get("baseline") or {}, result.get("duel") or {}
    models = list(man["models"])
    out = [f"# {TITLE}", "", f"*{man['title']}*", "", dek(result), ""]
    status, q = status_line(result), question(result)
    out += ([status, ""] if status else []) + ([f"**Question.** {q}", ""] if q else [])
    out += [f"{i}. {text} *({tag})*" for i, (text, tag) in enumerate(zip(findings(ws, result), finding_tags(result)), 1)] + [""]

    out += ["## 1. Most categories already have a default", "", section_default(ws, result), ""]
    for tier, cats in st["tiers"].items():
        if not cats:
            continue
        out += [f"**{TIER_TITLES[tier]}** ({len(cats)})", "", "| Category | Pick | Share | Models agreeing | Runner-up |", "|---|---|---|---|---|"]
        out += [f"| {base[c]['label']} | {name(ws, base[c]['top'], c)} | {pct(base[c]['top_share'])} | "
                f"{base[c]['models_agree']}/{base[c]['models_total']} | {runner_up(ws, base[c], c)} |" for c in cats]
        out.append("")

    contested = st["tiers"]["contested"]
    if contested:
        out += ["## 2. Without a default, the pick moves with the model and the wording", ""]
        out += [p + "\n" for p in section_contested(ws, result)]
        out += ["| Category | Top pick of how many models | Same pick when reworded |", "|---|---|---|"]
        for c in contested:
            split = " · ".join(f"{name(ws, v, c)} ×{n}" for v, n in st["splits"][c])
            out.append(f"| {base[c]['label']} | {split} | {base[c]['variant_consistent']}/{base[c]['models_total']} |")
        out += ["", "A model tied between two tools counts for both. Per-model picks are in the appendix.", ""]

    if duel:
        out += ["## 3. What the model reads can decide the pick", ""]
        out += [p + "\n" for p in section_duel(ws, result)]
        out += ["| Category | Candidate | No notes | All three candidates' notes | Its notes alone |", "|---|---|---|---|---|"]
        for c, row in duel.items():
            for v in row["vendors"]:
                out.append(f"| {row['label']} | {name(ws, v, c)} | {pct(row['arms'].get('none', {}).get(v))} | "
                           f"{pct(row['arms'].get('trio', {}).get(v))} | {pct(row['solo_win'][v])} |")
        out.append("")

    out += ["## What this means", ""] + [f"- {p}" for p in section_meaning(ws, result)] + [""]

    if st.get("pilot"):
        p = st["pilot"]
        out += ["## Early check: asked vs done", ""] + [x + "\n" for x in section_pilot(ws, result)]
        out += [f"| Need | Asked ({mark(man, p['model_id'])}, API) | Written by Claude Code ({p['runs']} runs) |", "|---|---|---|"]
        for i in p["items"]:
            out.append(f"| {base[i['item']]['label']} | {name(ws, i['asked'], i['item'])} {i['asked_n']}/{i['asked_total']} | "
                       f"{name(ws, i['done'], i['item'])} {i['done_n']}/{i['runs']} |")
        out += ["", f"Raw results: [`{p['file']}`](../../{p['file']}).", ""]

    out += ["## Limits", ""] + [f"- {x}" for x in limits(ws, result)] + [""]

    proto = man.get("protocol") or {}
    note = f" Protocol: [{proto['path']}](../../{proto['path']}) ({proto['status']})." if proto else ""
    harness = f" Harness this round: {harness_note(result)}" if harness_note(result) else ""
    out += ["## Data and method", "",
            "Raw answers, the vendor catalog and the code are open; every number here is regenerated from them in CI. "
            f"Method: [docs/METHODOLOGY.md](../../docs/METHODOLOGY.md).{note}{harness}", "",
            "| Experiment | Planned | Observed | Coverage |", "|---|---|---|---|"]
    out += [f"| {e['id']} | {e['planned']} | {e['observed']} | {pct(e['coverage'])} |" for e in man["experiments"].values()]
    out += ["", f"Answers not matched to the catalog: {pct(man['unmatched_rate'])} of items. Catalog `{man['catalog_sha']}`, harness {man['harness']}.",
            "", "| Model | Lab | Answers | Reported as |", "|---|---|---|---|"]
    out += [f"| {mark(man, mid)} | {m['lab']} | {m['answers']} | {', '.join(m['reported']) or '—'} |" for mid, m in man["models"].items()]

    out += ["", "## Appendix: top pick by model, all categories", "",
            "Ties are shown as A / B. † route adds its own system prompt.", "",
            "| Category | " + " | ".join(mark(man, m) for m in models) + " |", "|---|" + "---|" * len(models)]
    for c, row in base.items():
        cells = []
        for m in models:
            mm = row["models"].get(m)
            cells.append(f"{names(ws, mm['tops'], c)} {pct(mm['top_share'])}" if mm and mm["tops"] else "—")
        out.append(f"| {row['label']} | " + " | ".join(cells) + " |")
    out.append("")
    return "\n".join(out)
