"""Map raw choice strings to catalog vendors, scoped by category.

Matching order: exact alias inside the category, exact alias anywhere (cross-category), then the
longest alias that appears as a whole word inside the answer. Everything unmatched is reported so
the catalog can be curated; re-running analysis then updates every release deterministically.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .config import Workspace

EMPTY = {"", "none", "n/a", "na", "null", "-", "no", "not needed", "skip", "unknown"}
SPLIT = re.compile(r"\s+(?:\+|/|&|or|and|with|via|on|using|plus)\s+|,\s*|;\s*")


def canon(text: str) -> str:
    s = str(text).strip().strip("`\"' ").lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(?<=[a-z0-9\-/])@[\^~]?\d[\w.\-]*$", "", s)  # pkg@1.2.3
    s = re.sub(r"\s*(?:==|>=|<=|~=|\^|~)\s*\d[\w.\-]*$", "", s)  # pkg==1.2
    return s.rstrip(".").strip()


@dataclass(frozen=True)
class Pick:
    vendor: str | None
    raw: str
    how: str  # exact | cross | contains | unmatched | empty | missing


class Matcher:
    def __init__(self, ws: Workspace):
        self.ws = ws
        self.by_cat: dict = {}
        self.global_alias: dict = {}
        for v in ws.vendors.values():
            names = {canon(a) for a in v.aliases} | {canon(v.name), canon(v.id)}
            for alias in names:
                if not alias:
                    continue
                self.global_alias.setdefault(alias, set()).add(v.id)
                for cat in v.categories:
                    self.by_cat.setdefault(cat, {})[alias] = v.id
        self.contains = {
            cat: sorted(((a, vid) for a, vid in table.items() if len(a) >= 3), key=lambda x: -len(x[0]))
            for cat, table in self.by_cat.items()
        }

    def candidates(self, c: str) -> list:
        out = [c]
        inner = re.findall(r"\(([^)]*)\)", c)
        outer = re.sub(r"\([^)]*\)", " ", c).strip()
        for piece in [outer, *inner]:
            piece = re.sub(r"\s+", " ", piece).strip()
            if piece and piece not in out:
                out.append(piece)
            for part in SPLIT.split(piece):
                part = part.strip()
                if part and part not in out:
                    out.append(part)
        return out

    def match(self, category: str, raw) -> Pick:
        if raw is None:
            return Pick(None, "", "missing")
        c = canon(raw)
        if c in EMPTY:
            return Pick(None, str(raw), "empty")
        table = self.by_cat.get(category, {})
        cands = self.candidates(c)
        hits = [table[cand] for cand in cands if cand in table]
        specific = [h for h in hits if not self.ws.vendors[h].generic]
        if specific:
            return Pick(specific[0], str(raw), "exact")
        for alias, vid in self.contains.get(category, []):
            if self.ws.vendors[vid].generic:
                continue
            if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", c):
                return Pick(vid, str(raw), "contains")
        if hits:
            return Pick(hits[0], str(raw), "exact")
        for cand in cands:
            hits = self.global_alias.get(cand)
            if hits and len(hits) == 1:
                return Pick(next(iter(hits)), str(raw), "cross")
        return Pick(None, str(raw), "unmatched")


def picks(ws: Workspace, records, matcher: Matcher | None = None):
    """Yield (record, category, Pick) for every item of every successful observation."""
    matcher = matcher or Matcher(ws)
    for rec in records:
        answer = rec.get("answer") or {}
        for item in rec.get("items", []):
            yield rec, item, matcher.match(item, answer.get(item))


def unmatched(ws: Workspace, records, limit: int = 200) -> list:
    counts: dict = {}
    for _rec, cat, pick in picks(ws, records):
        if pick.how in ("unmatched", "cross"):
            key = (cat, canon(pick.raw), pick.how, pick.vendor or "")
            counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
