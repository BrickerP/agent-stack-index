# Pilot: does "ask" agree with "do"? (2026-10-15)

The index asks models what they would use. This pilot checks that against what a real coding agent writes when it does the job.

**Setup.** Claude Code, headless, model route `Opus 5.5` through the same gateway as the index. Each run starts in an empty directory with a temporary home (no user settings, hooks, memory or MCP servers), file tools only (no shell, no web), and the task of `ts-saas-starter`: scaffold a Next.js SaaS with email login, Postgres, subscription billing, transactional email and error monitoring, writing `package.json` and minimal wiring. The pilot did not install dependencies or execute or test the generated app. Dependencies written into `package.json` are mapped to vendors with the public catalog. Script: [`scripts/agent_probe_pilot.py`](../../scripts/agent_probe_pilot.py); raw results: [`2026-10-15-agent-probe.json`](2026-10-15-agent-probe.json).

**Result (5 runs, 238–334 s and 26–32 turns each).**

| Need | Asked (Claude Opus 5.5, 12 answers) | Done (Claude Code + Opus 5.5, 5 runs) |
|---|---|---|
| Auth | Better Auth 12/12 | **Auth.js** (`next-auth` + `@auth/drizzle-adapter`) 5/5 |
| Postgres hosting | Neon 12/12 | **none named**: `postgres` driver, `DATABASE_URL` on localhost, 5/5 |
| ORM | Drizzle 12/12 | Drizzle 5/5 |
| Billing | Stripe 12/12 | Stripe 5/5 |
| Email | Resend 12/12 | Resend 5/5 |
| Monitoring | Sentry 12/12 | Sentry 5/5 |

**Reading.** Four of six rows have the same named package or service. The auth row differs: all five generated `package.json` files contain `next-auth` and `@auth/drizzle-adapter`, while the 12 direct API answers name Better Auth. The Postgres-hosting row remains unspecified in the generated files. The API questions and Claude Code runs use different harnesses and system prompts, so this pilot does not identify why the outputs differ, establish a causal choice, or compare library quality or completeness.

**Limits.** One agent, one model, one task, five runs. Claude Code adds its own system prompt and the gateway route adds another. The next releases extend this to more agents (Codex, opencode), more tasks, and an "allow the shell" arm.
