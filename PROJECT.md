# Access Investigation Agent — Project Reference

> **For the AI agent:** Read this file at the start of every session. It is the
> authoritative single source of truth about the project's purpose, current
> state, architecture, data model, API, and known gotchas.

---

# Access Investigation Agent — Project Plan

## Problem Summary

Build a small LLM-based agent that helps a security team investigate employee access across HR, identity provider (IdP), Google Workspace, GitHub, and device management systems. The database is a SQLite snapshot with ~2,000 people, ~4,900 accounts, 8,000 user-to-app relationships, and 48,000 audit events. It is too large to send wholesale to a model; the core challenge is giving the model just enough context to reason accurately.

---

## Agent Design

### Pattern: ReAct (Reason + Act) loop, single-threaded

A single-agent ReAct loop is the right fit here:

- The investigation is inherently iterative. A first query surfaces an anomaly; follow-up queries gather supporting evidence. The model must decide at each step what to look at next.
- The data is relational and fragmented across tables. No single query answers a full question; the agent must chain lookups.
- There is no planning phase that benefits from a multi-agent or supervisor pattern — a single capable model running tool calls in a loop is simpler and more auditable.
- The loop terminates when the model emits a structured final answer with evidence IDs, or when a step budget is exhausted.

### Interface

A minimal CLI: `python agent.py "<investigation question>"`. The agent prints a structured text report to stdout. No web UI. Output is suitable for piping to a file for submission artifacts.

### Output contract

Every answer must include:
1. A plain-language conclusion.
2. A list of supporting record or event IDs (e.g. `person_id`, `account_id`, `event_id`).
3. An explicit uncertainty note when evidence is absent or incomplete.

---

## Model Choice

**Model: `google/gemini-2.5-flash` via OpenRouter**

Rationale:
- Strong reasoning with a large context window (1 M tokens), important when the agent needs to hold several query results simultaneously.
- Fast and cheap — stays well within the spending cap for tens of investigation turns.
- Function-calling support is solid and well-documented via the OpenAI-compatible API.
- Alternatives considered:
  - `anthropic/claude-3-5-sonnet`: better reasoning, but ~6× more expensive per token; risk of hitting budget on a multi-turn investigation.
  - `openai/gpt-4o-mini`: cheapest, but weaker at multi-hop relational reasoning.
  - `google/gemini-2.5-pro`: best reasoning but most expensive; not justified given the time and budget constraints.

The agent will use the OpenRouter OpenAI-compatible endpoint (`https://openrouter.ai/api/v1`) with the Python `openai` SDK, reading the key from the `OPENROUTER_API_KEY` environment variable. It is set inside `.env` and this file should be git-ignored.

---

## Investigations to Support

Starting simple: two high-value, clearly-scoped investigation workflows.

### Investigation 1 — Offboarding Residual Access

**Question type:** "Which former employees still have active accounts or permissions?"

Why easy to start with:
- Clear definition of anomaly: `people.employment_status = 'ended'` joined against any active account table.
- Data is directly in the snapshot — no complex audit trail traversal needed.
- High business value (a classic SOC/access-review finding).
- Produces concrete record IDs for every finding.

Sub-questions the agent can answer:
- Active IdP account after employment end.
- Active Workspace account after employment end.
- Active GitHub account after employment end.
- Active application access (`application_user_access.status = 'active'`) after employment end.
- Drive permissions not revoked for a departed user's Workspace account.
- Any audit activity (logins, git pushes) after the `end_date`.

### Investigation 2 — MFA Gap Analysis

**Question type:** "Which users have access to critical/sensitive applications without MFA enrolled?"

Why easy to start with:
- Contained to two tables: `applications` and `application_user_access`.
- A clear risk classification: `applications.sensitivity` combined with `mfa_enrollment_status`.
- Can be extended to audit sign-in events to find actual logins without MFA.

Sub-questions:
- Users active on `critical` or `sensitive` apps with `mfa_enrollment_status != 'enrolled'`.
- Cross-check: did any of those users authenticate recently via `audit_events` without MFA?
- Which apps have `default_mfa_requirement = 'required'` but enrolled users < 100%?

### Additional investigations (available but lower priority for initial delivery)

