# Agent Stack Index

**Which libraries and hosted services do AI coding models pick when they start a project from scratch, and what changes the pick?**

Live report: **https://brickerp.github.io/agent-stack-index/** · Latest release: [`releases/2026-10/REPORT.md`](releases/2026-10/REPORT.md)

## October 2026, in short

10 models from 8 labs, 29 categories, 2,670 answers ([data](releases/2026-10/results.json)). This release is a **pilot**: its design was not pre-registered, so every finding is exploratory ([protocol](protocols/2026-10.md)).

- **Most categories already have a default.** In 12 of 29, every model picks the same tool and it takes at least 95% of the answers: Neon (Postgres hosting), Stripe, Sentry, BullMQ, PostHog analytics, Vercel hosting, Playwright, FastAPI, SQLAlchemy, Celery, Resend, Redis. In 7 more, at least 8 of 10 models agree.
- **Without a default, the pick also moves with the wording.** In the 10 contested categories, 31 of 100 model–category pairs change their top pick when the request is reworded, against about 17 expected from sampling noise alone; in the 12 settled categories, none do.
- **What the model reads can decide the pick.** With only one candidate's notes in context, models pick that candidate 85–100% of the time, including tools they never pick unprompted (Trigger.dev 0% → 90%, Postmark 0% → 100%, SendGrid 0% → 90%); that is close to a forced choice.
- **Side by side, we detected no shift in four of five duels** (with 30 and 60 answers per arm, shifts under about 19–30 points cannot be ruled out). Authentication, which has no default, flipped: Better Auth goes from 17% to 52% when Better Auth, Clerk and Auth.js notes are all in context. The first-listed candidate won 43% of side-by-side picks (a third expected).
- **Splits worth watching:** authentication (Auth.js 52%, Better Auth 24%, Clerk 24%), UI components (MUI, Ant Design, shadcn/ui), vector databases, Python auth, pipeline orchestration.
- **Own-lab preference:** asked for an LLM provider, Claude Opus 5.5 names Anthropic every time; every other model's top pick is OpenAI, including Gemini (Google 8%).

These are stated preferences from direct API questions. A first [ask-vs-do pilot](docs/pilots/2026-10-agent-probe.md) ran Claude Code on the SaaS-starter task five times with file tools only: it wrote `next-auth` into `package.json` in all five runs where the same model, asked through a different harness, named Better Auth, and it left the database host unchosen. The pilot did not install dependencies or execute or test the generated app, and it does not establish why the harnesses differed or compare library quality. Read the [methodology and limitations](docs/METHODOLOGY.md) before quoting a number.

## How it works

```
inputs (reviewed text)  →  plan (content-addressed trials)  →  run (resumable)  →  raw answers (append-only JSONL)
                                                                                     ↓ catalog matching
                                                         releases (JSON, CSV, report)  →  site · vendor audits
```

- **Two probes.** *Ask*: a build task plus a list of needs, answered as JSON, in three phrasings with repeats. *Duel*: one need, with no notes, all candidates' notes in rotated order, or one candidate's notes alone.
- **Collection is separate from interpretation.** Answers are stored verbatim; a public [catalog](catalog/) maps them to vendors later, so catalog fixes never require new model calls.
- **Releases are reproducible.** CI regenerates every release from raw data and fails on drift.
- **Experiments are planned in writing.** Each release has a [protocol](protocols/) with its goal, hypotheses, design and analysis plan; a confirmatory one is locked before data exists, and the report labels every finding confirmed, not detected or exploratory. See the [charter](docs/CHARTER.md).
- Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · plans: [docs/ROADMAP.md](docs/ROADMAP.md)

## Run it

Python 3.11+, no dependencies. Any OpenAI-compatible endpoint works.

```bash
export PYTHONPATH=src ASI_GATEWAY_BASE_URL=https://your-gateway/v1 ASI_GATEWAY_API_KEY=...
python -m agent_stack_index validate                 # inputs and protocols are consistent
python -m agent_stack_index lock 2026-11             # freeze a confirmatory protocol before any data
python -m agent_stack_index plan 2026-10-baseline    # what would run
python -m agent_stack_index run 2026-10-baseline     # resumable; only missing trials execute
python -m agent_stack_index release 2026-10          # regenerate results.json, picks.csv, REPORT.md
python -m agent_stack_index site --out _site         # static report
python -m agent_stack_index share                    # Open Graph card and thread images (needs Chrome; set CHROME to its path)
python -m unittest discover -s tests                 # offline tests with a fake model
```

## Extend it

| To add | Edit | Then |
|---|---|---|
| A model | `config/models.toml` | `run` the month's experiments; only new trials execute |
| A vendor or alias | `catalog/vendors/*.toml` | `release <id>`; the diff shows every number that moved |
| A task or phrasing | `tasks/tasks.toml`, `prompts/prompts.toml` | new trials appear in `plan` |
| A duel | `experiments/*-duel.toml` + notes in `contexts/public/` | `run`, `release` |
| A monthly release | `asi new-release 2026-11 --from 2026-10` | write `protocols/2026-11.md`, `validate`, `lock`, then `run`, `release`, `share`, push |

## Repository layout

```
config/models.toml        model registry (routes, labs, concurrency); secrets come from env vars
catalog/                  categories and vendors with aliases (package and product names)
tasks/ prompts/           build tasks and prompt phrasings
contexts/public/          neutral, equal-length vendor notes used in duels
experiments/              declarative experiment specs
data/observations/        raw answers, one JSONL file per experiment and model
protocols/                one protocol per release (goal, hypotheses, design, analysis plan) and its lock
releases/<id>/            release.toml (+ [analysis] thresholds), derived results.json, picks.csv, REPORT.md, share/
src/agent_stack_index/    the engine (plan, run, normalize, analyze, infer, protocol, story, release, site, share, audit)
```

## Independence

No vendor pays for inclusion, placement or early access, and duel notes are written by the maintainer from public documentation. The maintainer, [Yupeng Lu](https://brickerp.github.io/), separately helps developer-tool teams become agent-ready (docs, MCP servers, integration tests) using the same open method on private runs; that work never changes the public index.

## License

Code: MIT. Data in `data/` and `releases/`: CC BY 4.0, cite as "Agent Stack Index, release 2026-10".
