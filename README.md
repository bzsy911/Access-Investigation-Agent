# Access Investigation Agent

A small LLM-based agent that helps a security team investigate employee access across HR, identity provider (IdP), Google Workspace, GitHub, and device management systems.

The agent uses a [ReAct](https://arxiv.org/abs/2210.03629) (Reason + Act) loop: the model decides which tool to call next, interprets the result, and repeats until it can produce a conclusion with supporting evidence IDs.

---

## Quick start

### 1. Prerequisites

- Python 3.11+
- `sqlite3` CLI (optional, for direct database inspection)
- An OpenRouter API key

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the API key

```bash
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY=<your key>
```

The key is read from the `OPENROUTER_API_KEY` environment variable.  
**Never commit `.env` or the key itself.**

### 4. Run an investigation

```bash
python agent.py "Which former employees still have active accounts?"
python agent.py "Which users on critical apps are not enrolled in MFA?"
```

Additional options:

```
python agent.py --help

  question          Investigation question (quoted string). If omitted, reads from stdin.
  --steps N         Maximum tool calls before forcing a summary (default: 12).
  --debug           Print full tool inputs and outputs at each step.
  --model MODEL     Override the model (e.g. anthropic/claude-3-5-sonnet).
```

Enable the `run_sql` escape hatch (disabled by default):

```bash
DEBUG_SQL=true python agent.py "Show all active IdP accounts for ended employees"
```

### 5. Run the tests

```bash
python -m pytest tests/ -v
```

---

## Architecture

```
agent.py          CLI entry point; runs the ReAct loop
  │
  ├── runner.py   OpenRouter API wrapper (thin openai SDK shim)
  ├── tools.py    Nine named tools that query the read-only SQLite database
  └── prompts.py  System prompt + compact schema digest injected at turn 0
```

### ReAct loop

```
User question
    │
    ▼
[System prompt + schema digest]
[User message]
    │
    ▼
┌─────────────────────────────────────────┐
│  Model decides: call a tool or answer?  │◄──────────────────────┐
└─────────────────────────────────────────┘                       │
        │ tool call                │ text answer                  │
        ▼                          ▼                              │
  Execute tool             Print final answer               Append tool
  (read-only SQL)          and exit                         result to history
        │                                                         │
        └─────────────────────────────────────────────────────────┘
```

The loop terminates when:
- The model produces a text response (final answer), or
- The step budget is exhausted (`--steps N`, default 12).

### Tool design

All tools are pure Python functions that open the database read-only, run a parameterised query, and return a JSON-serialisable `dict`. The model never writes SQL.

| Tool | Purpose |
|---|---|
| `lookup_person` | Find a person by name, email, or ID; return HR record + linked accounts |
| `find_offboarding_gaps` | People with ended/leave status who still have active accounts |
| `get_person_access_summary` | All accounts, groups, app access, and permissions for one person |
| `get_mfa_gaps` | Active users on sensitive/critical apps without MFA enrolled |
| `get_audit_events` | Audit trail for a given actor or target; filterable by system/type/time |
| `get_application_summary` | App metadata, MFA enrollment stats, recent auth events |
| `get_drive_permissions` | Non-revoked Drive permissions; flag external/domain-wide sharing |
| `get_group_members` | Recursively resolve IdP or Workspace group members (up to depth 3) |
| `run_sql` | Escape hatch: arbitrary `SELECT`; only when `DEBUG_SQL=true` |

Every tool result includes a `_meta` field with `total_count`, `returned`, `truncated`, and `query_time_ms`. Results are trimmed to ~6,000 characters to prevent context overflow.

### Model

Default: `google/gemini-2.5-flash` via OpenRouter.

Rationale: 1 M token context window (holds many tool results simultaneously), strong function-calling, fast and cheap. Override with `--model` or the `MODEL` env variable.

### Context management

- The **system prompt** contains a compact schema digest (~600 tokens) — table names, column types, and the joins that matter — not the full SCHEMA.md.
- **Tool results** are capped at ~6,000 characters each.
- **Step budget** prevents runaway loops and keeps total context bounded.
- No RAG, no trajectory summarisation: the 1 M window is large enough for a single investigation session.

### Evidence discipline

The system prompt instructs the model to:
1. Cite every record or event ID that supports a conclusion.
2. Separate facts (what the database shows) from inferences.
3. Note gaps and uncertainty explicitly.

The final answer is always a structured JSON block:

```json
{
  "conclusion": "Plain-language summary.",
  "findings": [
    {
      "description": "Specific finding.",
      "severity": "high|medium|low",
      "evidence_ids": ["id1", "id2"]
    }
  ],
  "uncertainty": "What could not be determined.",
  "steps_used": 5
}
```

---

## Known limitations

| Limitation | Impact |
|---|---|
| **Nested group depth cap (3)** | Groups nested more than 3 levels deep may have unresolved indirect members |
| **Incomplete audit logs** | Absence of an event does not prove absence of activity; the agent notes this |
| **Snapshot only** | Data is frozen at `2026-08-15T12:00:00Z`; no real-time changes are visible |
| **`person_id` nulls** | Accounts without a matched person are excluded from person-centric queries |
| **No cross-system dedup** | A person with three accounts may appear three times in some queries |
| **run_sql disabled by default** | Advanced ad-hoc queries require `DEBUG_SQL=true` |

---

## What to build next

1. **Privilege escalation investigation** — detect admin roles added recently via audit events.
2. **Cross-system access correlation** — one view of all permissions across all systems for a person, with risk scoring.
3. **Automated anomaly report** — HTML summary of all open offboarding gaps and MFA gaps.
4. **Confidence scoring** — numeric confidence based on how many corroborating sources agree.
5. **run_sql hardening** — full SELECT-only parser for safer production use.

---

## File layout

```
Access-Investigation-Agent/
├── agent.py              Entry point; ReAct loop
├── tools.py              All 9 tool implementations
├── prompts.py            System prompt and schema digest
├── runner.py             OpenRouter API client wrapper
├── requirements.txt      Python dependencies
├── .env.example          Environment variable template
├── tests/
│   └── test_tools.py     Tool unit tests
├── examples/             Sample investigation outputs (generated)
├── input_data/
│   ├── access_snapshot.sqlite
│   └── SCHEMA.md
└── PROJECT.md            Architecture and planning notes
```
