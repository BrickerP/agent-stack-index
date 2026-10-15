"""Human-readable release report (Markdown), generated from results.json data only."""
from __future__ import annotations

from .config import Workspace


def name(ws: Workspace, vendor: str | None, category: str) -> str:
    if not vendor:
        return "—"
    if vendor == "_other":
        return "other (not in catalog)"
    if vendor == "_none":
        return "none / no answer"
    v = ws.vendors.get(vendor)
    return v.product(category) if v else vendor


def pct(x) -> str:
    return f"{round(100 * float(x or 0))}%"


LAB_VENDOR = {"Anthropic": "anthropic", "OpenAI": "openai", "Google": "google"}


def window(man: dict) -> str:
    w = man.get("data_window") or []
    return w[0] if len(w) == 2 and w[0] == w[1] else " to ".join(w)


def headline(ws: Workspace, result: dict) -> list:
    base = result.get("baseline") or {}
    duel = result.get("duel") or {}
    man = result["manifest"]
    total = len(base)
    strong = [c for c, r in base.items() if r["models_total"] and r["models_agree"] >= 0.8 * r["models_total"]]
    unanimous = [c for c, r in base.items() if r["models_agree"] == r["models_total"] and r["top_share"] >= 0.95]
    lines = [f"- **{len(strong)} of {total} categories** have a default that at least 80% of models share; "
             f"in {len(unanimous)} of them every model picks the same tool and it takes at least 95% of all answers."]
    ranked = sorted(base.items(), key=lambda kv: (-kv[1]["top_share"], kv[0]))[:6]
    lines.append("- Unanimous defaults include " + ", ".join(
        f"{name(ws, r['top'], c)} ({r['label']})" for c, r in ranked) + ".")
    if duel:
        solo = [(r["solo_win"][v], v, c) for c, r in duel.items() for v in r["vendors"]]
        never = [(v, c) for c, r in duel.items() for v in r["vendors"] if r["arms"].get("none", {}).get(v, 0) <= 0.01 and r["solo_win"][v] >= 0.5]
        low, high = min(s for s, _v, _c in solo), max(s for s, _v, _c in solo)
        lines.append(f"- **Whatever the model reads decides the pick.** With only one candidate's notes in context, models pick that candidate "
                     f"{pct(low)}–{pct(high)} of the time" + (", including tools they never pick unprompted (" + ", ".join(
                         f"{name(ws, v, c)} 0% → {pct(duel[c]['solo_win'][v])}" for v, c in never[:3]) + ")" if never else "") + ".")
        flips = sorted(((r["lift"][v], v, c) for c, r in duel.items() for v in r["vendors"]), reverse=True)
        lift, v, c = flips[0]
        if lift >= 0.1:
            lines.append(f"- With all candidates' notes side by side, most defaults hold, but {duel[c]['label']} moves: "
                         f"{name(ws, v, c)} goes from {pct(duel[c]['arms'].get('none', {}).get(v))} to {pct(duel[c]['arms'].get('trio', {}).get(v))}.")
    provider = base.get("llm_provider")
    if provider:
        own = []
        for mid, m in provider["models"].items():
            lab = man["models"].get(mid, {}).get("lab")
            if lab in LAB_VENDOR and m["n"]:
                own.append(f"{man['models'][mid]['label']} names {lab} {pct(m['counts'].get(LAB_VENDOR[lab], 0) / m['n'])}")
        if own:
            lines.append(f"- Asked for an LLM provider, the pooled pick is {name(ws, provider['top'], 'llm_provider')}; by lab: " + "; ".join(own) + ".")
    lines.append(f"- {man['answers']:,} answers from {len(man['models'])} models, collected {window(man)}.")
    return lines


def markdown(ws: Workspace, result: dict) -> str:
    man = result["manifest"]
    base = result.get("baseline") or {}
    duel = result.get("duel") or {}
    out = [f"# {man['title']}", "",
           "Which libraries and hosted services AI coding models pick when they start a project from scratch, "
           "and how much the pick moves when vendor documentation is in context.", "",
           "## Headline", "", *headline(ws, result), ""]
    out += ["## The default stack", "", "| Category | Top pick | Pooled share | Models agreeing | Runner-up |", "|---|---|---|---|---|"]
    for cat, r in base.items():
        named = [(k, v) for k, v in r["pooled"].items() if not k.startswith("_")]
        runner = f"{name(ws, named[1][0], cat)} ({pct(named[1][1])})" if len(named) > 1 else "—"
        out.append(f"| {r['label']} | {name(ws, r['top'], cat)} | {pct(r['top_share'])} | {r['models_agree']}/{r['models_total']} | {runner} |")
    models = list(man["models"])
    if base and models:
        out += ["", "## Top pick by model", "", "| Category | " + " | ".join(man["models"][m]["label"] for m in models) + " |",
                "|---|" + "---|" * len(models)]
        for cat, r in base.items():
            cells = []
            for m in models:
                mm = r["models"].get(m)
                cells.append(f"{name(ws, mm['top'], cat)} {pct(mm['top_share'])}" if mm and mm["top"] else "—")
            out.append(f"| {r['label']} | " + " | ".join(cells) + " |")
    if duel:
        out += ["", "## Context duels", "",
                "Same single-item task, three arms: no notes, all candidates' notes (order rotated), each candidate's notes alone.", "",
                "| Category | Candidate | No notes | All notes | Its notes alone |", "|---|---|---|---|---|"]
        for cat, r in duel.items():
            for v in r["vendors"]:
                out.append(f"| {r['label']} | {name(ws, v, cat)} | {pct(r['arms'].get('none', {}).get(v))} | "
                           f"{pct(r['arms'].get('trio', {}).get(v))} | {pct(r['solo_win'][v])} |")
        rates = [r["first_position_rate"] for r in duel.values() if r["first_position_rate"] is not None]
        if rates:
            out += ["", f"Listed-first candidate won {pct(sum(rates) / len(rates))} of all-notes picks (one third would be no position effect)."]
    out += ["", "## Coverage", "", "| Experiment | Planned | Observed | Coverage |", "|---|---|---|---|"]
    for e in man["experiments"].values():
        out.append(f"| {e['id']} | {e['planned']} | {e['observed']} | {pct(e['coverage'])} |")
    out += ["", f"Answers not matched to the catalog: {pct(man['unmatched_rate'])} of items. Catalog `{man['catalog_sha']}`, harness {man['harness']}.",
            "", "## Models", "", "| Model | Lab | Answers | Reported as | Notes |", "|---|---|---|---|---|"]
    for mid, m in man["models"].items():
        out.append(f"| {m['label']} | {m['lab']} | {m['answers']} | {', '.join(m['reported']) or '—'} | {m['notes'] or ''} |")
    out += ["", "Method and limitations: see [docs/METHODOLOGY.md](../../docs/METHODOLOGY.md).", ""]
    return "\n".join(out)
