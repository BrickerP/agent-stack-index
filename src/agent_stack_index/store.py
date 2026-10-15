"""Append-only JSONL storage, partitioned by experiment and model.

Raw observations are never edited. Re-running a trial appends a new line; readers take the last
successful line per trial id. Interpretation (vendor matching) is derived later, so improving the
catalog never requires calling a model again.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

_LOCK = threading.Lock()


def obs_dir(root: Path) -> Path:
    return root / "data" / "observations"


def obs_path(root: Path, experiment: str, model_id: str) -> Path:
    return obs_dir(root) / experiment / f"{model_id}.jsonl"


def append(root: Path, record: dict) -> None:
    path = obs_path(root, record["experiment"], record["model_id"])
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()


def read(root: Path, experiments=None):
    base = obs_dir(root)
    if not base.exists():
        return
    for exp_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if experiments and exp_dir.name not in experiments:
            continue
        for path in sorted(exp_dir.glob("*.jsonl")):
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        yield json.loads(line)


def latest_ok(records) -> dict:
    """trial_id -> the last successful observation for that trial."""
    best: dict = {}
    for rec in records:
        if rec.get("ok"):
            best[rec["trial_id"]] = rec
    return best


def done_ids(root: Path, experiment: str) -> set:
    return set(latest_ok(read(root, {experiment})))
