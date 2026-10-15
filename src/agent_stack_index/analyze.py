"""Statistics over normalized picks. Pure functions: records + catalog in, plain dicts out.

Models are weighted equally when pooling, so a model that answers more often does not dominate.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

from .config import Workspace
from .normalize import Matcher, picks

OTHER = "_other"  # answered, but not a catalog vendor
NONE = "_none"  # empty, missing or "not needed"


def wilson(k: int, n: int, z: float = 1.96) -> list:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def bucket(pick) -> str:
    if pick.vendor:
        return pick.vendor
    return OTHER if pick.how == "unmatched" else NONE


def share_table(counter: Counter) -> dict:
    n = sum(counter.values())
    return {k: round(v / n, 4) for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))} if n else {}


def pooled(per_model: dict) -> dict:
    """Equal-weight mean of each model's share vector."""
    tables = [share_table(c) for c in per_model.values() if sum(c.values())]
    if not tables:
        return {}
    keys = set().union(*tables)
    mean = {k: sum(t.get(k, 0.0) for t in tables) / len(tables) for k in keys}
    return dict(sorted(((k, round(v, 4)) for k, v in mean.items()), key=lambda kv: (-kv[1], kv[0])))


def top(shares: dict) -> tuple:
    named = [(k, v) for k, v in shares.items() if not k.startswith("_")]
    return named[0] if named else (None, 0.0)


def summarize(per_model: dict, per_variant: dict) -> dict:
    models = {}
    for model_id, counter in sorted(per_model.items()):
        n = sum(counter.values())
        t, s = top(share_table(counter))
        models[model_id] = {
            "n": n,
            "counts": dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))),
            "top": t,
            "top_share": s,
            "top_ci": wilson(counter.get(t, 0), n) if t else [0.0, 0.0],
        }
    pool = pooled(per_model)
    pool_top, pool_share = top(pool)
    agree = sum(1 for m in models.values() if m["top"] == pool_top)
    consistent = 0
    for model_id, variants in per_variant.items():
        tops = {top(share_table(c))[0] for c in variants.values() if sum(c.values())}
        consistent += len(tops) == 1
    return {
        "n": sum(m["n"] for m in models.values()),
        "models": models,
        "pooled": pool,
        "top": pool_top,
        "top_share": pool_share,
        "models_agree": agree,
        "models_total": len(models),
        "variant_consistent": consistent,
        "hhi": round(sum(v * v for k, v in pool.items() if not k.startswith("_")), 4),
    }


def baseline(ws: Workspace, records, matcher: Matcher | None = None) -> dict:
    per = defaultdict(lambda: defaultdict(Counter))
    per_var = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    tasks = defaultdict(set)
    for rec, cat, pick in picks(ws, records, matcher):
        b = bucket(pick)
        per[cat][rec["model_id"]][b] += 1
        per_var[cat][rec["model_id"]][rec["variant"]][b] += 1
        tasks[cat].add(rec["task_id"])
    out = {}
    for cat in sorted(per, key=lambda c: list(ws.categories).index(c) if c in ws.categories else 999):
        out[cat] = {"label": ws.categories[cat].label, "group": ws.categories[cat].group, "tasks": sorted(tasks[cat])}
        out[cat].update(summarize(per[cat], per_var[cat]))
    return out


def duel(ws: Workspace, records, spec_duels, matcher: Matcher | None = None) -> dict:
    by_cat = {d.category: d for d in spec_duels}
    arms = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    first = defaultdict(Counter)
    for rec, cat, pick in picks(ws, records, matcher):
        if cat not in by_cat:
            continue
        b = bucket(pick)
        arms[cat][rec["arm"]][rec["model_id"]][b] += 1
        if rec["arm"] == "trio" and rec.get("order"):
            first[cat]["n"] += 1
            first[cat]["first"] += int(b == rec["order"][0])
    out = {}
    for cat, d in by_cat.items():
        table = {arm: pooled(per_model) for arm, per_model in arms[cat].items()}
        none, trio = table.get("none", {}), table.get("trio", {})
        out[cat] = {
            "label": ws.categories[cat].label,
            "task": d.task,
            "vendors": list(d.vendors),
            "arms": table,
            "n": {arm: sum(sum(c.values()) for c in pm.values()) for arm, pm in arms[cat].items()},
            "lift": {v: round(trio.get(v, 0.0) - none.get(v, 0.0), 4) for v in d.vendors},
            "solo_win": {v: table.get(f"solo:{v}", {}).get(v, 0.0) for v in d.vendors},
            "first_position_rate": round(first[cat]["first"] / first[cat]["n"], 4) if first[cat]["n"] else None,
            "trio_top_by_model": {m: top(share_table(c))[0] for m, c in sorted(arms[cat].get("trio", {}).items())},
        }
    return out
