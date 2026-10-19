"""Sentences of the report, rendered from the release's `story`. Shared by Markdown, HTML and share images.

Text uses **bold** markers only; renderers convert them. Every number comes from the result dict.
"""
from __future__ import annotations

from .config import Workspace

TITLE = "AI coding models already have a default stack"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
PROPER = {"Python", "Postgres", "LLM", "UI", "ORM"}


def word(n: int, cap: bool = False) -> str:
    """Spell out small counts in prose (twelve, seven); keep digits for larger numbers."""
    w = WORDS[n] if 0 <= n < len(WORDS) else str(n)
    return w[0].upper() + w[1:] if cap else w


def lower(text: str) -> str:
    """Lower-case a category label for use mid-sentence, keeping proper nouns and acronyms."""
    first = text.split(" ", 1)[0]
    if first in PROPER or not first[1:].islower():
        return text
    return text[0].lower() + text[1:]


def pct(x) -> str:
    return f"{round(100 * float(x or 0))}%"


def pts(x) -> int:
    return round(100 * float(x or 0))


def name(ws: Workspace, vendor: str | None, category: str) -> str:
    if not vendor:
        return "—"
    if vendor == "_other":
        return "other (not in catalog)"
    if vendor in ("_none", "_unspecified"):
        return "not specified"
    v = ws.vendors.get(vendor)
    return v.product(category) if v else vendor


def names(ws: Workspace, vendors, category: str) -> str:
    return " / ".join(name(ws, v, category) for v in vendors)


def series(items) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def label(result: dict, cat: str) -> str:
    return (result.get("baseline", {}).get(cat) or result.get("duel", {}).get(cat) or {}).get("label", cat)


def few(n: int, total: int) -> str:
    return "none" if n == 0 else f"{n} of {total}"


def changed(st: dict, tier: str) -> tuple:
    consistent, total = st["stability"].get(tier, [0, 0])
    return total - consistent, total


def dek(result: dict) -> str:
    sc = result["story"]["scale"]
    phrasing = f", in {word(sc['phrasings'])} phrasings, {word(sc['repeats'])} times each" if sc.get("phrasings") else ""
    return (f"We asked {sc['models']} models from {sc['labs']} labs to start the same {sc['tasks']} projects from scratch and name one tool "
            f"for each of {result['story']['counts']['categories']} needs{phrasing} ({sc['baseline_answers']:,} answers). "
            f"Then we put neutral notes on competing tools in front of them {sc['duel_answers']:,} more times.")


def findings(ws: Workspace, result: dict) -> list:
    st = result["story"]
    c = st["counts"]
    cc, ct = changed(st, "contested")
    dc, dt = changed(st, "default")
    out = [
        f"**Most categories already have a default.** In {c['default']} of {c['categories']} categories every model picks the same tool, "
        f"and it takes at least 95% of the answers; in {c['leaning']} more, at least 8 of 10 models agree.",
        f"**Without a default, the pick moves with the model and the wording.** In the {c['contested']} contested categories, "
        f"{cc} of {ct} model–category pairs change their top pick when the request is reworded; in the default categories, {few(dc, dt)} do.",
    ]
    if st["duels"]:
        lo, hi = st["solo_range"]
        n = len(st["duels"])
        if st["flipped"]:
            f = st["flipped"][0]
            no_default = " which has no default," if st["duels"][f]["baseline_tier"] == "contested" else ""
            tail = f"the favourite held in {word(len(st['held']))} of the {word(n)} categories we tested; in {lower(label(result, f))},{no_default} the lead flipped."
        else:
            tail = f"the favourite held in all {word(n)} categories we tested."
        out.append(f"**What the model reads decides the pick, unless the default is strong.** With only one candidate's notes in context, "
                   f"models pick it {pts(lo)}–{pct(hi)} of the time. With all candidates' notes side by side, {tail}")
    return out


