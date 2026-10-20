# AI coding models already have a default stack

*Agent Stack Index — October 2026*

We asked 10 models from 8 labs to start the same 16 projects from scratch and name one tool for each of 29 needs, in three phrasings, four times each (1,920 answers). Then we put neutral notes on competing tools in front of them 750 more times.

**Pilot.** The design was not pre-registered, so every finding below is exploratory. Each one is checked against a noise model; see Limits for how far it holds.

**Question.** Which tools do AI coding models pick when they start a project from scratch, and what moves the pick: the wording, the order of candidates, or documentation in context?

1. **Most categories already have a default.** In 12 of 29 categories every model picks the same tool and it takes at least 95% of the answers; in 7 more, at least 8 of 10 models agree. *(exploratory)*
2. **Without a default, the pick also moves with the wording.** In the 10 contested categories, 31 of 100 model–category pairs change their top pick when the request is reworded, against about 17 expected from sampling noise alone; in the default categories, none do. *(exploratory)*
3. **What the model reads can decide the pick.** With only one candidate's notes in context, models pick it 85–100% of the time. With all candidates' notes side by side, the favourite showed no detectable change in four of the five categories we tested (shifts under about 19–30 points cannot be ruled out); in authentication, which has no default, the lead flipped. *(exploratory)*

## 1. Most categories already have a default

Twelve categories are settled: every model picks the same tool and it takes at least 95% of the answers. Seven more lean one way: at least 8 of 10 models agree and the tool wins most answers. Ten are contested.

**Settled — every model, at least 95% of answers** (12)

| Category | Pick | Share | Models agreeing | Runner-up |
|---|---|---|---|---|
| App hosting | Vercel | 100% | 10/10 | — |
| Background jobs | BullMQ | 100% | 10/10 | — |
| End-to-end testing | Playwright | 100% | 10/10 | — |
| Error monitoring | Sentry | 100% | 10/10 | — |
| Postgres hosting | Neon | 100% | 10/10 | — |
| Product analytics | PostHog | 100% | 10/10 | — |
| Python background jobs | Celery | 100% | 10/10 | — |
| Python database layer | SQLAlchemy | 100% | 10/10 | — |
| Python web framework | FastAPI | 100% | 10/10 | — |
| Subscription billing | Stripe | 100% | 10/10 | — |
| Transactional email | Resend | 99% | 10/10 | Postmark 1% |
| Cache | Redis | 96% | 10/10 | Upstash Redis 2% |

**Leaning — at least 8 of 10 models agree** (7)

| Category | Pick | Share | Models agreeing | Runner-up |
|---|---|---|---|---|
| Headless CMS | Sanity | 90% | 10/10 | Contentful 8% |
| LLM SDK | Vercel AI SDK | 89% | 9/10 | OpenAI SDK 11% |
| Realtime | Liveblocks | 87% | 9/10 | Pusher 9% |
| File storage | Amazon S3 | 83% | 9/10 | Cloudflare R2 12% |
| LLM provider | OpenAI | 83% | 9/10 | Anthropic 16% |
| Search | Meilisearch | 77% | 9/10 | Elasticsearch 13% |
| Image delivery | Cloudinary | 64% | 8/10 | Cloudflare Images 13% |

**Contested** (10)

| Category | Pick | Share | Models agreeing | Runner-up |
|---|---|---|---|---|
| ORM / query builder | Drizzle ORM | 72% | 7/10 | Prisma 28% |
| Rate limiting | rate-limiter-flexible | 67% | 7/10 | express-rate-limit 31% |
| Feature flags | LaunchDarkly | 59% | 7/10 | PostHog 38% |
| Python agent framework | LangChain / LangGraph | 57% | 6/10 | LlamaIndex 42% |
| Unit testing | Vitest | 57% | 6/10 | Jest 42% |
| Pipeline orchestration | Apache Airflow | 54% | 6/10 | Prefect 42% |
| Authentication | Auth.js (NextAuth) | 52% | 5/10 | Better Auth 24% |
| UI components | MUI | 52% | 5/10 | Ant Design 38% |
| Vector database | Pinecone | 46% | 8/10 | Qdrant 25% |
| Python authentication | Auth0 | 42% | 6/10 | Authlib 27% |

## 2. Without a default, the pick moves with the model and the wording

Where no tool is settled, models split. In authentication, Auth.js (NextAuth) is the top pick of 5 models, Clerk of 3 and Better Auth of 2.

The same model's answer also depends on the wording: in contested categories, 31 of 100 model–category pairs change their top pick across the three phrasings. Shuffling the phrasing labels over the same answers gives 17 ± 3 (sampling noise alone), so the wording accounts for roughly 14 of the 100 (p = 0.001).

