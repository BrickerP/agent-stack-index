# Roadmap

## Research

| Next | Why |
|---|---|
| **Agent probe** (pilot done, see `docs/pilots/`): extend to Codex and opencode, more tasks, and a shell-enabled arm; then promote it into the planner as `probe = "agent"` | Turns stated preference into revealed preference; measures how often "ask" agrees with "do" |
| **Retrieval probe**: give the agent web and docs tools and record which pages it fetches before choosing | Shows which surfaces (docs, llms.txt, Context7, GitHub, comparison posts) actually feed the decision |
| Trend view across monthly releases | Defaults drift as models and training data change; the time series is the index's long-term value |
| More stacks (Go, Rails, mobile) and more phrasings per task | Wider coverage, tighter intervals |
| Per-lab and per-model-family breakdowns | Vendors care which agents miss them |

The probe interface is the extension point: a probe plans trials from an experiment spec and turns one trial into one stored observation. Add a planner in `plan.py` and a runner path; storage, normalization, analysis and releases are shared.

## Products on top of the research

1. **Public index (free, monthly).** Brand and distribution. Never sold: no paid placement, no early access.
2. **Agent-readiness audit (paid, fixed scope).** For one developer-tool vendor: custom duels with its real documentation against the measured default and runner-up across all models, agent-probe sessions on its quickstart, and a prioritized fix list. Engine: `asi audit --vendor <id> --plan --out <private path>`.
3. **Agent-ready engineering (paid project).** Ship the fixes: llms.txt and Markdown docs, a copy-paste quickstart for the stacks agents build, an MCP server for setup tasks, example repositories, comparison pages. Close with a before/after re-test on the same harness, so the result is measured rather than claimed.
4. **Monitoring retainer.** Monthly re-test of the vendor's categories with alerts when a model release moves the default.
5. **Data access (later).** The raw observations are already public; a hosted API or custom cuts only if vendors ask.

## Validation gate for the commercial track

Two weeks after the first public post: at least 3 of 10 contacted vendors reply and at least 1 agrees to a paid pilot, or the commercial track stops and the index continues as research.