- **Privilege escalation / unusual role assignments**: users with `admin` roles added recently.
- **External Drive over-sharing**: `drive_permissions` where `principal_type = 'external_email'` or `domain` on `restricted`/`confidential` resources.
- **OAuth scope sprawl**: `workspace_oauth_grants` with broad scopes held by users with sensitive app access.
- **Orphaned / unlinked accounts**: accounts with `person_id IS NULL` that have active permissions.
- **Service account activity**: GitHub service accounts with recent commit activity.

---

## Tool Design

The agent has access to a small, focused set of SQL-backed tools. Each tool runs a parameterised query and returns a compact JSON result. The model never constructs raw SQL — it calls named tools with structured arguments.

### Core principle: tools return summaries, not raw rows

Each tool caps its result set (default 50 rows) and summarises counts before listing records. This prevents context bloat.

### Planned tools

| Tool | Purpose |
|---|---|
| `lookup_person` | Given a name, email, or person_id, return basic HR record and list of linked accounts. |
| `find_offboarding_gaps` | Return people with `employment_status = 'ended'` (or 'leave') who have at least one active account. Accepts optional `system` filter (`idp`, `github`, `workspace`). |
| `get_person_access_summary` | Given a `person_id`, return all active accounts, group memberships, application access, and drive/github permissions. |
| `get_mfa_gaps` | Return active application access records where app sensitivity meets threshold (`sensitive` or `critical`) and MFA is not enrolled. Accepts optional `app_id` filter. |
| `get_audit_events` | Given an actor or target ID, return recent audit events. Accepts `system`, `event_type`, `since` filters and a row limit. |
| `get_application_summary` | Return an application's metadata, all active user access (with MFA status), and recent auth events. |
| `get_drive_permissions` | Given a resource or account ID, return current (non-revoked) permissions, highlighting external or domain-wide ones. |
| `get_group_members` | Given a group ID (IdP or Workspace), resolve direct and nested members recursively (up to 3 levels). |
| `run_sql` | *(Escape hatch, disabled by default)* Execute an arbitrary read-only SELECT. Only enabled in debug mode; every call is logged. |

### Tool design notes
- All tools open the database read-only (`sqlite3.connect(..., check_same_thread=False)` with `PRAGMA query_only=ON`).
- Results are serialised to JSON and truncated at a token budget (~2,000 tokens per result).
- Tools return a `_meta` field with row count, truncation flag, and query time.

---

## Agent Techniques

### What we include

| Technique | Why |
|---|---|
| **System prompt with schema summary** | The model needs to know table names, key relationships, and the anomaly definitions. A compact schema digest (~600 tokens) is prepended to every conversation. This is not the full SCHEMA.md — it is a distilled version with the joins that matter for the planned investigations. |
| **Step budget / turn cap** | Cap at 12 tool calls per investigation to prevent runaway loops. If the budget runs out, the model is instructed to summarise what it found so far. |
| **Structured final answer format** | The model is instructed via the system prompt to end every investigation with a JSON block: `{"conclusion": "...", "evidence_ids": [...], "uncertainty": "..."}`. This makes parsing and submission artefact generation reliable. |
| **Result truncation** | Every tool trims output to fit a token budget. The model sees counts and top-N rows, not full table dumps. |

### What we deliberately exclude

| Technique | Why not |
|---|---|
| **RAG / embedding retrieval** | The schema is small and stable. Pre-embedding is unnecessary overhead for a 4-hour build. A compact schema digest in the system prompt is sufficient. |
| **Prompt caching** | Beneficial only at scale. The session is short-lived; cache warm-up cost outweighs savings. |
| **Trajectory compression / summarisation** | The context window is 1 M tokens. Summarising intermediate steps is not needed and risks losing evidence. |
| **Injection guardrails** | The model never executes remediation. Tools are read-only SQL. Injection risk is low and the `run_sql` escape hatch is disabled by default. Adding a guardrail layer would add code without meaningful safety benefit in this context. |
| **Multi-agent orchestration** | One investigation at a time; a supervisor/sub-agent split adds complexity without a clear benefit given the scope. |
| **Memory / persistence** | Each investigation is stateless. Persisting state across sessions is out of scope. |