def section_default(ws: Workspace, result: dict) -> str:
    c = result["story"]["counts"]
    return (f"{word(c['default'], True)} categories are settled: every model's top pick is the same tool, and it takes at least 95% of the answers. "
            f"{word(c['leaning'], True)} more lean one way: at least 8 of 10 models agree and the tool wins most answers. "
            f"{word(c['contested'], True)} are contested.")


def section_contested(ws: Workspace, result: dict) -> list:
    st = result["story"]
    base = result["baseline"]
    out = []
    f = st.get("feature_split")
    if f:
        split = st["splits"][f]
        parts = [f"{name(ws, v, f)} is the top pick of {n} model{'s' if n != 1 else ''}" if i == 0 else f"{name(ws, v, f)} of {n}"
                 for i, (v, n) in enumerate(split)]
        out.append(f"Where no tool is settled, models split. In {lower(base[f]['label'])}, {series(parts)}.")
    cc, ct = changed(st, "contested")
    lc, lt = changed(st, "leaning")
    dc, dt = changed(st, "default")
    out.append(f"The same model's answer also depends on the wording: in contested categories, {cc} of {ct} model–category pairs change their "
               f"top pick across the three phrasings, against {few(lc, lt)} in leaning and {few(dc, dt)} in default categories.")
    if st["flagged_models"]:
        flagged = series(result["manifest"]["models"][m]["label"] for m in st["flagged_models"])
        out.append(f"The split is not just the {flagged} routes, which add a hidden system prompt (see Limits): in "
                   f"{st['contested_unflagged_disagree']} of {len(st['tiers']['contested'])} contested categories, at least one other model "
                   f"also disagrees with the pooled pick.")
    return out


def section_duel(ws: Workspace, result: dict) -> list:
    st = result["story"]
    d = st["duels"]
    if not d:
        return []
    lo, hi = st["solo_range"]
    ex = [f"{name(ws, v, c)} {pct(none)} → {pct(solo)}" for c, v, none, solo in st["zero_to_solo"][:3]]
    out = [f"In {word(len(d))} duels we gave the same single-need task three ways: no notes; neutral notes on three candidates, in rotated order; "
           f"and one candidate's notes alone. Alone, every candidate won {pts(lo)}–{pct(hi)} of picks"
           + (f", including tools that got 0% with no notes ({', '.join(ex)})." if ex else ".")]
    if st["held"]:
        drops = [pts(d[c]["favourite_none"]) - pts(d[c]["favourite_trio"]) for c in st["held"]]  # as displayed, so readers can check
        a, b = min(drops), max(drops)
        held = [f"{name(ws, d[c]['favourite'], c)} {pct(d[c]['favourite_none'])} → {pct(d[c]['favourite_trio'])}" for c in st["held"]]
        drop = f"{a}–{b} points" if a != b else f"{a} points"
        out.append(f"Side by side, the no-notes favourite stayed on top in {word(len(st['held']))} of {word(len(d))} duels, losing {drop} ({', '.join(held)}).")
    for c in st["flipped"]:
        x = d[c]
        why = ", where models had no default," if x["baseline_tier"] == "contested" else ""
        out.append(f"In {lower(label(result, c))}{why} the lead flipped: {name(ws, x['favourite'], c)} {pct(x['favourite_none'])} → "
                   f"{pct(x['favourite_trio'])}, {name(ws, x['leader_trio'], c)} {pct(x['leader_none'])} → {pct(x['leader_trio_share'])}.")
    if st["first_position_mean"] is not None and st["first_position_top"]:
        top = st["first_position_top"]
        clause = ""
        if len(top) == 2 and all(d[c]["baseline_tier"] != "default" for c, _r in top):
            clause = ", the two duels without a settled default"
        out.append(f"Order mattered a little: the first-listed candidate won {pct(st['first_position_mean'])} of side-by-side picks (a third would "
                   f"mean no effect), most in {series(f'{lower(label(result, c))} ({pct(r)})' for c, r in top)}{clause}.")
    return out


