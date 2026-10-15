"""Pilot of the agent probe: does what a model *says* it would use match what a real agent *writes*?

Runs Claude Code headless in empty, isolated workspaces (temporary HOME, no user settings, no hooks,
no shell or web tools), asks it to scaffold the same SaaS starter as the `ts-saas-starter` task, then
reads the dependencies it wrote into package.json and maps them to catalog vendors.

    PYTHONPATH=src python scripts/agent_probe_pilot.py --runs 5 --model "Opus 5.5"

Needs ASI_GATEWAY_ANTHROPIC_URL (Anthropic-compatible base URL) and ASI_GATEWAY_API_KEY.
Writes docs/pilots/<date>-agent-probe.json. Workspaces are deleted afterwards.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import date
from pathlib import Path

from agent_stack_index.config import load
from agent_stack_index.normalize import Matcher

TASK = ("Scaffold a new Next.js (TypeScript) SaaS starter in the current directory: user accounts with email login, "
        "a Postgres database, subscription billing, transactional email, and error monitoring. Create package.json with "
        "the dependencies you would actually use, plus minimal source files wiring each one up. Do not run any commands; "
        "only create files.")
ITEMS = ["auth", "database_host", "orm", "payments", "transactional_email", "error_monitoring"]


def one(run: int, model: str, timeout: int) -> dict:
    work = Path(tempfile.mkdtemp(prefix="asi-agent-"))
    home = Path(tempfile.mkdtemp(prefix="asi-home-"))
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "ANTHROPIC_BASE_URL": os.environ["ASI_GATEWAY_ANTHROPIC_URL"],
        "ANTHROPIC_AUTH_TOKEN": os.environ["ASI_GATEWAY_API_KEY"],
        "ANTHROPIC_SMALL_FAST_MODEL": os.environ.get("ASI_SMALL_MODEL", "Claude Haiku 4.5"),
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }
    cmd = ["claude", "-p", TASK, "--model", model, "--bare", "--setting-sources", "", "--permission-mode", "acceptEdits",
           "--allowedTools", "Write,Edit,Read,Glob", "--disallowedTools", "Bash,WebFetch,WebSearch,Task",
           "--max-turns", "40", "--output-format", "json"]
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=timeout)
        meta = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {"raw": proc.stdout[-400:], "stderr": proc.stderr[-400:]}
    except subprocess.TimeoutExpired:
        meta = {"error": "timeout"}
    pkg = work / "package.json"
    deps = {}
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        except json.JSONDecodeError:
            meta["package_json"] = "invalid"
    env_text = " ".join(p.read_text(errors="ignore") for p in work.rglob(".env*") if p.is_file())
    files = sorted(str(p.relative_to(work)) for p in work.rglob("*") if p.is_file())
    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(home, ignore_errors=True)
    match = re.search(r'DATABASE_URL\s*=\s*"?[a-z+]+://[^@\s]*@?([^/:\s"]+)', env_text)
    return {"run": run, "seconds": round(time.monotonic() - started), "deps": sorted(deps), "env": env_text[:2000],
            "database_url_host": match.group(1) if match else None,
            "files": len(files), "turns": meta.get("num_turns"), "is_error": meta.get("is_error"), "error": meta.get("error") or meta.get("stderr")}


def picks(ws, result: dict) -> dict:
    m = Matcher(ws)
    out = {}
    for item in ITEMS:
        hits = [m.match(item, d) for d in result["deps"]]
        named = [h.vendor for h in hits if h.vendor and h.how in ("exact", "contains") and not ws.vendors[h.vendor].generic
                 and item in ws.vendors[h.vendor].categories]
        if item == "database_host" and not named:
            for host, vendor in (("neon.tech", "neon"), ("supabase.co", "supabase"), ("psdb.cloud", "planetscale")):
                if host in result["env"]:
                    named = [vendor]
        out[item] = named[0] if named else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--model", default="Opus 5.5")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    ws = load()
    out = ws.root / "docs" / "pilots" / f"{date.today().isoformat()}-agent-probe.json"
    previous = []
    if out.exists():
        old = json.loads(out.read_text())
        if old.get("model") == args.model and old.get("task") == TASK:
            previous = old["results"]
    offset = len(previous)
    with cf.ThreadPoolExecutor(max_workers=args.runs) as pool:
        results = list(pool.map(lambda r: one(offset + r, args.model, args.timeout), range(args.runs)))
    for r in results:
        r["picks"] = picks(ws, r)
        r.pop("env", None)  # generated .env files are not published; only the database host is kept
    results = previous + results
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"agent": "claude-code", "model": args.model, "task": TASK, "results": results}, indent=1) + "\n")
    for r in results:
        print(r["run"], r["seconds"], "s", r["turns"], "turns", r["picks"], (r["error"] or "")[:120] if r["is_error"] or r["error"] else "")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