---

## Repository Layout

```
Access-Investigation-Agent/
├── agent.py              # Entry point: parses CLI args, runs ReAct loop
├── tools.py              # All tool implementations (SQL + formatting)
├── prompts.py            # System prompt and schema digest constants
├── runner.py             # OpenRouter API client wrapper (thin openai SDK shim)
├── input_data/
│   ├── access_snapshot.sqlite   (read-only, not committed if large)
│   └── SCHEMA.md
├── examples/
│   ├── investigation_1_offboarding.md   # Sample run output
│   └── investigation_2_mfa_gaps.md      # Sample run output
├── README.md             # Setup, usage, architecture, limitations
├── requirements.txt      # openai, (no other heavy deps)
└── PROJECT.md            # This file
```

---

## Testing Approach

- **Smoke tests**: Run both planned investigations against the real database; manually verify that every cited record or event ID exists in the database.
- **Tool unit tests**: For each tool, call it directly with known inputs and assert the output shape and key fields.
- **Adversarial prompts**: Ask questions that have no anomaly (e.g. a fully offboarded user with no residual access) and confirm the agent says "nothing found" rather than hallucinating findings.
- **Truncation test**: Verify that a result exceeding the token cap is trimmed and the `_meta.truncated` flag is set.

---

## Known Limitations (initial assessment)

- **Nested group resolution is bounded**: The `get_group_members` tool resolves groups to a max depth of 3. Deeper nesting may miss indirect access.
- **Audit log completeness**: The schema explicitly notes audit logs are incomplete. The agent is instructed to qualify conclusions that rest solely on the absence of an audit event.
- **No real-time data**: The database is a snapshot at `2026-08-15T12:00:00Z`. The agent cannot detect changes after that point.
- **`person_id` nulls**: Unmatched accounts are excluded from person-centric queries. The agent notes this gap but does not attempt fuzzy matching.
- **Service accounts**: GitHub service accounts and Workspace accounts without `person_id` may have significant permissions that person-centric investigations miss. A separate "unlinked account" query is planned but lower priority.

---

## What to Build Next

1. **Privilege escalation investigation**: detect accounts with admin roles added recently (join `idp_group_memberships` or `github_org_memberships` with `audit_events`).
2. **Cross-system access correlation**: given a person, show all permissions across all systems in one view with risk scoring.
3. **Automated summary report**: generate a daily/weekly HTML report of all open anomalies across the three investigation types.
4. **Deeper `run_sql` hardening**: parse and whitelist only `SELECT` statements if the escape hatch is needed in production.
5. **Confidence scoring**: attach a numeric confidence score to each finding based on how many corroborating evidence sources agree.

## Implementation Status

All core code is written and tested. The project is runnable from a clean checkout.

### Files

| File | Status | Purpose |
|---|---|---|
| `agent.py` | ✅ done | CLI entry point; ReAct loop with step budget and structured output |
| `tools.py` | ✅ done | 9 SQL-backed tool functions |
| `prompts.py` | ✅ done | System prompt + compact schema digest (~600 tokens) |
| `runner.py` | ✅ done | OpenRouter API wrapper (thin `openai` SDK shim) |
| `demo.py` | ✅ done | Quick launcher for three prepared demo investigations (offboarding, MFA, drive permissions) |
| `tests/test_tools.py` | ✅ done | 54 unit tests — all passing |
| `README.md` | ✅ done | Setup, usage, architecture, limitations |
| `requirements.txt` | ✅ done | `openai>=1.30.0`, `python-dotenv>=1.0.0` |
| `.env.example` | ✅ done | Key template; `.env` is git-ignored |

### Quick start for the next session

```bash
# 1. Activate the virtual environment (already created with uv)
source .venv/bin/activate

# 2. Make sure .env has the OpenRouter key
cp .env.example .env   # then fill in OPENROUTER_API_KEY

# 3. Run the prepared demos
python demo.py          # both demos
python demo.py 1        # offboarding gaps only
python demo.py 2        # MFA gaps only

# 4. Run an ad-hoc investigation
python agent.py "Which former employees still have active accounts?"
python agent.py --debug --steps 15 "Show drive permissions for ended employees"

# 5. Run tests
python -m pytest tests/ -v --timeout=20
```

