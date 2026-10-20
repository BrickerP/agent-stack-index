"""Inference behind the claims a release makes: null models, intervals and corrected tests.

Pure functions, standard library only, deterministic (seeded from the release's `[analysis]` table). Everything here is computed from
the raw observations and written to results.json, so the report can say "not detected" instead of reading noise as an effect.
"""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict

from .analyze import bucket, keeps_pick, wilson
from .config import Analysis
from .normalize import picks


def fisher(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value for the table [[a, b], [c, d]]."""
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def pm(x: int) -> float:
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)

    p0 = pm(a)
    return min(1.0, sum(pm(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if pm(x) <= p0 * (1 + 1e-9)))


def holm(ps: list) -> list:
    """Holm step-down adjusted p-values, in the input order."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = running
    return out


def binom_upper(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, x) * p ** x * (1 - p) ** (n - x) for x in range(k, n + 1))


def mde_points(n1: int, n2: int, p: float) -> int:
    """Smallest difference, in points, that arms of these sizes resolve with 80% power at alpha 0.05, for a share near p."""
    p = min(max(p, 0.1), 0.9)
    return math.ceil(100 * 2.8 * math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)))


def baseline_answers(ws, records, matcher) -> dict:
    """(category, model) -> [(task, phrasing, picked vendor bucket)] for every baseline answer."""
    out = defaultdict(list)
    for rec, cat, pick in picks(ws, records, matcher):
        out[(cat, rec["model_id"])].append((rec["task_id"], rec["variant"], bucket(pick)))
    return out


def wording(answers: dict, tier_of: dict, an: Analysis) -> dict:
    """Model-category pairs whose top pick differs across phrasings, against the same answers with the phrasing labels shuffled.

    Shuffling happens within each task, so a task effect cannot masquerade as a wording effect. The shuffled counts are what
    sampling noise alone produces; only the excess over them is attributable to the wording.
    """
    rng = random.Random(an.seed)
    prepared, pairs, observed = [], Counter(), Counter()
    for key in sorted(answers):
        items = answers[key]
        tier = tier_of[key[0]]
        by_task = defaultdict(list)
        for i, (task, _v, _b) in enumerate(items):
            by_task[task].append(i)
        prepared.append((tier, [b for _t, _v, b in items], [v for _t, v, _b in items], list(by_task.values())))
        pairs[tier] += 1
        by = defaultdict(Counter)
        for _t, v, b in items:
            by[v][b] += 1
        observed[tier] += not keeps_pick(by)
    null = defaultdict(list)
    for _ in range(an.shuffles):
        got = Counter()
        for tier, buckets, variants, groups in prepared:
            labels = list(variants)
            for idx in groups:
                shuffled = [variants[i] for i in idx]
                rng.shuffle(shuffled)
                for i, v in zip(idx, shuffled):
                    labels[i] = v
            by = defaultdict(Counter)
            for b, v in zip(buckets, labels):
                by[v][b] += 1
            got[tier] += not keeps_pick(by)
        for tier in pairs:
            null[tier].append(got[tier])
    out = {}
    for tier, xs in null.items():
        mean = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / len(xs))
        out[tier] = {"pairs": pairs[tier], "changed": observed[tier], "null_mean": round(mean, 1), "null_sd": round(sd, 1),
                     "excess": round(observed[tier] - mean, 1),
                     "p": round((1 + sum(x >= observed[tier] for x in xs)) / (1 + len(xs)), 4)}
    return out


def duel_counts(ws, records, matcher) -> tuple:
    """(arms, first): raw counts per category and arm, and [first-listed wins, trio answers]."""
    arms = defaultdict(lambda: defaultdict(Counter))
    first = [0, 0]
    for rec, cat, pick in picks(ws, records, matcher):
        b = bucket(pick)
        arms[cat][rec["arm"]][b] += 1
        if rec["arm"] == "trio" and rec.get("order"):
            first[1] += 1
            first[0] += int(b == rec["order"][0])
    return arms, first


def duel_contrasts(arms: dict, duels, an: Analysis) -> dict:
    """No-notes vs all-candidates'-notes for every candidate (Fisher exact, Holm across the whole family)."""
    rows = []
    for d in duels:
        none, trio = arms[d.category]["none"], arms[d.category]["trio"]
        nn, nt = sum(none.values()), sum(trio.values())
        for v in d.vendors:
            a, c = none[v], trio[v]
            rows.append({"category": d.category, "vendor": v, "none": [a, nn], "trio": [c, nt],
                         "delta_points": round(100 * (c / nt - a / nn)) if nn and nt else 0,
                         "ci_none": wilson(a, nn), "ci_trio": wilson(c, nt),
                         "p": fisher(a, nn - a, c, nt - c) if nn and nt else 1.0})
    for r, q in zip(rows, holm([r["p"] for r in rows])):
        r["p"], r["p_adj"] = round(r["p"], 4), round(q, 4)
        r["shifted"] = q < an.alpha and abs(r["delta_points"]) >= an.min_effect_points
    mde = {}
    for d in duels:
        mine = [r for r in rows if r["category"] == d.category]
        nn, nt = mine[0]["none"][1], mine[0]["trio"][1]
        lead = max(mine, key=lambda r: r["none"][0])
        mde[d.category] = mde_points(nn, nt, lead["none"][0] / nn) if nn and nt else None
    return {"contrasts": rows, "mde_points": mde}


def position(first: list, duels) -> dict:
    """Does the first-listed candidate win more often than chance (one in the number of candidates)?"""
    k, n = first
    p0 = sum(1 / len(d.vendors) for d in duels) / len(duels) if duels else 1 / 3
    return {"first": k, "n": n, "rate": round(k / n, 4) if n else None, "expected": round(p0, 4), "ci": wilson(k, n),
            "p": round(binom_upper(k, n, p0), 4) if n else None}


def run(ws, records: dict, duels, matcher, an: Analysis, tier_of: dict) -> dict:
    """records: {"baseline": [...], "duel": [...]} -> the `inference` block of results.json."""
    out = {}
    if records.get("baseline"):
        out["wording"] = wording(baseline_answers(ws, records["baseline"], matcher), tier_of, an)
    if records.get("duel") and duels:
        arms, first = duel_counts(ws, records["duel"], matcher)
        out["duel"] = duel_contrasts(arms, duels, an)
        out["position"] = position(first, duels)
    return out