In leaning categories 7 of 70 change, against about 6 expected (no detectable wording effect); in default categories, none.

The split is not just the Claude Opus 5.5 and Claude Sonnet 5.5 routes, which add a hidden system prompt (see Limits): in 9 of 10 contested categories, at least one other model also disagrees with the pooled pick.

| Category | Top pick of how many models | Same pick when reworded |
|---|---|---|
| ORM / query builder | Drizzle ORM ×7 · Prisma ×3 | 8/10 |
| Rate limiting | rate-limiter-flexible ×7 · express-rate-limit ×3 | 9/10 |
| Feature flags | LaunchDarkly ×7 · PostHog ×3 | 9/10 |
| Python agent framework | LangChain / LangGraph ×6 · LlamaIndex ×4 | 8/10 |
| Unit testing | Vitest ×6 · Jest ×4 | 6/10 |
| Pipeline orchestration | Apache Airflow ×6 · Prefect ×5 | 3/10 |
| Authentication | Auth.js (NextAuth) ×5 · Clerk ×3 · Better Auth ×2 | 6/10 |
| UI components | MUI ×5 · Ant Design ×4 · shadcn/ui ×1 | 7/10 |
| Vector database | Pinecone ×8 · Chroma ×1 · pgvector ×1 · Qdrant ×1 | 6/10 |
| Python authentication | Auth0 ×6 · Authlib ×3 · Roll-your-own (JWT / sessions) ×1 · FastAPI Users ×1 | 7/10 |

A model tied between two tools counts for both. Per-model picks are in the appendix.

## 3. What the model reads can decide the pick

In five duels we gave the same single-need task three ways: no notes; neutral notes on three candidates, in rotated order; and one candidate's notes alone. Alone, every candidate won 85–100% of picks, including tools that got 0% with no notes (Supabase 0% → 100%, Postmark 0% → 100%, Trigger.dev 0% → 90%). That is close to a forced choice: it shows the notes are read, not that they persuade.

Side by side, the no-notes favourite stayed on top in four of five duels, with no detectable shift (BullMQ 97% → 92%, Meilisearch 67% → 58%, Resend 100% → 95%, Neon 100% → 92%). With 30 and 60 answers per arm, shifts under about 19–30 points cannot be told apart from noise, so this means no detectable change, not no change.

In authentication, where models had no default, the lead flipped: Auth.js (NextAuth) 67% → 27%, Better Auth 17% → 52% (significant after correcting for 15 comparisons).

Order mattered: the first-listed candidate won 43% of side-by-side picks (95% interval 38–49%; chance is 33%; p < 0.001).

| Category | Candidate | No notes | All three candidates' notes | Its notes alone |
|---|---|---|---|---|
| Background jobs | BullMQ | 97% | 92% | 100% |
| Background jobs | Inngest | 3% | 7% | 100% |
| Background jobs | Trigger.dev | 0% | 2% | 90% |
| Search | Typesense | 3% | 18% | 100% |
| Search | Meilisearch | 67% | 58% | 100% |
| Search | Algolia | 17% | 23% | 100% |
| Authentication | Better Auth | 17% | 52% | 100% |
| Authentication | Clerk | 17% | 22% | 100% |
| Authentication | Auth.js (NextAuth) | 67% | 27% | 100% |
| Transactional email | Resend | 100% | 95% | 100% |
| Transactional email | Postmark | 0% | 5% | 100% |
| Transactional email | SendGrid | 0% | 0% | 90% |
| Postgres hosting | Neon | 100% | 92% | 100% |
| Postgres hosting | Supabase | 0% | 8% | 100% |
| Postgres hosting | PlanetScale | 0% | 0% | 85% |

## What this means

- **If you build with agents:** an agent's stack is mostly the model's default plus whatever documentation reaches its context. If you care which tool you get, name it; in contested categories, rewording the request can change the answer, and the order of a list you give it matters.
- **If you make developer tools:** if you are not the default, the lever is being read, and being listed first helps. Alone in context, every candidate's notes won 85–100% of picks; next to a settled default we detected no shift, and where there was no default the notes flipped the lead. The open ground is the contested categories, where models already disagree: for example Python authentication, vector database, authentication, UI components and pipeline orchestration.

## Early check: asked vs done

We ran Claude Code (model route Opus 5.5) five times on the SaaS-starter task with file tools only, and mapped the dependencies it wrote into package.json to the catalog. Four of six rows name the same package or service as the same model's direct API answers.

Differences: all five runs wrote `next-auth` for authentication, where the API answers named Better Auth 12/12; the Postgres hosting row stays unspecified in the generated files (DATABASE_URL on localhost), where the API answers named Neon 12/12.

The runs did not install, execute or test anything, and used a different harness and system prompt from the API calls, so this pilot does not say why the outputs differ or compare library quality.

