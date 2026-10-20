"""The claims a release makes, computed from its own numbers.

Every sentence in the report, site and share images is rendered from this dict, so a
claim exists only if the data in the same release supports it, and the next release re-derives it.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

TIERS = ("default", "leaning", "contested")


def _named(shares: dict) -> list:
    return [(k, v) for k, v in shares.items() if not k.startswith("_")]


def tiers(baseline: dict) -> dict:
    out = {t: [] for t in TIERS}
    for cat, row in baseline.items():
        out[row["tier"]].append(cat)
    for t in TIERS:
        out[t].sort(key=lambda c: (-baseline[c]["top_share"], baseline[c]["label"]))
    return out


def splits(row: dict) -> list:
    """How many models have each vendor among their top picks, most first."""
    c = Counter(v for m in row["models"].values() for v in m["tops"])
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))


def duels(baseline: dict, duel: dict, groups: dict, inf: dict) -> dict:
    tier_of = {c: t for t, cats in groups.items() for c in cats}
    contrasts = {}
    for r in (inf.get("duel") or {}).get("contrasts", []):
        contrasts.setdefault(r["category"], []).append(r)
    mde = (inf.get("duel") or {}).get("mde_points", {})
    out = {}
    for cat, row in duel.items():
        none, trio = row["arms"].get("none", {}), row["arms"].get("trio", {})
        fav, fav_none = (_named(none) or [(None, 0.0)])[0]
        lead, lead_trio = (_named(trio) or [(None, 0.0)])[0]
        out[cat] = {
            "favourite": fav,
            "favourite_none": fav_none,
            "favourite_trio": trio.get(fav, 0.0) if fav else 0.0,
            "leader_trio": lead,
            "leader_trio_share": lead_trio,
            "leader_none": none.get(lead, 0.0) if lead else 0.0,
            "held": bool(fav) and lead == fav,
            "solo": row["solo_win"],
            "first_position_rate": row["first_position_rate"],
            "baseline_tier": tier_of.get(cat),
            "shifted": [r["vendor"] for r in contrasts.get(cat, []) if r["shifted"]],
            "favourite_delta": next((r["delta_points"] for r in contrasts.get(cat, []) if r["vendor"] == fav), None),
            "answers": [contrasts[cat][0]["none"][1], contrasts[cat][0]["trio"][1]] if contrasts.get(cat) else [],
            "mde_points": mde.get(cat),
        }
    return out


def pilot_summary(ws, baseline: dict, path: Path) -> dict | None:
    from .normalize import Matcher

    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    model_id = next((m.id for m in ws.models.values() if m.route == data.get("model")), None)
    runs = [r for r in data.get("results", []) if not r.get("is_error")]
    if not model_id or not runs:
        return None
    matcher = Matcher(ws)
    items = []
    for item in runs[0]["picks"]:
        done = Counter(r["picks"].get(item) or "_unspecified" for r in runs)
        done_v, done_n = sorted(done.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        asked = (baseline.get(item) or {}).get("models", {}).get(model_id)
        asked_v = asked["top"] if asked else None
        packages = sorted({d for r in runs for d in r.get("deps", []) if matcher.match(item, d).vendor == done_v and done_v != "_unspecified"})
        items.append({
            "item": item,
            "asked": asked_v,
            "asked_n": asked["counts"].get(asked_v, 0) if asked and asked_v else 0,
            "asked_total": asked["n"] if asked else 0,
            "done": done_v,
            "done_n": done_n,
            "packages": packages,
            "runs": len(runs),
            "same": done_v == asked_v,
        })
    hosts = sorted({r.get("database_url_host") for r in runs if r.get("database_url_host")})
    return {"agent": data.get("agent"), "model_id": model_id, "runs": len(runs), "file": path.relative_to(ws.root).as_posix(),
            "items": items, "same": sum(i["same"] for i in items), "total": len(items), "database_url_hosts": hosts}


def story(result: dict) -> dict:
    base = result.get("baseline") or {}
    duel = result.get("duel") or {}
    man = result["manifest"]
    groups = tiers(base)
    flagged = sorted(m for m, v in man["models"].items() if v.get("injected_prompt"))
    unflagged_disagree = [c for c in groups["contested"]
                          if any(base[c]["top"] not in m["tops"] for mid, m in base[c]["models"].items() if mid not in flagged)]
    inf = result.get("inference") or {}
    d = duels(base, duel, groups, inf)
    solo = [s for row in duel.values() for s in row["solo_win"].values()]
    zero = sorted(([c, v, row["arms"].get("none", {}).get(v, 0.0), row["solo_win"][v]]
                   for c, row in duel.items() for v in row["vendors"]
                   if row["arms"].get("none", {}).get(v, 0.0) <= 0.01 and row["solo_win"][v] >= 0.85),
                  key=lambda x: (-(x[3] - x[2]), x[0], x[1]))
    held = [c for c, x in d.items() if x["held"]]
    order = sorted(((x["first_position_rate"], c) for c, x in d.items() if x["first_position_rate"] is not None), reverse=True)
    base_exp = man["experiments"].get("baseline") or {}
    feature = next((c for c in groups["contested"] if c in duel), groups["contested"][-1] if groups["contested"] else None)
    return {
        "tiers": groups,
        "counts": {t: len(groups[t]) for t in TIERS} | {"categories": len(base)},
        "scale": {
            "models": len(man["models"]),
            "labs": len({m["lab"] for m in man["models"].values()}),
            "baseline_answers": base_exp.get("observed", 0),
            "duel_answers": (man["experiments"].get("duel") or {}).get("observed", 0),
            "tasks": len({t for row in base.values() for t in row["tasks"]}),
            "phrasings": len(base_exp.get("variants", [])),
            "repeats": base_exp.get("repeats", 0),
        },
        "wording": inf.get("wording", {}),
        "position": inf.get("position"),
        "splits": {c: splits(base[c]) for c in groups["contested"]},
        "feature_split": feature,
        "flagged_models": flagged,
        "contested_unflagged_disagree": len(unflagged_disagree),
        "duels": d,
        "solo_range": [min(solo), max(solo)] if solo else [],
        "zero_to_solo": zero,
        "held": held,
        "flipped": [c for c in d if c not in held],
        "first_position_mean": round(sum(r for r, _c in order) / len(order), 4) if order else None,
        "first_position_top": [[c, r] for r, c in order[:2]],
        "pilot": result.get("pilot"),
    }
