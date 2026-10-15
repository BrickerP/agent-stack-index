# Methodology

## Question

When an AI coding model starts a project from scratch, which library or hosted service does it pick for each need, and how much does that pick move when documentation is in its context?

## Probes

**Ask (baseline).** One API call per trial. The model receives a from-scratch build task and a list of needs (for example `auth`, `database_host`, `payments`) and must answer with one JSON object naming one package or service per need. Every task is asked in three phrasings: an agent persona (`pick`), a user question (`user`) and a dependency plan (`install`), each repeated several times. See `prompts/prompts.toml` and `tasks/tasks.toml`.

**Duel (context).** Same single-need task, three arms:

- `none`: no notes (control);
- `trio`: neutral notes for three candidates, with the order rotated through all permutations;
- `solo:<vendor>`: only that candidate's notes.

Notes are written by us from public documentation, follow one template (what it is, how it runs, capabilities, install command, pricing model) and have roughly equal length. They are in `contexts/public/`. The arm structure separates three effects: the default (none), being in context next to rivals (trio), and being the only documentation the model has read (solo). The rotated order measures position bias.

## Interpretation

Raw answers are stored verbatim. A public catalog (`catalog/`) maps answers to vendors per category: exact aliases (product and package names) first, then the longest alias appearing as a whole word, with catch-all entries such as "Postgres (no host named)" used only when nothing specific matches. Unmatched answers are counted as "other", never dropped, and listed in each release so the catalog can be curated. Long-tail tools are grouped (for example "Other email APIs"); splitting a group is a catalog edit and regenerates every release from the same raw data.

## Statistics

- Each model's share of picks per category, with a Wilson 95% interval on its top pick.
- Pooled shares are the equal-weight mean of the models' share vectors, so a model that answers more often does not count more.
- "Models agreeing" counts models whose own top pick equals the pooled top pick.
- Variant consistency counts models whose top pick is the same in all three phrasings.
- Duels report pooled shares per arm, the lift from being in context next to rivals (trio minus none), the solo win rate, and the rate at which the first-listed candidate wins in the trio arm.

## Limitations

- **Stated, not revealed, preference.** These are answers to direct questions through an API, not dependencies installed during a full agent session with tools, a repository and a long system prompt. Agent harnesses add their own instructions and documentation retrieval. An agent probe that inspects what a real CLI agent writes into `package.json` is on the roadmap; until then, read the index as "what the model reaches for by default".
- **Gateway.** Models are reached through an OpenAI-compatible gateway and identified by the model name the gateway reports. Some routes add their own system prompt (noted per model in each release); we cannot see its content.
- **Sampling.** Default sampling parameters; a few repeats per phrasing. Wilson intervals are reported per model; small cells are wide. Attempts that return no parseable answer (for example a reasoning model spending its whole token budget on reasoning) are stored and retried; releases use the last successful answer per trial.
- **Coverage.** Tasks lean towards TypeScript and Next.js, plus a Python track. Categories and phrasings are a design choice, not a census of real projects.
- **Notes are ours.** Duel results depend on the notes. They are short and neutral by design; real vendor documentation is longer and more persuasive, so solo results are, if anything, conservative for a vendor with good docs.
- **Time.** Models and their training data change. Each monthly release is a snapshot with its data window recorded.

## Independence

No vendor pays for inclusion, placement or early access, and notes are not vendor-written. The author offers agent-readiness engineering to developer-tool companies; that work uses the same open method on private runs and never changes the public index.