| Need | Asked (Claude Opus 5.5†, API) | Written by Claude Code (5 runs) |
|---|---|---|
| Authentication | Better Auth 12/12 | Auth.js (NextAuth) 5/5 |
| Postgres hosting | Neon 12/12 | not specified 5/5 |
| ORM / query builder | Drizzle ORM 12/12 | Drizzle ORM 5/5 |
| Subscription billing | Stripe 12/12 | Stripe 5/5 |
| Transactional email | Resend 12/12 | Resend 5/5 |
| Error monitoring | Sentry 24/24 | Sentry 5/5 |

Raw results: [`docs/pilots/2026-10-15-agent-probe.json`](../../docs/pilots/2026-10-15-agent-probe.json).

## Limits

- **Pilot.** The design was not pre-registered, and some choices (the tier thresholds, the statistics added after a first look) were made after seeing data, so every finding is exploratory. Confirmatory releases lock their protocol before any data is collected (docs/CHARTER.md).
- **Stated preference.** Each answer is one API call naming a tool. Apart from the file-only pilot above, which wrote dependencies but installed nothing, we did not observe real projects.
- **One gateway.** All models were reached through one OpenAI-compatible gateway. The Claude Opus 5.5 and Claude Sonnet 5.5 routes add their own system prompt (about 6.6k tokens), so their picks may reflect it; they are marked † in the tables.
- **Default sampling.** Every model ran at its route's default sampling settings, which differ between models and were not recorded.
- **One task per category.** 27 of 29 categories were asked through a single task prompt (in three phrasings), so a default is a default for that task.
- **Models are not independent.** The 10 models come from 8 labs (two from Anthropic and two from OpenAI), so "every model agrees" is weaker than that many independent confirmations.
- **Our notes, few answers.** Duel notes are short, neutral summaries we wrote from public documentation; real documentation is longer and more persuasive. Each duel arm holds 30 to 60 answers, which is why most shifts are "not detected" rather than "absent".
- **One snapshot.** Collected 2026-10-15 with default sampling; tasks lean to TypeScript and Next.js plus a Python track; each model contributes about 12 answers per category, so single-model cells are small.

## Data and method

Raw answers, the vendor catalog and the code are open; every number here is regenerated from them in CI. Method: [docs/METHODOLOGY.md](../../docs/METHODOLOGY.md). Protocol: [protocols/2026-10.md](../../protocols/2026-10.md) (pilot). Harness this round: the story-driven report, share cards and an inference module (null models, corrected tests).

| Experiment | Planned | Observed | Coverage |
|---|---|---|---|
| 2026-10-baseline | 1920 | 1920 | 100% |
| 2026-10-duel | 750 | 750 | 100% |

Answers not matched to the catalog: 0% of items. Catalog `92e09c2e11c5`, harness 0.1.0.

| Model | Lab | Answers | Reported as |
|---|---|---|---|
| Claude Opus 5.5† | Anthropic | 267 | claude-opus-5-5 |
| Claude Sonnet 5.5† | Anthropic | 267 | claude-sonnet-5.5 |
| DeepSeek V4 Pro | DeepSeek | 267 | deepseek-v4-pro-202606 |
| Gemini 3.8 Flash | Google | 267 | gemini-3.8-flash |
| GLM-5.3 | Zhipu | 267 | glm-5.3 |
| GPT-6.1 Sol | OpenAI | 267 | gpt-6.1-sol |
| GPT-6 Astra | OpenAI | 267 | gpt-6-astra |
| Grok 4.7 | xAI | 267 | grok-4.7-build |
| Kimi K2.7 Code | Moonshot | 267 | kimi-k2.7-code |
| MiniMax M3 | MiniMax | 267 | MiniMax-M3 |

## Appendix: top pick by model, all categories

Ties are shown as A / B. † route adds its own system prompt.

