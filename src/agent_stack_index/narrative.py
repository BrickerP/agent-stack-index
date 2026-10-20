"""Sentences of the report, rendered from the release's `story` and `inference`. Shared by Markdown, HTML and share images.

Text uses **bold** markers only; renderers convert them. Every number comes from the result dict, and every claim is worded by what
its test supports: "changed" only when the noise check says so, "no detectable change" otherwise.
"""
from __future__ import annotations

import math

from .config import Analysis, Workspace

TITLE = "AI coding models already have a default stack"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
PROPER = {"Python", "Postgres", "LLM", "UI", "ORM"}
NO_WORDING = {"pairs": 0, "changed": 0, "null_mean": 0.0, "null_sd": 0.0, "excess": 0.0, "p": 1.0}


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


def pfmt(p) -> str:
    return "p < 0.001" if p is not None and p < 0.001 else f"p = {p:.3f}"


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


def analysis(result: dict) -> Analysis:
    return Analysis(**result["manifest"]["analysis"])


def wording(st: dict, tier: str) -> dict:
    return st.get("wording", {}).get(tier) or NO_WORDING


def settled_rule(an: Analysis) -> str:
    return f"every model picks the same tool and it takes at least {pct(an.default_share)} of the answers"


def leaning_rule(an: Analysis, n_models: int) -> str:
    return f"at least {math.ceil(an.leaning_agree * n_models)} of {n_models} models agree"


def dek(result: dict) -> str:
    sc = result["story"]["scale"]
    phrasing = f", in {word(sc['phrasings'])} phrasings, {word(sc['repeats'])} times each" if sc.get("phrasings") else ""
    return (f"We asked {sc['models']} models from {sc['labs']} labs to start the same {sc['tasks']} projects from scratch and name one tool "
            f"for each of {result['story']['counts']['categories']} needs{phrasing} ({sc['baseline_answers']:,} answers). "
            f"Then we put neutral notes on competing tools in front of them {sc['duel_answers']:,} more times.")


def status_line(result: dict) -> str:
    """One sentence on how much the design was fixed in advance."""
    p = result["manifest"].get("protocol") or {}
    if p.get("status") == "pilot":
        return ("**Pilot.** The design was not pre-registered, so every finding below is exploratory. "
                "Each one is checked against a noise model; see Limits for how far it holds.")
    if p.get("status") == "confirmatory":
        when = (p.get("locked_at") or "")[:10]
        return (f"**Pre-registered.** Design and analysis plan were locked on {when} (protocol {p['sha']}). "
                f"Findings are labelled confirmed or not detected against that plan.")
    return ""


def question(result: dict) -> str:
    return (result["manifest"].get("protocol") or {}).get("goal", "")


def finding_tags(result: dict) -> list:
    """Evidence label for each headline finding: exploratory in a pilot, confirmed / not detected against a locked plan."""
    st, an = result["story"], analysis(result)
    status = (result["manifest"].get("protocol") or {}).get("status")
    n = 1 + bool(wording(st, "contested")["pairs"]) + bool(st["duels"])
    if status != "confirmatory":
        return ["exploratory"] * n
    tags = ["descriptive"]
    if wording(st, "contested")["pairs"]:
        tags.append("confirmed" if wording(st, "contested")["p"] < an.alpha else "not detected")
    if st["duels"]:
        tags.append("confirmed" if any(d["shifted"] for d in st["duels"].values()) else "not detected")
    return tags


def harness_note(result: dict) -> str:
    return (result["manifest"].get("protocol") or {}).get("benefit", {}).get("harness", "")


def findings(ws: Workspace, result: dict) -> list:
    st, an = result["story"], analysis(result)
    c, n = st["counts"], st["scale"]["models"]
    wc, wd = wording(st, "contested"), wording(st, "default")
    out = [f"**Most categories already have a default.** In {c['default']} of {c['categories']} categories {settled_rule(an)}; "
           f"in {c['leaning']} more, {leaning_rule(an, n)}."]
    if wc["pairs"]:
        head = ("**Without a default, the pick also moves with the wording.**" if wc["p"] < an.alpha
                else "**We could not detect an effect of wording.**")
        out.append(f"{head} In the {c['contested']} contested categories, {wc['changed']} of {wc['pairs']} model–category pairs change "
                   f"their top pick when the request is reworded, against about {round(wc['null_mean'])} expected from sampling noise alone; "
                   f"in the default categories, {few(wd['changed'], wd['pairs'])} do.")
    if st["duels"]:
        lo, hi = st["solo_range"]
        d = st["duels"]
        mdes = [x["mde_points"] for x in d.values() if x["mde_points"]]
        side = (f"With all candidates' notes side by side, the favourite showed no detectable change in {word(len(st['held']))} of the "
                f"{word(len(d))} categories we tested")
        side += f" (shifts under about {min(mdes)}–{max(mdes)} points cannot be ruled out)" if mdes else ""
        flipped = [x for x in st["flipped"] if d[x]["shifted"]]
        if flipped:
            f = flipped[0]
            no_default = ", which has no default," if d[f]["baseline_tier"] == "contested" else ""
            side += f"; in {lower(label(result, f))}{no_default} the lead flipped."
        elif st["flipped"]:
            side += f"; in {lower(label(result, st['flipped'][0]))} the lead changed, within noise."
        else:
            side += "."
        out.append(f"**What the model reads can decide the pick.** With only one candidate's notes in context, models pick it "
                   f"{pts(lo)}–{pct(hi)} of the time. {side}")
    return out


