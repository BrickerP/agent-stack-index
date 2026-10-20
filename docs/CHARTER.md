# Research charter

The Agent Stack Index is the first step of a research series on **agent experience (AX) engineering**: how AI coding agents choose, read and use developer tools, and what builders and tool makers can do about it. This charter fixes what every experiment in the series must state, how it must be run, and how it is reported. The report is for engineers to read; the path behind it follows the rules of a good experiment.

## Direction: the ladder

Each experiment sits on one rung, and its protocol says why that rung is next.

| Rung | Question | Typical design |
|---|---|---|
| 1 Describe | What do agents pick? | The same needs asked across models, tasks and phrasings |
| 2 Explain | What moves the pick? | Minimal pairs: change one thing (wording, order, documentation), keep the rest |
| 3 Behave | Do agents do what they say? | Real harnesses on real tasks; record what is written, installed and run |
| 4 Intervene | Which change makes a tool or a setup work better? | Before and after on the same harness, randomized where possible |
| 5 Track | How does it drift? | The same instrument, every month |

Release 2026-10 is rung 1, run as a pilot.

## What every experiment states, before it runs

1. **Direction.** Its rung, and what the previous experiment left open.
2. **Goal.** One falsifiable question, and the decision its answer changes.
3. **Process.** Hypotheses, design, controls, sample size and analysis plan.
4. **Engineering benefit.** What builders and tool makers can do with the answer, and what we improve in our own harness this round.
5. **Report.** The findings we expect to report, in plain words, and what "not detected" would look like.

These live in `protocols/<release>.md` (template: `protocols/TEMPLATE.md`). `asi validate` fails when a release has no protocol, when a section is empty or still says TODO, or when the release has no `[analysis]` table.

## Process rules

- **Write the plan first.** A confirmatory protocol is locked (`asi lock <release>`) before any data exists. The lock covers the protocol text, the experiment specs and `release.toml`, which holds the analysis thresholds. Later changes go under `## Deviations`; `asi run` refuses to start on an unlocked or changed confirmatory protocol, and `asi validate` fails on data older than the lock.
- **Control what you can, record what you cannot.** Sampling parameters are fixed and written down, candidates' order is counterbalanced, hidden system prompts are flagged, and the headline claims get a replication through a path we do not control.
- **Manipulate one thing at a time.** Changes are minimal pairs, with a no-effect control and a sanity check run before anyone reads a result.
- **Size the experiment for the effect you care about.** The protocol states how many answers each arm gets and the smallest shift they can resolve. Smaller shifts are reported as "not detected", never as "no effect".
- **Compare with noise, not with zero.** Counts are reported against a null model (the release prints it), intervals are shown, and families of tests are corrected (Holm).
- **Label the evidence.** Confirmatory means the plan said so before the data. Anything added after a first look is exploratory and says so. A pilot is exploratory by definition.
- **Log deviations; never edit them away.**

## Reports

- Answer first, in plain words: at most three findings, each tagged (confirmed, not detected, exploratory) and backed by one number.
- Then: the question and why it matters, what we did, what it means for builders and for tool makers, how sure we are, and where the data and the protocol are.
- A claim appears only if the analysis plan allows it. The report is generated from the same inference that CI checks, so wording follows the test: "changed" when the test supports it, "no detectable change" when it does not.
- Details (statistics, per-model tables) sit below the fold, not in the headline.

## Not in scope

Paid placement; rankings of tool quality; explanations of why a model behaves as it does without an experiment that isolates the cause.
