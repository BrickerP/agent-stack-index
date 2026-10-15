# Agent Stack Index — October 2026

Which libraries and hosted services AI coding models pick when they start a project from scratch, and how much the pick moves when vendor documentation is in context.

## Headline

- **19 of 29 categories** have a default that at least 80% of models share; in 12 of them every model picks the same tool and it takes at least 95% of all answers.
- Unanimous defaults include BullMQ (Background jobs), Neon (Postgres hosting), Playwright (End-to-end testing), Sentry (Error monitoring), Vercel (App hosting), Stripe (Subscription billing).
- **Whatever the model reads decides the pick.** With only one candidate's notes in context, models pick that candidate 85%–100% of the time, including tools they never pick unprompted (Trigger.dev 0% → 90%, Postmark 0% → 100%, SendGrid 0% → 90%).
- With all candidates' notes side by side, most defaults hold, but Authentication moves: Better Auth goes from 17% to 52%.
- Asked for an LLM provider, the pooled pick is OpenAI; by lab: Claude Opus 5.5 names Anthropic 100%; Claude Sonnet 5.5 names Anthropic 50%; Gemini 3.8 Flash names Google 8%; GPT-6.1 Sol names OpenAI 100%; GPT-6 Astra names OpenAI 100%.
- 2,670 answers from 10 models, collected 2026-10-15.

## The default stack

| Category | Top pick | Pooled share | Models agreeing | Runner-up |
|---|---|---|---|---|
| Authentication | Auth.js (NextAuth) | 52% | 5/10 | Better Auth (24%) |
| Postgres hosting | Neon | 100% | 10/10 | — |
| ORM / query builder | Drizzle ORM | 72% | 7/10 | Prisma (28%) |
| Subscription billing | Stripe | 100% | 10/10 | — |
| Transactional email | Resend | 99% | 10/10 | Postmark (1%) |
| Error monitoring | Sentry | 100% | 10/10 | — |
| Search | Meilisearch | 77% | 8/10 | Elasticsearch (13%) |
| Background jobs | BullMQ | 100% | 10/10 | — |
| Product analytics | PostHog | 100% | 10/10 | — |
| Feature flags | LaunchDarkly | 59% | 7/10 | PostHog (38%) |
| File storage | Amazon S3 | 83% | 9/10 | Cloudflare R2 (12%) |
| Image delivery | Cloudinary | 64% | 8/10 | Cloudflare Images (13%) |
| LLM SDK | Vercel AI SDK | 89% | 9/10 | OpenAI SDK (11%) |
| LLM provider | OpenAI | 83% | 8/10 | Anthropic (16%) |
| App hosting | Vercel | 100% | 10/10 | — |
| Realtime | Liveblocks | 87% | 9/10 | Pusher (9%) |
| Vector database | Pinecone | 46% | 7/10 | Qdrant (25%) |
| Headless CMS | Sanity | 90% | 10/10 | Contentful (8%) |
| UI components | MUI | 52% | 5/10 | Ant Design (38%) |
| Unit testing | Vitest | 57% | 6/10 | Jest (42%) |
| End-to-end testing | Playwright | 100% | 10/10 | — |
| Cache | Redis | 96% | 10/10 | Upstash Redis (2%) |
| Rate limiting | rate-limiter-flexible | 67% | 7/10 | express-rate-limit (31%) |
| Python web framework | FastAPI | 100% | 10/10 | — |
| Python database layer | SQLAlchemy | 100% | 10/10 | — |
| Python authentication | Auth0 | 42% | 6/10 | Authlib (27%) |
| Python background jobs | Celery | 100% | 10/10 | — |
| Python agent framework | LangChain / LangGraph | 57% | 6/10 | LlamaIndex (42%) |
| Pipeline orchestration | Apache Airflow | 54% | 6/10 | Prefect (42%) |

## Top pick by model

