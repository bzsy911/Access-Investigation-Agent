# Session 1 — Initial Planning

## Context

We are building a small LLM-based agent that helps a security team investigate
employee access. Read `Problem_Description.md` to understand the full brief, and
`input_data/SCHEMA.md` for data model details. You may also query
`input_data/access_snapshot.sqlite` directly if needed.

## Your task

Produce a working plan and write it to `PROJECT.md`. The plan must address the
following questions with clear reasoning:

- **Agent design** — What architectural pattern is appropriate for this exercise
  (e.g. ReAct loop, multi-agent, planning agent)?
- **Model selection** — Which model should be used, balancing capability,
  context window size, and cost?
- **Investigation scope** — Which investigation types are the highest value and
  simplest to implement first?
- **Tool design** — What is the minimal set of tools required to support the
  planned investigations?
- **Agent techniques** — Which techniques (RAG, context engineering, prompt
  caching, trajectory compression, injection guardrails, etc.) should be
  included and which should be deliberately excluded, and why?

Write your plan in `PROJECT.md` as a structured document with a rationale for
each decision.