---

## Debugging Gotchas Found During Implementation

### 1. `_trim()` infinite loop (fixed)

**Problem:** The original `_trim()` halved rows with `max(1, len//2)`. When a
single row was still over the char budget, `max(1, 0) == 1` kept the loop alive
forever. `get_mfa_gaps()` hit this because the 242-row `gaps` list, even trimmed
to 1, produced a result over 6 000 chars.

**Fix:** `_trim()` now explicitly drops to an empty list when a single row still
exceeds the budget and breaks. It also only trims a *primary* data list, leaving
small metadata lists (`summary_by_app`, `mfa_enrollment_stats`, `groups_visited`,
`recent_auth_events`) untouched. The primary key can be passed explicitly (e.g.
`_trim(result, primary_key="gaps")`) to avoid auto-detection ambiguity.

**Symptom to watch for:** A tool call that never returns (hangs indefinitely).

---

### 2. `get_mfa_gaps` — `summary_by_app` was being zeroed by trimming (fixed)

**Problem:** `_trim()` used to trim *all* list keys. `summary_by_app` appeared
first in `get_mfa_gaps`'s result dict, so it was the first thing halved. After
a few passes it was empty, making the `test_mfa_enrollment_stats_present` test
fail with `assert 0 > 0`.

**Fix:** Added `_PROTECTED_LIST_KEYS` — a frozenset of list keys that `_trim`
never touches. `summary_by_app` and similar small metadata lists are in this set.

---

### 3. `groups_visited` emptied by trimming (fixed, same root cause as #2)

**Problem:** `get_group_members` returns `groups_visited` as a plain Python list.
The old `_trim` was trimming it down to zero, causing
`test_groups_visited_includes_root` to fail.

**Fix:** `groups_visited` is now in `_PROTECTED_LIST_KEYS`.

---

### 4. `test_lookup_by_name_fragment` was over-specific (fixed in test)

**Problem:** The test searched for "Rowan" and asserted `per_001941` was in the
results. But there are 33 people named "Rowan" — the full result exceeds the
char budget, and `_trim` trims the `people` list so `per_001941` (at the end)
may not survive.

**Fix:** Test was updated to assert `len > 0` and that every returned person's
name contains "Rowan" — not that one specific person_id appears.

---

### 5. Stale model ID caused 404 on first real run (fixed)

**Problem:** The default model was set to `google/gemini-2.0-flash-001`, which
is no longer listed on OpenRouter. The first call to `python demo.py 1` returned
a 404.

**Fix:** Updated the default in `runner.py` to `google/gemini-2.5-flash`, which
is the current equivalent — same speed and cost tier, 1 M context window,
strong function-calling.

**Lesson:** Always verify model IDs against the live
`GET https://openrouter.ai/api/v1/models` endpoint before finalising defaults.

---

### 6. Agent exited silently on tool gap (fixed)

**Problem:** When demo 3 ("Show drive permissions for ended employees") ran, the
agent correctly identified that `get_drive_permissions` requires a specific
`account_id` or `resource_id` — it cannot enumerate permissions across an entire
cohort. However, instead of emitting a structured final answer, the model
returned a free-form question ("Would you like me to do that?") and the loop
terminated. The output was ambiguous and provided no actionable information.

**Root cause:** The system prompt had no instruction for the cannot-proceed case,
so the model fell back to conversational behaviour.

**Fix:** Added a "When you cannot proceed" section to `SYSTEM_PROMPT` in
`prompts.py`. The model is now required to emit the standard final-answer JSON
immediately, extended with a `cannot_proceed` object containing:
- `reason` — why the available tools are insufficient.
- `missing_capability` — a description of a tool that would enable the investigation, with a suggested name.
- `alternative_command` — a ready-to-paste CLI command for the closest supported investigation.

`_print_final_answer()` in `agent.py` detects the `cannot_proceed` key and
renders it under a distinct `⚠️  Cannot Proceed` header.

**Lesson:** Every failure mode visible to the user needs an explicit output
contract in the system prompt. Silent exits or free-form questions are not
acceptable outputs for a CLI tool.
