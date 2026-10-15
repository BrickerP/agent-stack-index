"""Expand a declarative experiment into concrete, content-addressed trials.

A trial id is a hash of everything that defines the measurement (including the rendered prompt),
so re-running an experiment only executes what is missing, and editing a prompt or a context
naturally creates new trials instead of silently mixing old and new answers.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass

from .config import Experiment, Workspace


@dataclass(frozen=True)
class Trial:
    trial_id: str
    experiment: str
    probe: str
    task_id: str
    items: tuple
    variant: str
    model_id: str
    repeat: int
    arm: str
    order: tuple
    prompt: str
    prompt_sha: str


def sha(text: str, n: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def render_items(ws: Workspace, items) -> str:
    return "\n".join(f"- {cid}: {ws.categories[cid].hint}" for cid in items)


def render(template: str, **values) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out.strip() + "\n"


def resolve_models(ws: Workspace, wanted) -> list:
    if "*" in wanted:
        return [m.id for m in ws.enabled_models()]
    missing = [m for m in wanted if m not in ws.models]
    if missing:
        raise ValueError(f"unknown models: {missing}")
    return list(wanted)


def resolve_tasks(ws: Workspace, wanted) -> list:
    if "*" in wanted:
        return [t.id for t in ws.tasks.values() if t.baseline]
    missing = [t for t in wanted if t not in ws.tasks]
    if missing:
        raise ValueError(f"unknown tasks: {missing}")
    return list(wanted)


def _trial(exp, probe, task_id, items, variant, model_id, repeat, arm, order, prompt) -> Trial:
    prompt_sha = sha(prompt)
    key = json.dumps([exp.id, probe, task_id, variant, model_id, repeat, arm, list(order), prompt_sha])
    return Trial(sha(key), exp.id, probe, task_id, tuple(items), variant, model_id, repeat, arm, tuple(order), prompt, prompt_sha)


def plan_ask(ws: Workspace, exp: Experiment) -> list:
    trials = []
    for model_id in resolve_models(ws, exp.models):
        for task_id in resolve_tasks(ws, exp.tasks):
            task = ws.tasks[task_id]
            for variant in exp.variants:
                template = ws.prompts["ask"][variant]["template"]
                prompt = render(template, task=task.text, items=render_items(ws, task.items))
                for r in range(exp.repeats):
                    trials.append(_trial(exp, "ask", task_id, task.items, variant, model_id, r, "", (), prompt))
    return trials


def duel_arms(exp: Experiment, vendors) -> list:
    """(arm, order) pairs: a no-context control, shuffled all-candidate notes, and each candidate alone."""
    arms = []
    arms += [("none", ())] * int(exp.arms.get("none", 0))
    perms = list(itertools.permutations(vendors))
    arms += [("trio", perms[i % len(perms)]) for i in range(int(exp.arms.get("trio", 0)))]
    for vendor in vendors:
        arms += [(f"solo:{vendor}", (vendor,))] * int(exp.arms.get("solo", 0))
    return arms


def plan_duel(ws: Workspace, exp: Experiment) -> list:
    variant = exp.variants[0]
    template = ws.prompts["duel"][variant]["template"]
    trials = []
    for model_id in resolve_models(ws, exp.models):
        for duel in exp.duels:
            task = ws.tasks[duel.task]
            items = (duel.category,)
            counters: dict = {}
            for arm, order in duel_arms(exp, duel.vendors):
                notes = "\n\n".join(ws.context(duel.category, vendor) for vendor in order)
                block = f"Reference notes on some candidate tools:\n\n{notes}\n" if notes else ""
                prompt = render(template, task=task.text, items=render_items(ws, items), contexts=block)
                key = (arm, order)
                counters[key] = counters.get(key, -1) + 1
                trials.append(_trial(exp, "duel", task.id, items, variant, model_id, counters[key], arm, order, prompt))
    return trials


PLANNERS = {"ask": plan_ask, "duel": plan_duel}


def plan(ws: Workspace, exp: Experiment) -> list:
    if exp.probe not in PLANNERS:
        raise ValueError(f"{exp.id}: unknown probe {exp.probe}")
    return PLANNERS[exp.probe](ws, exp)


def shard(trials, spec: str | None) -> list:
    """Keep the trials owned by shard 'i/n' (stable across machines)."""
    if not spec:
        return list(trials)
    index, count = (int(x) for x in spec.split("/"))
    return [t for t in trials if int(t.trial_id, 16) % count == index]
