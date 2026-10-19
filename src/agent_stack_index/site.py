"""Static report site built from a release's results.json. No JavaScript, no external assets."""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from .config import Workspace
from .narrative import (TITLE, dek, findings, limits, name, names, pct, section_contested, section_default, section_duel,
                        section_meaning, section_pilot)
from .release import latest_release, release_dir

REPO = "https://github.com/BrickerP/agent-stack-index"
SITE = "https://brickerp.github.io/agent-stack-index/"
PALETTE = ["#1f3a5f", "#c2412d", "#c99a2e"]
TIER_HEAD = {
    "default": ("Settled", "every model picks the same tool, at least 95% of answers"),
    "leaning": ("Leaning", "at least 8 of 10 models agree, the tool wins most answers"),
    "contested": ("Contested", "models disagree"),
}
SHARE_IMAGES = {"default-stack": (2400, 1260), "context": (2400, 1350), "contested": (2400, 1350)}


def e(text) -> str:
    return html.escape(str(text), quote=True)


def rich(text: str) -> str:
    """Escape, then render **bold** and `code` from narrative text."""
    out = e(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", out)


def bar(shares: dict, ws: Workspace, category: str) -> str:
    named = [(k, v) for k, v in shares.items() if not k.startswith("_") and v > 0][:3]
    rest = max(0.0, 1.0 - sum(v for _k, v in named))
    segs = [f'<span class="seg" style="width:{v * 100:.1f}%;background:{PALETTE[i]}" title="{e(name(ws, k, category))} {pct(v)}"></span>'
            for i, (k, v) in enumerate(named)]
    if rest > 0.005:
        segs.append(f'<span class="seg rest" style="width:{rest * 100:.1f}%" title="other {pct(rest)}"></span>')
    return f'<span class="bar" aria-hidden="true">{"".join(segs)}</span>'


def mini(x) -> str:
    return f'<span class="mini" aria-hidden="true"><i style="width:{float(x or 0) * 100:.1f}%"></i></span>{pct(x)}'


def mark(man: dict, model_id: str) -> str:
    m = man["models"][model_id]
    return e(m["label"]) + ("<sup>†</sup>" if m.get("injected_prompt") else "")


def tier_rows(ws: Workspace, result: dict) -> str:
    base, st = result["baseline"], result["story"]
    blocks = []
    for tier, cats in st["tiers"].items():
        if not cats:
            continue
        head, sub = TIER_HEAD[tier]
        rows = []
        for c in cats:
            r = base[c]
            named = [(k, v) for k, v in r["pooled"].items() if not k.startswith("_")]
            show = named[:1] if tier == "default" else named[:2]
            pick = " ".join(f"<b>{e(name(ws, k, c))}</b> {pct(v)}" if i == 0 else f'<span class="runner">· {e(name(ws, k, c))} {pct(v)}</span>'
                            for i, (k, v) in enumerate(show))
            agree = f'{r["models_agree"]}/{r["models_total"]}'
            rows.append(f'<li class="row"><span class="cat">{e(r["label"])}</span>{bar(r["pooled"], ws, c)}'
                        f'<span class="pick">{pick} <span class="agree-inline">· {agree}</span></span><span class="agree">{agree}</span></li>')
        blocks.append(f'<div class="tier tier-{tier}"><h3>{head} <span>{len(cats)} · {sub}</span></h3><ol class="rows">{"".join(rows)}</ol></div>')
    return "".join(blocks)


def contested_table(ws: Workspace, result: dict) -> str:
    """One line per contested category: how the models split, and how many keep their pick when reworded."""
    base, st = result["baseline"], result["story"]
    rows = []
    for c in st["tiers"]["contested"]:
        r = base[c]
        chips = "".join(f'<span class="chip{" lead" if i == 0 else ""}">{e(name(ws, v, c))} <b>×{n}</b></span>'
                        for i, (v, n) in enumerate(st["splits"][c]))
        rows.append(f'<li class="split"><span class="cat">{e(r["label"])}</span><span class="chips">{chips}</span>'
                    f'<span class="agree">{r["variant_consistent"]}/{r["models_total"]}</span></li>')
    return (f'<ol class="rows splits"><li class="split head"><span class="cat">Category</span><span class="chips">Top pick of how many models</span>'
            f'<span class="agree">Same pick when reworded</span></li>{"".join(rows)}</ol>'
            f'<p class="note">A model tied between two tools counts for both. Per-model picks are in the appendix.</p>')


def duel_cards(ws: Workspace, result: dict) -> str:
    duel, st = result.get("duel") or {}, result["story"]
    cards = []
    for c, row in duel.items():
        held = st["duels"][c]["held"]
        badge = '<span class="badge held">favourite held</span>' if held else '<span class="badge flip">lead flipped</span>'
        rows = "".join(
            f'<tr><th>{e(name(ws, v, c))}</th><td>{mini(row["arms"].get("none", {}).get(v))}</td>'
            f'<td>{mini(row["arms"].get("trio", {}).get(v))}</td><td class="solo">{pct(row["solo_win"][v])}</td></tr>'
            for v in row["vendors"])
        cards.append(f'<section class="card{" flipped" if not held else ""}"><h3>{e(row["label"])} {badge}</h3>'
                     f'<table class="duel"><thead><tr><th></th><th>no notes</th><th>all three</th><th>alone</th></tr></thead>'
                     f'<tbody>{rows}</tbody></table></section>')
    return f'<div class="cards">{"".join(cards)}</div>'


def pilot_table(ws: Workspace, result: dict) -> str:
    p, base, man = result["story"].get("pilot"), result["baseline"], result["manifest"]
    rows = "".join(
        f'<tr class="{"same" if i["same"] else "diff"}"><th>{e(base[i["item"]]["label"])}</th>'
        f'<td>{e(name(ws, i["asked"], i["item"]))} <small>{i["asked_n"]}/{i["asked_total"]}</small></td>'
        f'<td>{e(name(ws, i["done"], i["item"]))} <small>{i["done_n"]}/{i["runs"]}</small></td></tr>'
        for i in p["items"])
    return (f'<table class="pilot"><thead><tr><th>Need</th><th>Asked ({mark(man, p["model_id"])}, API)</th>'
            f'<th>Written by Claude Code ({p["runs"]} runs)</th></tr></thead><tbody>{rows}</tbody></table>')


def appendix(ws: Workspace, result: dict) -> str:
    base, man = result["baseline"], result["manifest"]
    models = list(man["models"])
    head = "".join(f"<th>{mark(man, m)}</th>" for m in models)
    rows = []
    for c, r in base.items():
        cells = []
        for m in models:
            mm = r["models"].get(m) or {}
            tops = mm.get("tops") or []
            cls = "agree" if r["top"] in tops else "differ"
            cells.append(f'<td class="{cls}">{e(names(ws, tops, c))}<small>{pct(mm.get("top_share"))}</small></td>' if tops else "<td>—</td>")
        rows.append(f"<tr><th>{e(r['label'])}</th>{''.join(cells)}</tr>")
    models_list = "".join(
        f"<li><b>{mark(man, mid)}</b> · {e(m['lab'])} · {m['answers']} answers · reported as {e(', '.join(m['reported']) or '—')}</li>"
        for mid, m in man["models"].items())
    return (f'<details><summary>Top pick by model, all {len(base)} categories</summary><div class="scroll">'
            f'<table class="grid"><thead><tr><th></th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></details>'
            f'<details><summary>Models</summary><ul class="models">{models_list}</ul></details>')


def head_tags(ws: Workspace, result: dict, has_share: bool) -> str:
    man = result["manifest"]
    month = man["title"].split("—")[-1].strip()
    desc = re.sub(r"\*\*|`", "", findings(ws, result)[0])
    ld = {
        "@context": "https://schema.org", "@type": "Dataset", "name": man["title"], "description": dek(result),
        "url": SITE, "license": "https://creativecommons.org/licenses/by/4.0/", "isAccessibleForFree": True,
        "creator": {"@type": "Person", "name": "Yupeng Lu", "url": "https://brickerp.github.io/"},
        "temporalCoverage": (man.get("data_window") or [""])[-1],
        "keywords": ["AI coding agents", "developer tools", "LLM evaluation", "open data"],
        "variableMeasured": "Share of model answers naming each tool, per category",
        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE + "results.json"},
                         {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": SITE + "picks.csv"}],
    }
    tags = [f"<title>{e(TITLE)} — Agent Stack Index, {e(month)}</title>",
            f'<meta name="description" content="{e(desc)}">', f'<link rel="canonical" href="{SITE}">',
            '<meta property="og:type" content="article">', f'<meta property="og:title" content="{e(TITLE)}">',
            f'<meta property="og:description" content="{e(desc)}">', f'<meta property="og:url" content="{SITE}">',
            '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{e(TITLE)}">',
            f'<meta name="twitter:description" content="{e(desc)}">']
    if has_share:
        w, h = SHARE_IMAGES["default-stack"]
        tags += [f'<meta property="og:image" content="{SITE}share/default-stack.png">', f'<meta property="og:image:width" content="{w}">',
                 f'<meta property="og:image:height" content="{h}">', f'<meta name="twitter:image" content="{SITE}share/default-stack.png">',
                 f'<meta property="og:image:alt" content="{e(desc)}">']
    tags.append(f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    return "".join(tags)


def page(ws: Workspace, result: dict, release_id: str, has_share: bool = False) -> str:
    man = result["manifest"]
    month = man["title"].split("—")[-1].strip()
    f = findings(ws, result)
    anchors = ["s1", "s2", "s3"]
    parts = [f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{head_tags(ws, result, has_share)}<link rel="icon" href="data:,"><link rel="stylesheet" href="style.css"></head><body><main>
<p class="eyebrow">Agent Stack Index · {e(month)}</p>
<h1>{e(TITLE)}</h1>
<p class="lede">{rich(dek(result))}</p>
<ol class="findings">{''.join(f'<li><a href="#{anchors[i]}">{rich(t)}</a></li>' for i, t in enumerate(f))}</ol>
<section id="s1"><h2>1 · Most categories already have a default</h2><p>{rich(section_default(ws, result))}</p>
<p class="note">Pooled share of answers, each model weighted equally · right column: models whose top pick it is.</p>{tier_rows(ws, result)}</section>"""]
    if result["story"]["tiers"]["contested"]:
        parts.append(f'<section id="s2"><h2>2 · Without a default, the pick moves with the model and the wording</h2>'
                     f'{"".join(f"<p>{rich(p)}</p>" for p in section_contested(ws, result))}{contested_table(ws, result)}</section>')
    if result.get("duel"):
        parts.append(f'<section id="s3"><h2>3 · What the model reads decides the pick, unless the default is strong</h2>'
                     f'{"".join(f"<p>{rich(p)}</p>" for p in section_duel(ws, result))}'
                     f'<p class="note">Share of picks per arm, models weighted equally. “All three”: neutral notes on all three candidates, order rotated. '
                     f'“Alone”: only that candidate\'s notes.</p>{duel_cards(ws, result)}</section>')
    parts.append(f'<section id="meaning"><h2>What this means</h2>{"".join(f"<p>{rich(p)}</p>" for p in section_meaning(ws, result))}</section>')
    if result["story"].get("pilot"):
        p = result["story"]["pilot"]
        parts.append(f'<section id="pilot"><h2>Early check: asked vs done</h2>{"".join(f"<p>{rich(x)}</p>" for x in section_pilot(ws, result))}'
                     f'{pilot_table(ws, result)}<p class="note">Raw results: <a href="{REPO}/blob/main/{e(p["file"])}">{e(p["file"])}</a></p></section>')
    parts.append(f'<section id="limits"><h2>Limits</h2><ul>{"".join(f"<li>{rich(x)}</li>" for x in limits(ws, result))}</ul></section>')
    parts.append(f"""<section id="data"><h2>Data and method</h2>
<p>Raw answers, the vendor catalog and the code are open, and every number on this page is regenerated from them in CI: <a href="{REPO}/blob/main/docs/METHODOLOGY.md">methodology</a> · <a href="results.json">results.json</a> · <a href="picks.csv">picks.csv</a> · <a href="{REPO}/tree/main/data/observations">raw answers</a> · <a href="REPORT.md">report as Markdown</a> · <a href="{REPO}">code</a>. Answers not matched to the catalog: {pct(man['unmatched_rate'])}. Data CC BY 4.0: cite as “Agent Stack Index, release {e(release_id)}”.</p>
{appendix(ws, result)}</section>
<footer><p>By <a href="https://brickerp.github.io/">Yupeng Lu</a>. The index is vendor-neutral: no vendor pays for placement or sees results early. The author separately builds agent-ready docs, MCP servers and integration tests for developer-tool teams — <a href="https://brickerp.github.io/#contact">contact</a>.</p></footer>
</main></body></html>""")
    return "".join(parts)


def llms_txt(result: dict) -> str:
    return (f"# Agent Stack Index\n\n> {TITLE}. {dek(result)}\n\n## Latest release\n\n"
            f"- [Report (Markdown)]({SITE}REPORT.md): findings, tables, limits\n"
            f"- [Results (JSON)]({SITE}results.json): every number on the report page\n"
            f"- [Picks (CSV)]({SITE}picks.csv)\n"
            f"- [Methodology]({REPO}/blob/main/docs/METHODOLOGY.md)\n"
            f"- [Code and raw answers]({REPO})\n")


def build(ws: Workspace, out: Path, release_id: str | None = None) -> Path:
    release_id = release_id or latest_release(ws)
    src = release_dir(ws, release_id)
    result = json.loads((src / "results.json").read_text(encoding="utf-8"))
    share = src / "share"
    has_share = (share / "default-stack.png").exists()
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page(ws, result, release_id, has_share), encoding="utf-8")
    (out / "llms.txt").write_text(llms_txt(result), encoding="utf-8")
    shutil.copyfile(ws.root / "site" / "style.css", out / "style.css")
    for fname in ("results.json", "picks.csv", "REPORT.md"):
        shutil.copyfile(src / fname, out / fname)
    if share.exists():
        (out / "share").mkdir(exist_ok=True)
        for png in sorted(share.glob("*.png")):
            shutil.copyfile(png, out / "share" / png.name)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return out / "index.html"