def section_default(ws: Workspace, result: dict) -> str:
    st, an = result["story"], analysis(result)
    c, n = st["counts"], st["scale"]["models"]
    return (f"{word(c['default'], True)} categories are settled: {settled_rule(an)}. "
            f"{word(c['leaning'], True)} more lean one way: {leaning_rule(an, n)} and the tool wins most answers. "
            f"{word(c['contested'], True)} are contested.")


def section_contested(ws: Workspace, result: dict) -> list:
    st, base, an = result["story"], result["baseline"], analysis(result)
    out = []
    f = st.get("feature_split")
    if f:
        split = st["splits"][f]
        parts = [f"{name(ws, v, f)} is the top pick of {n} model{'s' if n != 1 else ''}" if i == 0 else f"{name(ws, v, f)} of {n}"
                 for i, (v, n) in enumerate(split)]
        out.append(f"Where no tool is settled, models split. In {lower(base[f]['label'])}, {series(parts)}.")
    wc, wl, wd = wording(st, "contested"), wording(st, "leaning"), wording(st, "default")
    if wc["pairs"]:
        noise = f"{round(wc['null_mean'])} ± {wc['null_sd']:.0f}"
        if wc["p"] < an.alpha:
            out.append(f"The same model's answer also depends on the wording: in contested categories, {wc['changed']} of {wc['pairs']} "
                       f"model–category pairs change their top pick across the three phrasings. Shuffling the phrasing labels over the same "
                       f"answers gives {noise} (sampling noise alone), so the wording accounts for roughly {round(wc['excess'])} of the "
                       f"{wc['pairs']} ({pfmt(wc['p'])}).")
        else:
            out.append(f"We could not detect an effect of wording: {wc['changed']} of {wc['pairs']} model–category pairs change their top pick "
                       f"across the three phrasings, against {noise} when the phrasing labels are shuffled ({pfmt(wc['p'])}).")
        lean_note = "" if wl["p"] < an.alpha else " (no detectable wording effect)"
        out.append(f"In leaning categories {few(wl['changed'], wl['pairs'])} change, against about {round(wl['null_mean'])} expected{lean_note}; "
                   f"in default categories, {few(wd['changed'], wd['pairs'])}.")
    if st["flagged_models"]:
        flagged = series(result["manifest"]["models"][m]["label"] for m in st["flagged_models"])
        out.append(f"The split is not just the {flagged} routes, which add a hidden system prompt (see Limits): in "
                   f"{st['contested_unflagged_disagree']} of {len(st['tiers']['contested'])} contested categories, at least one other model "
                   f"also disagrees with the pooled pick.")
    return out


def section_duel(ws: Workspace, result: dict) -> list:
    st, an = result["story"], analysis(result)
    d = st["duels"]
    if not d:
        return []
    lo, hi = st["solo_range"]
    ex = [f"{name(ws, v, c)} {pct(none)} → {pct(solo)}" for c, v, none, solo in st["zero_to_solo"][:3]]
    out = [f"In {word(len(d))} duels we gave the same single-need task three ways: no notes; neutral notes on three candidates, in rotated order; "
           f"and one candidate's notes alone. Alone, every candidate won {pts(lo)}–{pct(hi)} of picks"
           + (f", including tools that got 0% with no notes ({', '.join(ex)})." if ex else ".")
           + " That is close to a forced choice: it shows the notes are read, not that they persuade."]
    held = st["held"]
    if held:
        shown = [f"{name(ws, d[c]['favourite'], c)} {pct(d[c]['favourite_none'])} → {pct(d[c]['favourite_trio'])}" for c in held]
        n_none, n_trio = d[held[0]]["answers"] or [0, 0]
        mdes = [d[c]["mde_points"] for c in held if d[c]["mde_points"]]
        text = (f"Side by side, the no-notes favourite stayed on top in {word(len(held))} of {word(len(d))} duels, with no detectable shift "
                f"({', '.join(shown)}).")
        if mdes:
            text += (f" With {n_none} and {n_trio} answers per arm, shifts under about {min(mdes)}–{max(mdes)} points cannot be told apart "
                     f"from noise, so this means no detectable change, not no change.")
        out.append(text)
    for c in held:
        if d[c]["shifted"]:
            out.append(f"In {lower(label(result, c))} the favourite stayed on top, but "
                       f"{series(name(ws, v, c) for v in d[c]['shifted'])} moved detectably.")
    k = len(((result.get("inference") or {}).get("duel") or {}).get("contrasts", []))
    for c in st["flipped"]:
        x = d[c]
        why = ", where models had no default," if x["baseline_tier"] == "contested" else ""
        moves = (f"{name(ws, x['favourite'], c)} {pct(x['favourite_none'])} → {pct(x['favourite_trio'])}, "
                 f"{name(ws, x['leader_trio'], c)} {pct(x['leader_none'])} → {pct(x['leader_trio_share'])}")
        if x["shifted"]:
            out.append(f"In {lower(label(result, c))}{why} the lead flipped: {moves} (significant after correcting for {k} comparisons).")
        else:
            out.append(f"In {lower(label(result, c))}{why} the lead changed, within noise: {moves}.")
    pos = st.get("position")
    if pos and pos["n"]:
        ci = pos["ci"]
        stat = f"95% interval {pts(ci[0])}–{pct(ci[1])}; chance is {pct(pos['expected'])}; {pfmt(pos['p'])}"
        if pos["p"] < an.alpha:
            out.append(f"Order mattered: the first-listed candidate won {pct(pos['rate'])} of side-by-side picks ({stat}).")
        else:
            out.append(f"We could not detect an order effect: the first-listed candidate won {pct(pos['rate'])} of side-by-side picks ({stat}).")
    return out


