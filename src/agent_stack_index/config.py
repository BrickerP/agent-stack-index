"""Load and validate the declarative inputs: models, catalog, tasks, prompts, experiments.

Everything that defines a measurement lives in versioned text files; code only reads them.
"""
from __future__ import annotations

import hashlib
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def root_dir() -> Path:
    return Path(os.environ.get("ASI_ROOT", DEFAULT_ROOT)).resolve()


@dataclass(frozen=True)
class Provider:
    id: str
    kind: str
    base_url_env: str
    api_key_env: str
    max_concurrency: int = 8
    timeout_s: float = 180.0


@dataclass(frozen=True)
class Model:
    id: str
    provider: str
    route: str
    lab: str
    label: str
    enabled: bool = True
    max_concurrency: int = 4
    params: dict = field(default_factory=dict)
    notes: str = ""
    injected_prompt: bool = False  # the route adds a system prompt we cannot see; flagged in reports


@dataclass(frozen=True)
class Category:
    id: str
    label: str
    hint: str
    group: str


@dataclass(frozen=True)
class Vendor:
    id: str
    name: str
    categories: tuple
    aliases: tuple
    url: str = ""
    products: dict = field(default_factory=dict)
    generic: bool = False  # catch-all answers such as "Postgres" with no host named

    def product(self, category: str) -> str:
        return self.products.get(category, self.name)


@dataclass(frozen=True)
class Task:
    id: str
    stack: str
    text: str
    items: tuple
    baseline: bool = True


@dataclass(frozen=True)
class Duel:
    task: str
    category: str
    vendors: tuple


@dataclass(frozen=True)
class Analysis:
    """Analysis parameters of one release. For a confirmatory protocol they are locked before any data exists."""
    default_share: float = 0.95  # a category is settled when every model's top pick is the pooled one and takes this share
    leaning_agree: float = 0.8  # leaning: at least this fraction of models agree ...
    leaning_share: float = 0.5  # ... and the pick takes more than this share of answers
    alpha: float = 0.05  # family-wise level for the duel contrasts (Holm) and the wording shuffle test
    min_effect_points: int = 10  # a shift smaller than this is not reported as an effect, even when significant
    shuffles: int = 1000  # label shuffles for the wording null
    seed: int = 1


@dataclass(frozen=True)
class Experiment:
    id: str
    probe: str
    title: str
    path: Path
    models: tuple = ("*",)
    tasks: tuple = ("*",)
    variants: tuple = ("pick",)
    repeats: int = 1
    duels: tuple = ()
    arms: dict = field(default_factory=dict)


@dataclass
class Workspace:
    root: Path
    providers: dict
    models: dict
    categories: dict
    vendors: dict
    tasks: dict
    prompts: dict

    def context(self, category: str, vendor: str) -> str:
        path = self.root / "contexts" / "public" / category / f"{vendor}.md"
        return path.read_text(encoding="utf-8").strip()

    def enabled_models(self) -> list:
        return [m for m in self.models.values() if m.enabled]

    def catalog_sha(self) -> str:
        files = sorted((self.root / "catalog").rglob("*.toml"))
        digest = hashlib.sha256()
        for path in files:
            digest.update(path.relative_to(self.root).as_posix().encode())
            digest.update(path.read_bytes())
        return digest.hexdigest()[:12]


def _toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load(root: Path | None = None) -> Workspace:
    root = Path(root or root_dir())
    cfg = _toml(root / "config" / "models.toml")
    providers = {pid: Provider(id=pid, **spec) for pid, spec in cfg.get("providers", {}).items()}
    models = {mid: Model(id=mid, **spec) for mid, spec in cfg.get("models", {}).items()}
    cats = _toml(root / "catalog" / "categories.toml").get("category", [])
    categories = {c["id"]: Category(**c) for c in cats}
    vendors: dict = {}
    for path in sorted((root / "catalog" / "vendors").glob("*.toml")):
        for spec in _toml(path).get("vendor", []):
            spec = dict(spec)
            spec["categories"] = tuple(spec["categories"])
            spec["aliases"] = tuple(spec.get("aliases", ()))
            if spec["id"] in vendors:
                raise ValueError(f"duplicate vendor id {spec['id']} in {path.name}")
            vendors[spec["id"]] = Vendor(**spec)
    tasks = {}
    for spec in _toml(root / "tasks" / "tasks.toml").get("task", []):
        spec = dict(spec)
        spec["items"] = tuple(spec["items"])
        tasks[spec["id"]] = Task(**spec)
    prompts = _toml(root / "prompts" / "prompts.toml")
    return Workspace(root, providers, models, categories, vendors, tasks, prompts)


def load_experiment(path: Path) -> Experiment:
    spec = _toml(path)
    duels = tuple(Duel(d["task"], d["category"], tuple(d["vendors"])) for d in spec.get("duel", []))
    return Experiment(
        id=spec["id"],
        probe=spec["probe"],
        title=spec.get("title", spec["id"]),
        path=path,
        models=tuple(spec.get("models", ["*"])),
        tasks=tuple(spec.get("tasks", ["*"])),
        variants=tuple(spec.get("variants", ["pick"])),
        repeats=int(spec.get("repeats", 1)),
        duels=duels,
        arms=dict(spec.get("arms", {})),
    )


def experiments(root: Path) -> list:
    return [load_experiment(p) for p in sorted((root / "experiments").glob("*.toml"))]


def validate(ws: Workspace) -> list:
    """Return human-readable problems; an empty list means the inputs are consistent."""
    problems = []
    for m in ws.models.values():
        if m.provider not in ws.providers:
            problems.append(f"model {m.id}: unknown provider {m.provider}")
    for t in ws.tasks.values():
        for item in t.items:
            if item not in ws.categories:
                problems.append(f"task {t.id}: unknown category {item}")
    seen: dict = {}
    for v in ws.vendors.values():
        for cat in v.categories:
            if cat not in ws.categories:
                problems.append(f"vendor {v.id}: unknown category {cat}")
        for cat in v.products:
            if cat not in v.categories:
                problems.append(f"vendor {v.id}: product for unlisted category {cat}")
        for alias in v.aliases:
            for cat in v.categories:
                key = (cat, alias.strip().lower())
                if key in seen and seen[key] != v.id:
                    problems.append(f"alias '{alias}' in {cat} maps to both {seen[key]} and {v.id}")
                seen[key] = v.id
    for exp in experiments(ws.root):
        for d in exp.duels:
            if d.task not in ws.tasks:
                problems.append(f"{exp.id}: duel task {d.task} missing")
            for vid in d.vendors:
                if vid not in ws.vendors:
                    problems.append(f"{exp.id}: duel vendor {vid} missing")
                elif not (ws.root / "contexts" / "public" / d.category / f"{vid}.md").exists():
                    problems.append(f"{exp.id}: context contexts/public/{d.category}/{vid}.md missing")
        for name in exp.variants:
            if name not in ws.prompts.get(exp.probe, {}):
                problems.append(f"{exp.id}: prompt variant {exp.probe}.{name} missing")
    from .protocol import problems as protocol_problems

    for path in sorted((ws.root / "releases").glob("*/release.toml")):
        problems += protocol_problems(ws, path.parent.name)
    return problems