| Category | Claude Opus 5.5† | Claude Sonnet 5.5† | DeepSeek V4 Pro | Gemini 3.8 Flash | GLM-5.3 | GPT-6.1 Sol | GPT-6 Astra | Grok 4.7 | Kimi K2.7 Code | MiniMax M3 |
|---|---|---|---|---|---|---|---|---|---|---|
| Authentication | Better Auth 100% | Better Auth 83% | Auth.js (NextAuth) 83% | Clerk 67% | Auth.js (NextAuth) 83% | Clerk 50% | Auth.js (NextAuth) 67% | Auth.js (NextAuth) 67% | Auth.js (NextAuth) 83% | Clerk 58% |
| Postgres hosting | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% |
| ORM / query builder | Drizzle ORM 100% | Drizzle ORM 100% | Prisma 83% | Drizzle ORM 100% | Drizzle ORM 67% | Drizzle ORM 100% | Drizzle ORM 92% | Prisma 58% | Prisma 83% | Drizzle ORM 83% |
| Subscription billing | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% |
| Transactional email | Resend 100% | Resend 100% | Resend 92% | Resend 100% | Resend 100% | Resend 100% | Resend 100% | Resend 100% | Resend 100% | Resend 100% |
| Error monitoring | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% |
| Search | Meilisearch 100% | Meilisearch 100% | Algolia / Elasticsearch / Meilisearch 33% | Meilisearch 100% | Meilisearch 83% | Meilisearch 75% | Elasticsearch 50% | Meilisearch 75% | Meilisearch 92% | Meilisearch 75% |
| Background jobs | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% |
| Product analytics | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% |
| Feature flags | PostHog 100% | PostHog 100% | LaunchDarkly 100% | LaunchDarkly 100% | LaunchDarkly 75% | LaunchDarkly 100% | LaunchDarkly 83% | LaunchDarkly 83% | PostHog 100% | LaunchDarkly 50% |
| File storage | Amazon S3 100% | Amazon S3 100% | Amazon S3 75% | Amazon S3 83% | Amazon S3 92% | Amazon S3 100% | Amazon S3 100% | Amazon S3 83% | Amazon S3 100% | Cloudflare R2 100% |
| Image delivery | imgix 42% | Cloudinary / Next.js Image (Vercel) 33% | Cloudinary 92% | Cloudinary 75% | Cloudinary 83% | Cloudinary 83% | Cloudinary 100% | Cloudinary 83% | Cloudinary 83% | Cloudflare Images 100% |
| LLM SDK | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 92% | Vercel AI SDK 83% | Vercel AI SDK 100% | OpenAI SDK 83% | Vercel AI SDK 100% |
| LLM provider | Anthropic 100% | Anthropic / OpenAI 50% | OpenAI 100% | OpenAI 92% | OpenAI 92% | OpenAI 100% | OpenAI 100% | OpenAI 100% | OpenAI 100% | OpenAI 100% |
| App hosting | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% |
| Realtime | Liveblocks 100% | Liveblocks 100% | Liveblocks 100% | Liveblocks 100% | Pusher 92% | Liveblocks 100% | Liveblocks 92% | Liveblocks 100% | Liveblocks 67% | Liveblocks 100% |
| Vector database | Qdrant 50% | pgvector 46% | Pinecone 79% | Pinecone 50% | Pinecone 75% | Pinecone 62% | Pinecone 54% | Chroma / Pinecone 33% | Pinecone 46% | Pinecone 54% |
| Headless CMS | Sanity 100% | Sanity 100% | Sanity 92% | Sanity 100% | Sanity 58% | Sanity 100% | Sanity 100% | Sanity 100% | Sanity 67% | Sanity 83% |
| UI components | MUI 42% | MUI 100% | Ant Design 67% | shadcn/ui 50% | Ant Design 100% | MUI 100% | MUI 100% | Ant Design 100% | MUI 100% | Ant Design 75% |
| Unit testing | Vitest 100% | Vitest 83% | Jest 58% | Vitest 75% | Vitest 67% | Vitest 67% | Vitest 67% | Jest 83% | Jest 75% | Jest 67% |
| End-to-end testing | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% |
| Cache | Redis 100% | Redis 100% | Redis 100% | Redis 100% | Redis 100% | Redis 83% | Redis 100% | Redis 100% | Redis 83% | Redis 92% |
| Rate limiting | rate-limiter-flexible 100% | rate-limiter-flexible 100% | rate-limiter-flexible 83% | rate-limiter-flexible 92% | rate-limiter-flexible 75% | rate-limiter-flexible 67% | rate-limiter-flexible 83% | express-rate-limit 92% | express-rate-limit 75% | express-rate-limit 58% |
| Python web framework | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% |
| Python database layer | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% |
| Python authentication | FastAPI Users 100% | Authlib 83% | Auth0 75% | Roll-your-own (JWT / sessions) 75% | Auth0 67% | Auth0 58% | Auth0 75% | Authlib 83% | Auth0 / Authlib 50% | Auth0 75% |
| Python background jobs | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% |
| Python agent framework | LlamaIndex 100% | LlamaIndex 100% | LangChain / LangGraph 100% | LlamaIndex 58% | LangChain / LangGraph 58% | LlamaIndex 67% | LangChain / LangGraph 67% | LangChain / LangGraph 83% | LangChain / LangGraph 100% | LangChain / LangGraph 92% |
| Pipeline orchestration | Prefect 67% | Apache Airflow / Prefect 50% | Apache Airflow 58% | Apache Airflow 67% | Apache Airflow 58% | Prefect 58% | Prefect 58% | Apache Airflow 100% | Prefect 50% | Apache Airflow 67% |