| Category | Claude Opus 5.5 | Claude Sonnet 5.5 | DeepSeek V4 Pro | Gemini 3.8 Flash | GLM-5.3 | GPT-6.1 Sol | GPT-6 Astra | Grok 4.7 | Kimi K2.7 Code | MiniMax M3 |
|---|---|---|---|---|---|---|---|---|---|---|
| Authentication | Better Auth 100% | Better Auth 83% | Auth.js (NextAuth) 83% | Clerk 67% | Auth.js (NextAuth) 83% | Clerk 50% | Auth.js (NextAuth) 67% | Auth.js (NextAuth) 67% | Auth.js (NextAuth) 83% | Clerk 58% |
| Postgres hosting | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% | Neon 100% |
| ORM / query builder | Drizzle ORM 100% | Drizzle ORM 100% | Prisma 83% | Drizzle ORM 100% | Drizzle ORM 67% | Drizzle ORM 100% | Drizzle ORM 92% | Prisma 58% | Prisma 83% | Drizzle ORM 83% |
| Subscription billing | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% | Stripe 100% |
| Transactional email | Resend 100% | Resend 100% | Resend 92% | Resend 100% | Resend 100% | Resend 100% | Resend 100% | Resend 100% | Resend 100% | Resend 100% |
| Error monitoring | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% | Sentry 100% |
| Search | Meilisearch 100% | Meilisearch 100% | Algolia 33% | Meilisearch 100% | Meilisearch 83% | Meilisearch 75% | Elasticsearch 50% | Meilisearch 75% | Meilisearch 92% | Meilisearch 75% |
| Background jobs | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% | BullMQ 100% |
| Product analytics | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% | PostHog 100% |
| Feature flags | PostHog 100% | PostHog 100% | LaunchDarkly 100% | LaunchDarkly 100% | LaunchDarkly 75% | LaunchDarkly 100% | LaunchDarkly 83% | LaunchDarkly 83% | PostHog 100% | LaunchDarkly 50% |
| File storage | Amazon S3 100% | Amazon S3 100% | Amazon S3 75% | Amazon S3 83% | Amazon S3 92% | Amazon S3 100% | Amazon S3 100% | Amazon S3 83% | Amazon S3 100% | Cloudflare R2 100% |
| Image delivery | imgix 42% | Cloudinary 33% | Cloudinary 92% | Cloudinary 75% | Cloudinary 83% | Cloudinary 83% | Cloudinary 100% | Cloudinary 83% | Cloudinary 83% | Cloudflare Images 100% |
| LLM SDK | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 100% | Vercel AI SDK 92% | Vercel AI SDK 83% | Vercel AI SDK 100% | OpenAI SDK 83% | Vercel AI SDK 100% |
| LLM provider | Anthropic 100% | Anthropic 50% | OpenAI 100% | OpenAI 92% | OpenAI 92% | OpenAI 100% | OpenAI 100% | OpenAI 100% | OpenAI 100% | OpenAI 100% |
| App hosting | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% | Vercel 100% |
| Realtime | Liveblocks 100% | Liveblocks 100% | Liveblocks 100% | Liveblocks 100% | Pusher 92% | Liveblocks 100% | Liveblocks 92% | Liveblocks 100% | Liveblocks 67% | Liveblocks 100% |
| Vector database | Qdrant 50% | pgvector 46% | Pinecone 79% | Pinecone 50% | Pinecone 75% | Pinecone 62% | Pinecone 54% | Chroma 33% | Pinecone 46% | Pinecone 54% |
| Headless CMS | Sanity 100% | Sanity 100% | Sanity 92% | Sanity 100% | Sanity 58% | Sanity 100% | Sanity 100% | Sanity 100% | Sanity 67% | Sanity 83% |
| UI components | MUI 42% | MUI 100% | Ant Design 67% | shadcn/ui 50% | Ant Design 100% | MUI 100% | MUI 100% | Ant Design 100% | MUI 100% | Ant Design 75% |
| Unit testing | Vitest 100% | Vitest 83% | Jest 58% | Vitest 75% | Vitest 67% | Vitest 67% | Vitest 67% | Jest 83% | Jest 75% | Jest 67% |
| End-to-end testing | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% | Playwright 100% |
| Cache | Redis 100% | Redis 100% | Redis 100% | Redis 100% | Redis 100% | Redis 83% | Redis 100% | Redis 100% | Redis 83% | Redis 92% |
| Rate limiting | rate-limiter-flexible 100% | rate-limiter-flexible 100% | rate-limiter-flexible 83% | rate-limiter-flexible 92% | rate-limiter-flexible 75% | rate-limiter-flexible 67% | rate-limiter-flexible 83% | express-rate-limit 92% | express-rate-limit 75% | express-rate-limit 58% |
| Python web framework | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% | FastAPI 100% |
| Python database layer | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% | SQLAlchemy 100% |
| Python authentication | FastAPI Users 100% | Authlib 83% | Auth0 75% | Roll-your-own (JWT / sessions) 75% | Auth0 67% | Auth0 58% | Auth0 75% | Authlib 83% | Auth0 50% | Auth0 75% |
| Python background jobs | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% | Celery 100% |
| Python agent framework | LlamaIndex 100% | LlamaIndex 100% | LangChain / LangGraph 100% | LlamaIndex 58% | LangChain / LangGraph 58% | LlamaIndex 67% | LangChain / LangGraph 67% | LangChain / LangGraph 83% | LangChain / LangGraph 100% | LangChain / LangGraph 92% |
| Pipeline orchestration | Prefect 67% | Apache Airflow 50% | Apache Airflow 58% | Apache Airflow 67% | Apache Airflow 58% | Prefect 58% | Prefect 58% | Apache Airflow 100% | Prefect 50% | Apache Airflow 67% |

## Context duels

Same single-item task, three arms: no notes, all candidates' notes (order rotated), each candidate's notes alone.

| Category | Candidate | No notes | All notes | Its notes alone |
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

Listed-first candidate won 43% of all-notes picks (one third would be no position effect).

## Coverage

| Experiment | Planned | Observed | Coverage |
|---|---|---|---|
| 2026-10-baseline | 1920 | 1920 | 100% |
| 2026-10-duel | 750 | 750 | 100% |

Answers not matched to the catalog: 0% of items. Catalog `92e09c2e11c5`, harness 0.1.0.

## Models

| Model | Lab | Answers | Reported as | Notes |
|---|---|---|---|---|
| Claude Opus 5.5 | Anthropic | 267 | claude-opus-5-5 | Gateway route adds its own system prompt (~6.6k input tokens on an empty request). |
| Claude Sonnet 5.5 | Anthropic | 267 | claude-sonnet-5.5 | Gateway route adds its own system prompt (~6.6k input tokens on an empty request). |
| DeepSeek V4 Pro | DeepSeek | 267 | deepseek-v4-pro-202606 |  |
| Gemini 3.8 Flash | Google | 267 | gemini-3.8-flash |  |
| GLM-5.3 | Zhipu | 267 | glm-5.3 |  |
| GPT-6.1 Sol | OpenAI | 267 | gpt-6.1-sol |  |
| GPT-6 Astra | OpenAI | 267 | gpt-6-astra |  |
| Grok 4.7 | xAI | 267 | grok-4.7-build |  |
| Kimi K2.7 Code | Moonshot | 267 | kimi-k2.7-code |  |
| MiniMax M3 | MiniMax | 267 | MiniMax-M3 |  |

Method and limitations: see [docs/METHODOLOGY.md](../../docs/METHODOLOGY.md).
