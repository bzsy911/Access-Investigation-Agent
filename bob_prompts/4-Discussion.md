# Session 4 — Agent Behaviour Discussion

## Context

Demo 3 in `demo.py` ("Show drive permissions for ended employees") stops at
step 1 of 15 with the following output:

```
[step 1/15] Calling model …

════════════════════════════════════════════════════════════════
  INVESTIGATION RESULT
════════════════════════════════════════════════════════════════

I can only search for a specific `resource_id` or `account_id` when looking
for drive permissions, not for all ended employees. I can, however, find ended
employees who still have active accounts. Would you like me to do that?
```

The agent correctly identified a tool gap but then exited, asking an
interactive question that the current CLI cannot answer.

## Design question

Two approaches could address this:

**Option A — Interactive follow-up loop**  
Allow the user to respond to the agent's question (yes/no or a follow-up
prompt) and let the agent continue working from that response. How much effort
would this take to implement, and does it fit the current architecture?

**Option B — Structured fallback output**  
When the agent cannot proceed, have it emit a structured output describing the
gap and the available alternative, for example:

```
To enable investigation of drive permissions for ended employees,
consider adding a tool <tool_name> that does XYZ.

Alternatively, you can investigate ended employees with active accounts by running:

    python agent.py "Which former employees still have active accounts?"
```

Which option better fits the current framework and serves the goals of this
exercise? Provide a recommendation with reasoning, then implement the chosen
approach.
