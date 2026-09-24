# Session 7 — Submission Document

## Context

The project is complete. `README.md` and `PROJECT.md` contain the architecture
notes and quick-start instructions. The submission requirements are listed in
`Problem_Description.md`.

## Your task

Create `Submission.md` as a single, self-contained document that satisfies the
submission requirements exactly. It must contain the following five sections in
order:

### 1. Setup instructions

Step-by-step instructions to install dependencies, configure the API key, run
an investigation, and run the tests. A reviewer must be able to follow these
steps from a clean checkout with no prior knowledge of the project.

### 2. Scope and architecture

A concise explanation of:

- Which investigation types were chosen and why.
- The agent architecture (pattern, model choice, rationale).
- How tools are designed and how context is managed.
- The output contract (structured final answer format).

### 3. Three example investigations

Run the three successful demos in `demo.py` and capture the actual agent output.
Include the full structured output for each investigation, the tool calls made,
and the evidence IDs cited. Do not paraphrase — use the real output.

### 4. Testing approach

Describe how the agent was verified to be working correctly. Cover:

- The unit test suite and what it checks.
- Smoke tests and how cited evidence IDs were verified against the database.
- Adversarial / failure-mode testing and how the `cannot_proceed` path was
  exercised.

### 5. Known limitations and what to build next

List the current limitations with their practical impact. For each gap exposed
by the adversarial demos, describe the specific tool or capability that would
close it.
