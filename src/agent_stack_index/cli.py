"""asi: command line for the Agent Stack Index."""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from . import __version__, store
from .config import load, load_experiment, validate


def _exp(ws, ref: str):
    path = Path(ref)
    if not path.suffix:
        path = ws.root / "experiments" / f"{ref}.toml"
    return load_experiment(path)


def cmd_validate(ws, args) -> int:
    problems = validate(ws)
    for p in problems:
        print(f"problem: {p}")
    print(f"{len(ws.models)} models · {len(ws.categories)} categories · {len(ws.vendors)} vendors · {len(ws.tasks)} tasks · {len(problems)} problems")
    return 1 if problems else 0


def cmd_models(ws, args) -> int:
    for m in ws.models.values():
        print(f"{'on ' if m.enabled else 'off'} {m.id:<22} {m.lab:<10} route={m.route!r} provider={m.provider} max_concurrency={m.max_concurrency}")
    return 0


def cmd_plan(ws, args) -> int:
    from .plan import plan, shard

    exp = _exp(ws, args.experiment)
    trials = shard(plan(ws, exp), args.shard)
    done = store.done_ids(ws.root, exp.id)
    per = Counter(t.model_id for t in trials if t.trial_id not in done)
    print(f"{exp.id}: {len(trials)} trials · {sum(1 for t in trials if t.trial_id in done)} done · {sum(per.values())} pending")
    for model_id, n in sorted(per.items()):
        print(f"  {model_id:<22} {n} pending")
    if args.show:
        print(trials[0].prompt if trials else "(no trials)")
    return 0


def cmd_run(ws, args) -> int:
    from .providers import FakeClient, HttpClient
    from .runner import run

    exp = _exp(ws, args.experiment)
    if args.fake:
        client = FakeClient(lambda model, prompt: "{" + ", ".join(f'"{k}": "fake-{k}"' for k in re.findall(r"^- ([a-z_]+):", prompt, re.M)) + "}")
    else:
        client = HttpClient(ws)
    stats = run(ws, exp, client, max_calls=args.max_calls, shard_spec=args.shard, workers=args.workers, retry_failed=not args.no_retry)
    print(stats)
    return 0 if stats["error"] == 0 else 2


def cmd_unmatched(ws, args) -> int:
    from .normalize import unmatched

    records = store.latest_ok(store.read(ws.root, set(args.experiment) if args.experiment else None)).values()
    for (cat, raw, how, vendor), n in unmatched(ws, records, args.limit):
        print(f"{n:>4}  {cat:<22} {how:<9} {raw!r}" + (f" -> {vendor}" if vendor else ""))
    return 0


def cmd_release(ws, args) -> int:
    from .release import write

    drift = write(ws, args.release, check=args.check)
    if args.check:
        if drift:
            print(f"release {args.release} is stale: {', '.join(drift)} (run `asi release {args.release}`)")
            return 1
        print(f"release {args.release} is up to date")
        return 0
    print(f"wrote releases/{args.release}/ (results.json, picks.csv, REPORT.md)")
    return 0


def cmd_site(ws, args) -> int:
    from .site import build

    print(build(ws, Path(args.out), args.release))
    return 0


def cmd_audit(ws, args) -> int:
    from .audit import plan_spec, snapshot

    if args.vendor not in ws.vendors:
        print(f"unknown vendor {args.vendor}")
        return 1
    if args.plan:
        print(plan_spec(ws, args.vendor, args.release, args.tag, Path(args.out) if args.out else None))
        return 0
    text = snapshot(ws, args.vendor, args.release)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(args.out)
    else:
        print(text)
    return 0


def cmd_new_release(ws, args) -> int:
    """Scaffold a monthly release by copying the previous month's experiment specs under new ids."""
    from .release import spec

    prev = spec(ws, args.previous)
    out_dir = ws.root / "releases" / args.release
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [f'id = "{args.release}"', f'title = "Agent Stack Index — {args.release}"']
    for role in ("baseline", "duel"):
        if prev.get(role):
            old = ws.root / "experiments" / f"{prev[role]}.toml"
            new_id = prev[role].replace(args.previous, args.release)
            text = old.read_text(encoding="utf-8").replace(f'id = "{prev[role]}"', f'id = "{new_id}"')
            (ws.root / "experiments" / f"{new_id}.toml").write_text(text, encoding="utf-8")
            lines.append(f'{role} = "{new_id}"')
    (out_dir / "release.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"scaffolded releases/{args.release}; run the experiments, then `asi release {args.release}`")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="asi", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("models")
    sp = sub.add_parser("plan")
    sp.add_argument("experiment")
    sp.add_argument("--shard")
    sp.add_argument("--show", action="store_true", help="print the first rendered prompt")
    sr = sub.add_parser("run")
    sr.add_argument("experiment")
    sr.add_argument("--max-calls", type=int)
    sr.add_argument("--shard", help="i/n: run only this shard of the trials")
    sr.add_argument("--workers", type=int, default=64, help="cap on in-flight calls per provider")
    sr.add_argument("--no-retry", action="store_true", help="skip trials that already failed once")
    sr.add_argument("--fake", action="store_true", help="use a deterministic fake model (pipeline test)")
    su = sub.add_parser("unmatched")
    su.add_argument("--experiment", action="append")
    su.add_argument("--limit", type=int, default=80)
    sl = sub.add_parser("release")
    sl.add_argument("release")
    sl.add_argument("--check", action="store_true")
    ss = sub.add_parser("site")
    ss.add_argument("--release")
    ss.add_argument("--out", default="_site")
    sa = sub.add_parser("audit")
    sa.add_argument("--vendor", required=True)
    sa.add_argument("--release")
    sa.add_argument("--plan", action="store_true")
    sa.add_argument("--tag", default="baseline")
    sa.add_argument("--out")
    sn = sub.add_parser("new-release")
    sn.add_argument("release")
    sn.add_argument("--from", dest="previous", required=True)
    args = p.parse_args(argv)
    ws = load()
    handler = globals()[f"cmd_{args.cmd.replace('-', '_')}"]
    return handler(ws, args)


if __name__ == "__main__":
    sys.exit(main())