def section_meaning(ws: Workspace, result: dict) -> list:
    st = result["story"]
    most = sorted(st["tiers"]["contested"], key=lambda c: (result["baseline"][c]["top_share"], c))[:5]
    contested = [lower(result["baseline"][c]["label"]) for c in most]
    dev = ("**If you build with agents:** an agent's stack is mostly the model's default plus whatever documentation reaches its context. "
           "If you care which tool you get, name it; in contested categories, rewording the request can change the answer.")
    vendor = "**If you make developer tools:** if you are not the default, the lever is being read."
    if st["duels"]:
        lo, hi = st["solo_range"]
        held = [pts(st["duels"][c]["favourite_none"]) - pts(st["duels"][c]["favourite_trio"])
                for c in st["held"] if st["duels"][c]["baseline_tier"] == "default"]
        moved = f" by at most {max(held)} points" if held else ""
        vendor += (f" Alone in context, every candidate's notes won {pts(lo)}–{pct(hi)} of picks, but next to a strong default they moved it"
                   f"{moved}.")
    vendor += f" The open ground is the contested categories, where models already disagree: for example {series(contested)}."
    return [dev, vendor]


def section_pilot(ws: Workspace, result: dict) -> list:
    p = result["story"].get("pilot")
    if not p:
        return []
    m = result["manifest"]["models"].get(p["model_id"], {})
    out = [f"We ran Claude Code (model route {m.get('route', p['model_id'])}) {word(p['runs'])} times on the SaaS-starter task with file tools only, "
           f"and mapped the dependencies it wrote into package.json to the catalog. {word(p['same'], True)} of {word(p['total'])} rows name the same "
           f"package or service as the same model's direct API answers."]
    diffs = []
    for i in p["items"]:
        if i["same"]:
            continue
        cat = i["item"]
        asked = f"{name(ws, i['asked'], cat)} {i['asked_n']}/{i['asked_total']}"
        if i["done"] == "_unspecified":
            hosts = p.get("database_url_hosts") or []
            where = f" (DATABASE_URL on {', '.join(hosts)})" if cat == "database_host" and hosts else ""
            diffs.append(f"the {lower(label(result, cat))} row stays unspecified in the generated files{where}, where the API answers named {asked}")
        else:
            pkgs = ", ".join(f"`{x}`" for x in i["packages"]) or name(ws, i["done"], cat)
            diffs.append(f"all {word(i['done_n'])} runs wrote {pkgs} for {lower(label(result, cat))}, where the API answers named {asked}")
    if diffs:
        out.append("Differences: " + "; ".join(diffs) + ".")
    out.append("The runs did not install, execute or test anything, and used a different harness and system prompt from the API calls, "
               "so this pilot does not say why the outputs differ or compare library quality.")
    return out


def limits(ws: Workspace, result: dict) -> list:
    man = result["manifest"]
    flagged = [man["models"][m]["label"] for m in result["story"]["flagged_models"]]
    window = man.get("data_window") or []
    when = window[0] if len(window) == 2 and window[0] == window[1] else " to ".join(window)
    out = ["**Stated preference.** Each answer is one API call naming a tool. Apart from the file-only pilot above, which wrote dependencies "
           "but installed nothing, we did not observe real projects."]
    gateway = "**One gateway.** All models were reached through one OpenAI-compatible gateway."
    if flagged:
        gateway += f" The {series(flagged)} routes add their own system prompt (about 6.6k tokens), so their picks may reflect it; they are marked † in the tables."
    out.append(gateway)
    if result["story"]["duels"]:
        out.append("**Our notes.** Duel notes are short, neutral summaries we wrote from public documentation; real documentation is longer and more persuasive.")
    out.append(f"**One snapshot.** Collected {when} with default sampling; tasks lean to TypeScript and Next.js plus a Python track; "
               f"each model contributes about 12 answers per category, so single-model cells are small.")
    return out
