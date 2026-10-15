"""Turn a model's free text into {item_key: raw_choice_string}. No interpretation happens here."""
from __future__ import annotations

import json
import re

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S | re.I)


def _objects(text: str):
    """Yield every balanced top-level {...} span, in order of appearance."""
    depth, start, in_str, escape = 0, None, False, False
    for i, ch in enumerate(text):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                yield text[start : i + 1]
                start = None


def _key(k: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(k).lower()).strip("_")


def _value(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        return v.strip() or None
    if isinstance(v, (list, tuple)):
        return _value(v[0]) if v else None
    if isinstance(v, dict):
        for name in ("name", "package", "service", "choice", "tool", "library", "pick"):
            if name in v:
                return _value(v[name])
        return _value(next(iter(v.values()), None))
    return str(v)


def parse_answer(text: str, items) -> dict | None:
    """Best JSON object in the text, keyed by expected item ids. None when nothing usable."""
    items = list(items)
    wanted = {_key(i): i for i in items}
    candidates = []
    for chunk in FENCE.findall(text or "") + list(_objects(text or "")):
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            candidates.append(obj)
    best, best_hits = None, 0
    for obj in candidates:
        mapped = {}
        for k, v in obj.items():
            key = _key(k)
            item = wanted.get(key)
            if item is None:
                item = next((orig for norm, orig in wanted.items() if norm in key or key in norm), None)
            if item and item not in mapped:
                mapped[item] = _value(v)
        hits = sum(1 for v in mapped.values() if v)
        if hits > best_hits:
            best, best_hits = mapped, hits
    if not best:
        if len(items) == 1 and text and len(text.strip()) <= 80 and "{" not in text:
            return {items[0]: text.strip().strip("`\"' ")}
        return None
    return {item: best.get(item) for item in items}
