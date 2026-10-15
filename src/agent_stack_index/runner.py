"""Execute planned trials concurrently, resumably, with per-model and per-provider limits."""
from __future__ import annotations

import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from . import SCHEMA_VERSION, __version__, store
from .config import Experiment, Workspace
from .parse import parse_answer
from .plan import Trial, plan, shard
from .providers import ProviderError


def harness_version(ws: Workspace) -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ws.root, capture_output=True, text=True, timeout=5)
        return f"{__version__}+{rev.stdout.strip()}" if rev.returncode == 0 else __version__
    except (OSError, subprocess.SubprocessError):
        return __version__


def pending(ws: Workspace, exp: Experiment, shard_spec: str | None = None, retry_failed: bool = True) -> list:
    trials = shard(plan(ws, exp), shard_spec)
    done = store.done_ids(ws.root, exp.id)
    if not retry_failed:
        tried = {r["trial_id"] for r in store.read(ws.root, {exp.id})}
        done |= tried
    return [t for t in trials if t.trial_id not in done]


USAGE_KEYS = ("prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens", "reasoning_tokens")


def clean_usage(usage: dict) -> dict:
    """Keep provider-neutral token counts only; gateways add billing and routing fields we do not publish."""
    usage = usage or {}
    out = {k: int(usage[k]) for k in USAGE_KEYS if isinstance(usage.get(k), (int, float))}
    details = usage.get("completion_tokens_details") or usage.get("output_tokens_details") or {}
    if "reasoning_tokens" not in out and isinstance(details.get("reasoning_tokens"), (int, float)):
        out["reasoning_tokens"] = int(details["reasoning_tokens"])
    return out


def _record(ws, exp, trial: Trial, version, *, ok, error=None, completion=None, answer=None) -> dict:
    model = ws.models[trial.model_id]
    rec = {
        "schema": SCHEMA_VERSION,
        "trial_id": trial.trial_id,
        "experiment": exp.id,
        "probe": trial.probe,
        "task_id": trial.task_id,
        "items": list(trial.items),
        "variant": trial.variant,
        "arm": trial.arm,
        "order": list(trial.order),
        "model_id": trial.model_id,
        "route": model.route,
        "repeat": trial.repeat,
        "prompt_sha": trial.prompt_sha,
        "prompt": trial.prompt,
        "ok": ok,
        "error": error,
        "answer": answer,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "harness": version,
    }
    if completion is not None:
        rec.update(
            text=completion.text[:4000],
            reported_model=completion.reported_model,
            usage=clean_usage(completion.usage),
            finish_reason=completion.finish_reason,
            latency_ms=completion.latency_ms,
            attempts=completion.attempts,
        )
    return rec


def interleave(trials) -> list:
    """Round-robin across models so a slow model's queue never starves the worker pool."""
    by_model: dict = {}
    for t in trials:
        by_model.setdefault(t.model_id, []).append(t)
    out, queues = [], list(by_model.values())
    while queues:
        queues = [q for q in queues if q]
        for q in queues:
            out.append(q.pop(0))
    return out


def run(ws: Workspace, exp: Experiment, client, *, max_calls=None, shard_spec=None, workers=64, retry_failed=True, log=print):
    """Each model gets its own worker pool sized by its max_concurrency, so slow models never hold
    threads that fast models could use; the provider semaphore caps total in-flight calls."""
    todo = interleave(pending(ws, exp, shard_spec, retry_failed))
    if max_calls is not None:
        todo = todo[: int(max_calls)]
    version = harness_version(ws)
    cap = max(1, workers)
    provider_locks = {p.id: threading.BoundedSemaphore(min(cap, p.max_concurrency)) for p in ws.providers.values()}
    stats = {"planned": len(todo), "ok": 0, "unparsed": 0, "error": 0, "tokens": 0}
    lock = threading.Lock()
    started = time.monotonic()

    def execute(trial: Trial):
        model = ws.models[trial.model_id]
        with provider_locks[model.provider]:
            try:
                completion = client.complete(model, trial.prompt)
            except ProviderError as exc:
                return _record(ws, exp, trial, version, ok=False, error=str(exc)[:300])
        answer = parse_answer(completion.text, trial.items)
        if answer is None:
            return _record(ws, exp, trial, version, ok=False, error="unparsed answer", completion=completion)
        return _record(ws, exp, trial, version, ok=True, completion=completion, answer=answer)

    by_model: dict = {}
    for t in todo:
        by_model.setdefault(t.model_id, []).append(t)
    pools = {m: ThreadPoolExecutor(max_workers=max(1, ws.models[m].max_concurrency), thread_name_prefix=m) for m in by_model}
    try:
        futures = [pools[m].submit(execute, t) for m, trials in by_model.items() for t in trials]
        for n, future in enumerate(as_completed(futures), 1):
            rec = future.result()
            store.append(ws.root, rec)
            with lock:
                if rec["ok"]:
                    stats["ok"] += 1
                elif rec["error"] == "unparsed answer":
                    stats["unparsed"] += 1
                else:
                    stats["error"] += 1
                usage = rec.get("usage") or {}
                stats["tokens"] += int(usage.get("total_tokens") or 0) or int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
            if n % 25 == 0 or n == len(todo):
                elapsed = time.monotonic() - started
                log(f"[{exp.id}] {n}/{len(todo)} done · ok {stats['ok']} · unparsed {stats['unparsed']} · error {stats['error']} · {elapsed:.0f}s")
    finally:
        for pool in pools.values():
            pool.shutdown(wait=True, cancel_futures=True)
    stats["seconds"] = round(time.monotonic() - started, 1)
    return stats
