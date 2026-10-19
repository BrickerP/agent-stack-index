# Architecture

Four layers, each a pure function of the one below it plus versioned text inputs.

```
inputs (text, reviewed in PRs)        collection (local, needs a model API)     derived (CI-reproducible)
config/models.toml   ─┐
catalog/*.toml        │                                                         releases/<id>/results.json
tasks/tasks.toml      ├─► plan ─► trials ─► run ─► data/observations/*.jsonl ─► releases/<id>/picks.csv  ─► site (Pages)
prompts/prompts.toml  │   (content-addressed,     (append-only raw answers)     releases/<id>/REPORT.md  ─► audit (vendor)
contexts/public/*.md  │    resumable)
experiments/*.toml   ─┘
```

## Design rules

1. **Collection is separate from interpretation.** Raw answers are stored verbatim and never edited. Vendor matching and statistics run later, so improving the catalog never requires calling a model again.
2. **Trials are content-addressed.** A trial id hashes the experiment, task, phrasing, model, repeat, duel arm and the rendered prompt. Re-running an experiment executes only missing trials; editing a prompt or a context creates new trials instead of silently mixing answers to different questions.
3. **Releases are derived.** `asi release <id>` regenerates `results.json`, `picks.csv` and `REPORT.md` from raw data and the current catalog. CI runs `--check` and fails on drift, so a catalog edit shows up as a reviewable diff in every affected release. The share images are rendered by `asi share` (needs Chrome) from the same results and are committed; CI does not re-render them, so run it after `release`.
4. **Secrets live in the environment.** `config/models.toml` names environment variables for base URLs and keys; nothing secret or internal is committed.
5. **No runtime dependencies.** Standard-library Python 3.11+, so CI and new machines need nothing but Python.

## Code map (`src/agent_stack_index/`)

| Module | Role |
|---|---|
| `config.py` | Load and validate all inputs into dataclasses |
| `plan.py` | Expand an experiment into trials; prompt rendering; sharding |
| `providers.py` | HTTP adapters (`openai_chat`, `openai_responses`, `anthropic_messages`), retries, fake client |
| `runner.py` | Concurrent, resumable execution with per-model and per-provider limits |
| `store.py` | Append-only JSONL, partitioned by experiment and model |
| `parse.py` | Extract the JSON answer from free text |
| `normalize.py` | Map raw answers to catalog vendors, scoped by category |
| `analyze.py` | Shares, Wilson intervals, pooling, agreement, duel effects |
| `release.py`, `report.py`, `site.py` | Derived artifacts: JSON, CSV, Markdown, static HTML |
| `story.py`, `narrative.py` | The claims a release makes, computed from its own numbers, and the sentences rendered from them; shared by the Markdown report, the site and the share images |
| `share.py` | Open Graph card and thread images: HTML rendered from the story, PNG via headless Chrome |
| `audit.py` | Vendor snapshot and re-test experiment specs (commercial engine) |

## Operating it

```bash
export PYTHONPATH=src ASI_GATEWAY_BASE_URL=... ASI_GATEWAY_API_KEY=...
python -m agent_stack_index validate
python -m agent_stack_index plan 2026-10-baseline          # trial counts, nothing executed
python -m agent_stack_index run 2026-10-baseline           # resumable; --shard 0/4 to split machines
python -m agent_stack_index unmatched                      # curate catalog aliases
python -m agent_stack_index release 2026-10                # regenerate derived artifacts
python -m agent_stack_index site --out _site               # local preview of the Pages site
python -m agent_stack_index share                          # Open Graph card and thread images (CHROME=/path if not found)
```

- **New model:** add a `[models.<id>]` table, run the month's experiments again; only the new model's trials execute. Retire with `enabled = false`.
- **New vendor or alias:** edit `catalog/vendors/*.toml`, run `asi release <id>` for affected releases, commit the diff.
- **New task, phrasing or duel:** edit the inputs; new trials appear in `asi plan`.
- **Monthly release:** `asi new-release 2026-11 --from 2026-10` copies the specs under new ids; run, release, share, push. Pages redeploys from the latest release.
- **Scale:** raise `repeats` and per-model `max_concurrency`; split work with `--shard i/n` across machines and merge `data/` (files are append-only and per model, so merges do not conflict within a shard).

## Commercial layer

The public repository holds the method, the public data and the engine. Client work (custom duels with a vendor's real docs, before/after re-tests, reports) runs the same engine from a private workspace: `asi audit --vendor <id> --plan --out <private path>` writes the spec, and `ASI_ROOT` points the CLI at the private workspace. `clients/` and `audits/private/` are git-ignored here.
