"""Static report site built from a release's results.json. No JavaScript, no external assets."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .config import Workspace
from .release import latest_release, release_dir
from .report import headline, name, pct

REPO = "https://github.com/BrickerP/agent-stack-index"
PALETTE = ["#1f3a5f", "#c2412d", "#c99a2e", "#2f7d74", "#7b6aa8"]


def e(text) -> str:
    return html.escape(str(text), quote=True)


def bar(ws: Workspace, shares: dict, category: str, limit: int = 4) -> str:
    named = [(k, v) for k, v in shares.items() if not k.startswith("_") and v > 0][:limit]
    rest = max(0.0, 1.0 - sum(v for _k, v in named))
    segs = []
    for i, (k, v) in enumerate(named):
        label = f"{name(ws, k, category)} {pct(v)}"
        segs.append(f'<span class="seg" style="width:{v * 100:.1f}%;background:{PALETTE[i % len(PALETTE)]}" title="{e(label)}"></span>')
    if rest > 0.005:
        segs.append(f'<span class="seg rest" style="width:{rest * 100:.1f}%" title="other {pct(rest)}"></span>')
    legend = " · ".join(f'<i style="background:{PALETTE[i % len(PALETTE)]}"></i>{e(name(ws, k, category))} {pct(v)}' for i, (k, v) in enumerate(named))
    return f'<div class="bar">{"".join(segs)}</div><p class="legend">{legend}</p>'


def md_inline(text: str) -> str:
    out = e(text)
    while "**" in out:
        out = out.replace("**", "<b>", 1).replace("**", "</b>", 1)
    return out.lstrip("- ")


def page(ws: Workspace, result: dict, release_id: str) -> str:
    man = result["manifest"]
    base = result.get("baseline") or {}
    duel = result.get("duel") or {}
    labs = sorted({m["lab"] for m in man["models"].values()})
    parts = [f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(man['title'])}</title><meta name="description" content="Which tools AI coding models pick when they start a project from scratch, measured across {len(man['models'])} models.">
<link rel="icon" href="data:,"><link rel="stylesheet" href="style.css"></head><body><main>
<p class="eyebrow">Agent Stack Index · release {e(release_id)}</p>
<h1>What AI coding models pick when they start a project from scratch</h1>
<p class="lede">{len(man['models'])} models from {len(labs)} labs, {len(base)} categories, {man['answers']:,} answers. Every number comes from <a href="{REPO}">open data and code</a>.</p>
<ul class="headline">{''.join(f'<li>{md_inline(x)}</li>' for x in headline(ws, result))}</ul>
<h2>The default stack</h2><p class="note">Pooled share of each model's picks, models weighted equally.</p><div class="cats">"""]
    for cat, r in base.items():
        parts.append(f'<section class="cat"><h3>{e(r["label"])} <span>{r["models_agree"]}/{r["models_total"]} models agree</span></h3>{bar(ws, r["pooled"], cat)}</section>')
    parts.append("</div>")
    models = list(man["models"])
    if base:
        head = "".join(f"<th>{e(man['models'][m]['label'])}</th>" for m in models)
        rows = []
        for cat, r in base.items():
            cells = []
            for m in models:
                mm = r["models"].get(m) or {}
                top = mm.get("top")
                cls = "agree" if top and top == r["top"] else "differ"
                cells.append(f'<td class="{cls}">{e(name(ws, top, cat))}<small>{pct(mm.get("top_share"))}</small></td>' if top else "<td>—</td>")
            rows.append(f"<tr><th>{e(r['label'])}</th>{''.join(cells)}</tr>")
        parts.append(f'<h2>Top pick by model</h2><div class="scroll"><table><thead><tr><th></th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    if duel:
        parts.append('<h2>Does documentation in context move the pick?</h2><p class="note">Same task, three arms: no notes; all candidates\' notes, order rotated; each candidate\'s notes alone.</p><div class="cats">')
        for cat, r in duel.items():
            rows = "".join(
                f'<tr><th>{e(name(ws, v, cat))}</th><td>{pct(r["arms"].get("none", {}).get(v))}</td><td>{pct(r["arms"].get("trio", {}).get(v))}</td><td><b>{pct(r["solo_win"][v])}</b></td></tr>'
                for v in r["vendors"])
            parts.append(f'<section class="cat"><h3>{e(r["label"])}</h3><table class="duel"><thead><tr><th></th><th>no notes</th><th>all notes</th><th>its notes alone</th></tr></thead><tbody>{rows}</tbody></table></section>')
        parts.append("</div>")
    model_rows = "".join(f"<li><b>{e(m['label'])}</b> · {e(m['lab'])} · {m['answers']} answers{(' · ' + e(m['notes'])) if m['notes'] else ''}</li>" for m in man["models"].values())
    parts.append(f"""<h2>Method, briefly</h2>
<p>Each model gets the same build tasks in three phrasings and names one package or service per need. Answers are matched to a public catalog of vendors; unmatched answers are counted, not dropped ({pct(man['unmatched_rate'])} this release). Read the <a href="{REPO}/blob/main/docs/METHODOLOGY.md">methodology and limitations</a>: these are stated preferences from API calls. A first <a href="{REPO}/blob/main/docs/pilots/2026-10-agent-probe.md">ask-vs-do pilot</a> ran Claude Code on the SaaS-starter task: it matched the asked answers on 4 of 6 needs, but installed Auth.js where the same model, asked, named Better Auth.</p>
<h2>Models</h2><ul class="models">{model_rows}</ul>
<h2>Data</h2><p><a href="results.json">results.json</a> · <a href="picks.csv">picks.csv</a> · <a href="{REPO}/tree/main/data/observations">raw answers</a> · <a href="{REPO}/blob/main/releases/{e(release_id)}/REPORT.md">report</a> · catalog <code>{e(man['catalog_sha'])}</code></p>
<footer><p>By <a href="https://brickerp.github.io/">Yupeng Lu</a>. The index is vendor-neutral: no vendor pays for placement or sees results early. The author separately builds agent-ready docs, MCP servers and integration tests for developer-tool teams — <a href="https://brickerp.github.io/#contact">contact</a>.</p></footer>
</main></body></html>""")
    return "".join(parts)


def build(ws: Workspace, out: Path, release_id: str | None = None) -> Path:
    release_id = release_id or latest_release(ws)
    src = release_dir(ws, release_id)
    result = json.loads((src / "results.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page(ws, result, release_id), encoding="utf-8")
    shutil.copyfile(ws.root / "site" / "style.css", out / "style.css")
    for fname in ("results.json", "picks.csv", "REPORT.md"):
        shutil.copyfile(src / fname, out / fname)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return out / "index.html"
