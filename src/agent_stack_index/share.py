"""Share images (Open Graph card and thread images) rendered from a release's story.

Writes releases/<id>/share/<name>.html from the data, then screenshots each with headless Chrome
(set CHROME to the binary if it is not found). PNGs are committed; the site copies them.
"""
from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
from pathlib import Path

from .config import Workspace
from .narrative import TITLE, label, lower, name, pct
from .release import latest_release, release_dir

CSS = """*{box-sizing:border-box;margin:0}body{width:1200px;height:%(h)spx;background:#f6f0e3;color:#3b4250;font-family:Charter,'Bitstream Charter',Cambria,Georgia,serif;
padding:56px 64px;display:flex;flex-direction:column;overflow:hidden}
.eyebrow{font:500 15px ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:#6c7380}
h1{font-size:54px;line-height:1.06;color:#1f3a5f;margin:12px 0 0;letter-spacing:-.01em}
.grow{flex:1;display:flex;flex-direction:column;justify-content:center}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px 22px}
.cell{border-top:2px solid #1f3a5f;padding-top:8px}.cell span{display:block;font:500 13px ui-monospace,Menlo,monospace;color:#6c7380;letter-spacing:.04em;text-transform:uppercase}
.cell b{display:block;font-size:27px;color:#1f3a5f;margin-top:4px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}
.stat .big{font-size:50px;color:#c2412d;font-weight:700;letter-spacing:-.02em;white-space:nowrap}.stat .who{font-size:25px;color:#1f3a5f;margin-top:6px}
.stat .what{font:500 14px ui-monospace,Menlo,monospace;color:#6c7380;margin-top:6px;letter-spacing:.03em}
.line{font-size:25px;line-height:1.4;color:#3b4250;margin-top:30px;max-width:30em}.line b{color:#1f3a5f}
.split{display:grid;gap:16px}.split .r{display:grid;grid-template-columns:320px 1fr 210px;align-items:center;gap:18px;font-size:28px;color:#1f3a5f}
.split .bar{height:30px;background:#1f3a5f}.split .n{font:500 20px ui-monospace,Menlo,monospace;color:#6c7380;white-space:nowrap}
.foot{display:flex;justify-content:space-between;align-items:baseline;border-top:1px solid #d9d0bd;padding-top:14px;font:500 15px ui-monospace,Menlo,monospace;color:#6c7380}
.foot b{color:#c2412d;font-weight:600}
.label{font:500 15px ui-monospace,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;color:#6c7380;margin-bottom:16px}"""


def e(text) -> str:
    return html.escape(str(text), quote=True)


def doc(height: int, body: str) -> str:
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS % {"h": height}}</style></head><body>{body}</body></html>'


def foot(result: dict) -> str:
    sc = result["story"]["scale"]
    return (f'<div class="foot"><span>{sc["models"]} models · {sc["labs"]} labs · {sc["baseline_answers"]:,} answers · open data</span>'
            f'<b>brickerp.github.io/agent-stack-index</b></div>')


def eyebrow(result: dict) -> str:
    return f'<p class="eyebrow">Agent Stack Index · {e(result["manifest"]["title"].split("—")[-1].strip())}</p>'


def card_default(ws: Workspace, result: dict) -> str:
    st, base = result["story"], result["baseline"]
    cells = "".join(f'<div class="cell"><span>{e(base[c]["label"])}</span><b>{e(name(ws, base[c]["top"], c))}</b></div>'
                    for c in st["tiers"]["default"][:12])
    c = st["counts"]
    line = (f'<p class="line">In <b>{c["default"]} of {c["categories"]}</b> categories, every model picks the same tool '
            f'and it takes at least 95% of the answers.</p>')
    return doc(630, f'{eyebrow(result)}<h1>{e(TITLE)}</h1><div class="grow"><div class="grid">{cells}</div>{line}</div>{foot(result)}')


def card_context(ws: Workspace, result: dict) -> str:
    st = result["story"]
    stats = "".join(f'<div class="stat"><div class="big">{pct(none)} → {pct(solo)}</div><div class="who">{e(name(ws, v, c))}</div>'
                    f'<div class="what">{e(label(result, c))}</div></div>'
                    for c, v, none, solo in st["zero_to_solo"][:3])
    stats = (f'<p class="label">Share of picks · no notes → only its own notes in context</p>'
             f'<div class="stats">{stats}</div>')
    line = ""
    if st["flipped"]:
        f = st["flipped"][0]
        x = st["duels"][f]
        line = (f'<p class="line">With all three candidates\' notes side by side, the favourite held in <b>{len(st["held"])} of {len(st["duels"])}</b> '
                f'categories. In {e(lower(label(result, f)))}: {e(name(ws, x["favourite"], f))} {pct(x["favourite_none"])} → {pct(x["favourite_trio"])}, '
                f'<b>{e(name(ws, x["leader_trio"], f))} {pct(x["leader_none"])} → {pct(x["leader_trio_share"])}</b>.</p>')
    return doc(675, f'{eyebrow(result)}<h1>What the model reads decides the pick</h1><div class="grow">{stats}{line}</div>{foot(result)}')


def card_contested(ws: Workspace, result: dict) -> str:
    st, base = result["story"], result["baseline"]
    f = st.get("feature_split")
    rows = ""
    if f:
        total = base[f]["models_total"] or 1
        rows = "".join(f'<div class="r"><span>{e(name(ws, v, f))}</span><span class="bar" style="width:{100 * n / total:.0f}%"></span>'
                       f'<span class="n">{n} of {total} models</span></div>' for v, n in st["splits"][f])
        rows = f'<p class="label">Top pick for {e(lower(base[f]["label"]))}, by model</p><div class="split">{rows}</div>'
    cs, ct = st["stability"]["contested"]
    ds, dt = st["stability"]["default"]
    settled = "none" if dt - ds == 0 else f"{dt - ds} of {dt}"
    line = (f'<p class="line">In the {st["counts"]["contested"]} contested categories, <b>{ct - cs} of {ct}</b> model–category pairs change their '
            f'top pick when the request is reworded. In the {st["counts"]["default"]} settled categories, {settled} do.</p>')
    return doc(675, f'{eyebrow(result)}<h1>No default, no stable answer</h1><div class="grow">{rows}{line}</div>{foot(result)}')


CARDS = {"default-stack": (card_default, 630), "context": (card_context, 675), "contested": (card_contested, 675)}


def chrome() -> str | None:
    for candidate in (os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                      shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chrome")):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def build(ws: Workspace, release_id: str | None = None) -> list:
    release_id = release_id or latest_release(ws)
    src = release_dir(ws, release_id)
    result = json.loads((src / "results.json").read_text(encoding="utf-8"))
    out = src / "share"
    out.mkdir(exist_ok=True)
    binary = chrome()
    written = []
    for key, (render, height) in CARDS.items():
        if key == "context" and not result["story"]["duels"]:
            continue
        if key == "contested" and not result["story"]["tiers"]["contested"]:
            continue
        page = out / f"{key}.html"
        page.write_text(render(ws, result), encoding="utf-8")
        written.append(page)
        if binary:
            png = out / f"{key}.png"
            subprocess.run([binary, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                            f"--window-size=1200,{height}", f"--screenshot={png}", page.resolve().as_uri()],
                           check=True, capture_output=True, timeout=120)
            written.append(png)
    return written
