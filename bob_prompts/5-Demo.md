# Session 5 — Demo Coverage

## Context

The architecture and tool design have been finalised in `PROJECT.md`. Read that
file before proceeding.

## Your task

Expand the demo script to cover both the agent's strengths and its known limits.

### 1. Split `DEMOS` into two lists

In `demo.py`, replace the single `DEMOS` list with two named lists:

- **`DEMOS_SUCCESSFUL`** — investigations the agent answers end-to-end with
  findings and evidence IDs.
- **`DEMOS_ADVERSARIAL`** — questions that hit a tool limit and trigger the
  structured `cannot_proceed` fallback implemented in Session 4.

Update the CLI so that `python demo.py success` runs only the successful demos,
`python demo.py adversarial` runs only the adversarial ones, and numeric IDs
still work as before.

### 2. Add three new demo entries

Add one new entry to `DEMOS_SUCCESSFUL` and two new entries to `DEMOS_ADVERSARIAL`,
so each list contains exactly three demos.

- The new successful demo must produce a multi-finding structured answer using
  at least three tool calls.
- Each new adversarial demo must expose a distinct, realistic tool gap and
  trigger `cannot_proceed` with a meaningful `missing_capability` and
  `alternative_command`.

Include a brief `expected_behaviour` note on each adversarial entry so the
output is self-documenting during a live review.