def section_meaning(ws: Workspace, result: dict) -> list:
    st, an = result["story"], analysis(result)
    d, pos = st["duels"], st.get("position")
    order = bool(pos and pos["n"] and pos["p"] < an.alpha)
    most = sorted(st["tiers"]["contested"], key=lambda c: (result["baseline"][c]["top_share"], c))[:5]
    contested = [lower(result["baseline"][c]["label"]) for c in most]
    dev = ("**If you build with agents:** an agent's stack is mostly the model's default plus whatever documentation reaches its context. "
           "If you care which tool you get, name it; in contested categories, rewording the request can change the answer"
           + (", and the order of a list you give it matters." if order else "."))
    vendor = "**If you make developer tools:** if you are not the default, the lever is being read" + (", and being listed first helps." if order else ".")
    if d:
        lo, hi = st["solo_range"]
        settled = [c for c in st["held"] if d[c]["baseline_tier"] == "default"]
        flips = [c for c in st["flipped"] if d[c]["shifted"]]
        vendor += f" Alone in context, every candidate's notes won {pts(lo)}–{pct(hi)} of picks"
        vendor += "; next to a settled default we detected no shift" if settled else ""
        vendor += ", and where there was no default the notes flipped the lead." if flips else "."
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
    man, st, base = result["manifest"], result["story"], result["baseline"]
    flagged = [man["models"][m]["label"] for m in st["flagged_models"]]
    window = man.get("data_window") or []
    when = window[0] if len(window) == 2 and window[0] == window[1] else " to ".join(window)
    out = []
    if (man.get("protocol") or {}).get("status") == "pilot":
        out.append("**Pilot.** The design was not pre-registered, and some choices (the tier thresholds, the statistics added after a first "
                   "look) were made after seeing data, so every finding is exploratory. Confirmatory releases lock their protocol before "
                   "any data is collected (docs/CHARTER.md).")
    out.append("**Stated preference.** Each answer is one API call naming a tool. Apart from the file-only pilot above, which wrote dependencies "
               "but installed nothing, we did not observe real projects.")
    gateway = "**One gateway.** All models were reached through one OpenAI-compatible gateway."
    if flagged:
        gateway += f" The {series(flagged)} routes add their own system prompt (about 6.6k tokens), so their picks may reflect it; they are marked † in the tables."
    out.append(gateway)
    if not all("temperature" in (m.get("params") or {}) for m in man["models"].values()):
        out.append("**Default sampling.** Every model ran at its route's default sampling settings, which differ between models and were not recorded.")
    single = sum(1 for r in base.values() if len(r["tasks"]) == 1)
    out.append(f"**One task per category.** {single} of {len(base)} categories were asked through a single task prompt (in three phrasings), "
               f"so a default is a default for that task.")
    labs = {}
    for m in man["models"].values():
        labs[m["lab"]] = labs.get(m["lab"], 0) + 1
    twins = series(f"{word(k)} from {lab}" for lab, k in labs.items() if k > 1)
    out.append(f"**Models are not independent.** The {len(man['models'])} models come from {len(labs)} labs"
               + (f" ({twins})" if twins else "") + ", so \"every model agrees\" is weaker than that many independent confirmations.")
    if st["duels"]:
        n_none, n_trio = next((x["answers"] for x in st["duels"].values() if x["answers"]), (0, 0))
        out.append(f"**Our notes, few answers.** Duel notes are short, neutral summaries we wrote from public documentation; real documentation is "
                   f"longer and more persuasive. Each duel arm holds {n_none} to {n_trio} answers, which is why most shifts are \"not detected\" "
                   f"rather than \"absent\".")
    window_note = f"**One snapshot.** Collected {when} with default sampling; tasks lean to TypeScript and Next.js plus a Python track; "
    out.append(window_note + "each model contributes about 12 answers per category, so single-model cells are small.")
    return out
