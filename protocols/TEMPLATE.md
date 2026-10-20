# Protocol <release id>: <title>

Status: confirmatory
Rung: describe
Written: <date>

Fill every section. A section that is empty or still contains the word TODO fails `asi validate`. For a confirmatory protocol, run
`asi lock <release id>` before any data is collected: everything above `## Deviations`, the experiment specs and release.toml
(which holds the `[analysis]` parameters) are then frozen. Use `Status: pilot` only for an exploratory run, and say so in the report.

## Direction
TODO: the rung (describe, explain, behave, intervene or track) and what the previous experiment left open.

## Goal
TODO: one falsifiable question.

Decision: TODO: what we will do differently depending on the answer.

## Hypotheses
TODO: numbered, directional; each names its analysis (wording, duel contrast, position, or a new one) and its threshold.

## Design
TODO: models, tasks, phrasings, arms, repeats; what is manipulated and what is held fixed.

## Controls
TODO: sampling parameters fixed and recorded; order counterbalanced; hidden system prompts; an independent path for replication.

## Sample size
TODO: answers per arm, and the smallest shift they can resolve (the report prints the minimum detectable effect).

## Analysis
TODO: primary and secondary analyses, thresholds (`[analysis]` in release.toml), multiple-comparison correction, exclusion rules.

## Validity checks
TODO: checks run before reading results (mapping audit, neutrality of the notes, a no-effect control).

## Engineering benefit
Builders: TODO: what someone building with agents can do with the answer.

Tool makers: TODO: what someone making developer tools can do with it.

Harness: TODO: what we improve in our own method or tooling this round.

## Report
TODO: the findings we expect to report, in plain words, and what "not detected" would look like.

## Deviations
Changes after the lock, one line each: date, what, why.
