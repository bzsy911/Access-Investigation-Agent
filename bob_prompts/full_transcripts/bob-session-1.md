# read `bob_prompts/1-Initial-Planning.md` and follow its instructions.

---

**Status:** active  **Date:** 2026-09-24

---

### 👤 User

read `bob_prompts/1-Initial-Planning.md` and follow its instructions.

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — bob_prompts/1-Initial-planning.md

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — Problem_Description.md

> 🔧 **read_file** — input_data/SCHEMA.md

### 🤖 Assistant

> 🔧 called: execute_command

Now let me explore the database structure directly to understand what's available:

> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite ".tables"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
SELECT employment_status, COUNT(*) FROM people GROUP BY employment_status;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
SELECT status, COUNT(*) FROM idp_accounts GROUP BY status;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
SELECT event_type, system, COUNT(*) as n FROM audit_events GROUP BY event_type, system ORDER BY n DESC LIMIT 20;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
SELECT COUNT(*) FROM audit_events;
SELECT COUNT(*) FROM people;
SELECT COUNT(*) FROM idp_accounts;
SELECT COUNT(*) FROM application_user_access;
"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
-- Orphaned accounts: employment ended but account still active
SELECT COUNT(*) as orphaned_count FROM people p
JOIN idp_accounts ia ON ia.person_id = p.person_id
WHERE p.employment_status = 'ended' AND ia.status = 'active';
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- People on leave or ended with active github accounts
SELECT COUNT(*) FROM people p
JOIN github_accounts ga ON ga.person_id = p.person_id
WHERE p.employment_status IN ('ended','leave') AND ga.suspended_at IS NULL;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- Apps with mfa required but users not enrolled
SELECT COUNT(*) FROM application_user_access aua
JOIN applications a ON a.application_id = aua.application_id
WHERE a.default_mfa_requirement = 1 AND aua.mfa_enrollment_status != 'enrolled' AND aua.access_status = 'active';
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- Workspace oauth grants
SELECT COUNT(*) FROM workspace_oauth_grants;
SELECT COUNT(DISTINCT client_app_name) FROM workspace_oauth_grants;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- Drive permissions to external users
SELECT principal_type, COUNT(*) FROM drive_permissions GROUP BY principal_type;
"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite ".schema github_accounts" && echo "---" && sqlite3 input_data/access_snapshot.sqlite ".schema workspace_accounts" && echo "---" && sqlite3 input_data/access_snapshot.sqlite ".schema applications" && echo "---" && sqlite3 input_data/access_snapshot.sqlite ".schema application_user_access"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
-- Orphaned accounts detail
SELECT p.person_id, p.name, p.employment_status, ia.status as idp_status, ia.account_id
FROM people p JOIN idp_accounts ia ON ia.person_id = p.person_id
WHERE p.employment_status = 'ended' AND ia.status = 'active' LIMIT 5;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- GitHub orphans
SELECT COUNT(*) FROM people p
JOIN github_accounts ga ON ga.person_id = p.person_id
WHERE p.employment_status IN ('ended','leave') AND ga.status = 'active';
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- MFA non-enrolled on required apps
SELECT COUNT(*) FROM application_user_access aua
JOIN applications a ON a.application_id = aua.application_id
WHERE a.default_mfa_requirement = 'required' AND aua.mfa_enrollment_status != 'enrolled' AND aua.status = 'active';
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- External drive permissions
SELECT principal_type, COUNT(*) FROM drive_permissions WHERE revoked_at IS NULL GROUP BY principal_type;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- OAuth grants count
SELECT COUNT(*) FROM workspace_oauth_grants;
SELECT COUNT(DISTINCT client_app_name) FROM workspace_oauth_grants;
"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite ".schema people" && echo "---" && sqlite3 input_data/access_snapshot.sqlite ".schema drive_permissions" && echo "---" && sqlite3 input_data/access_snapshot.sqlite ".schema workspace_oauth_grants"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
-- Orphaned accounts: employment ended but idp account still active
SELECT p.person_id, p.full_name, p.employment_status, ia.status as idp_status, p.end_date
FROM people p JOIN idp_accounts ia ON ia.person_id = p.person_id
WHERE p.employment_status = 'ended' AND ia.status = 'active' LIMIT 5;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- GitHub orphans
SELECT COUNT(*) FROM people p
JOIN github_accounts ga ON ga.person_id = p.person_id
WHERE p.employment_status IN ('ended','leave') AND ga.status = 'active';
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- MFA non-enrolled on required apps
SELECT COUNT(*) FROM application_user_access aua
JOIN applications a ON a.application_id = aua.application_id
WHERE a.default_mfa_requirement = 'required' AND aua.mfa_enrollment_status != 'enrolled' AND aua.status = 'active';
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- External drive permissions
SELECT principal_type, COUNT(*) FROM drive_permissions WHERE revoked_at IS NULL GROUP BY principal_type;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
SELECT COUNT(*) FROM workspace_oauth_grants WHERE revoked_at IS NULL;
SELECT COUNT(DISTINCT application_name) FROM workspace_oauth_grants WHERE revoked_at IS NULL;
" && echo "---" && sqlite3 input_data/access_snapshot.sqlite "
-- Sensitivity levels for apps
SELECT sensitivity, default_mfa_requirement, COUNT(*) FROM applications GROUP BY sensitivity, default_mfa_requirement;
"

### 🤖 Assistant

> 🔧 called: write_file

Now I have a solid picture. Let me write the plan:

> 🔧 **write_file** — PROJECT.md

### 🤖 Assistant

[`PROJECT.md`](PROJECT.md) has been written. Here is a summary of the plan and the reasoning behind each decision:

---

## Plan summary

### Agent design: ReAct loop, single-threaded

A single model running a Reason-then-Act loop is the right fit. Investigations are inherently iterative (first query surfaces an anomaly, follow-up queries gather evidence), and one agent calling a series of named tools is both simpler and more auditable than any multi-agent pattern. The loop terminates when the model emits a structured final answer containing evidence IDs, or when a step budget of 12 tool calls is exhausted.

### Model: `google/gemini-2.0-flash-001` via OpenRouter

Balances reasoning quality, a 1 M-token context window (essential for holding multiple query results), and low cost. Claude 3.5 Sonnet would reason slightly better but costs ~6× more per token. GPT-4o-mini is cheapest but weaker at multi-hop relational reasoning. Gemini 2.5 Pro is overkill for a 4-hour timebox.

### Easiest investigations to start with

1. **Offboarding residual access** — clear anomaly definition (`employment_status = 'ended'` + active account), all data in snapshot tables, high business value, produces concrete record IDs. The database already shows 3 people with ended employment and active IdP accounts.
2. **MFA gap analysis** — contained to two tables (`applications` + `application_user_access`), natural risk tiers by sensitivity, the database shows 242 active users on `required`-MFA apps who are not enrolled.

### Minimal tool set (8 tools)

`lookup_person`, `find_offboarding_gaps`, `get_person_access_summary`, `get_mfa_gaps`, `get_audit_events`, `get_application_summary`, `get_drive_permissions`, `get_group_members` — plus a `run_sql` escape hatch disabled by default. The model never writes SQL; it calls named tools with structured arguments. Every tool returns a `_meta` field with count, truncation flag, and query time.

### Agent techniques

**Include:** compact schema digest in system prompt (~600 tokens, not the full SCHEMA.md), step budget cap, structured final-answer JSON contract, per-tool result truncation.

**Exclude:** RAG (schema is small and stable), prompt caching (session too short), trajectory compression (1 M context window, no need), injection guardrails (tools are read-only SQL, `run_sql` disabled), multi-agent orchestration (adds complexity with no benefit at this scope), memory/persistence (stateless per-investigation).

---

### 👤 User

As said in `bob_prompts/2-Coding.md`, write down the code for the project.

---

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — PROJECT.md

> 🔧 **read_file** — bob_prompts/2-Coding.md

### 🤖 Assistant

> 🔧 called: execute_command

Let me also do a quick sanity-check on a few more DB details needed for the tools:

> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
.schema idp_accounts
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
.schema idp_groups
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
.schema idp_group_memberships
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
.schema idp_app_assignments
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
.schema github_team_memberships
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
.schema github_repo_collaborators
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
.schema audit_events
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
.schema workspace_group_memberships
"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite ".schema idp_accounts" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema idp_groups" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema idp_group_memberships" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema idp_app_assignments" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema github_team_memberships" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema github_repo_collaborators" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema audit_events" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema workspace_group_memberships"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite ".schema drive_resources" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema github_repositories" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema github_teams" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema github_org_memberships" && echo "===" && sqlite3 input_data/access_snapshot.sqlite ".schema devices"

### 🤖 Assistant

> 🔧 called: update_todo_list

Good. Now I have all the schemas. Let me build all the files:

> 🔧 **update_todo_list** — 
[-] Write requirements.txt and .env.example
[ ] Write prompts.py — system prompt and schema digest
[ ] Write tools.py — all 9 tool implementations
[ ] Write runner.py — OpenRouter API client wrapper
[ ] Write agent.py — CLI entry point and ReAct loop
[ ] Write tests/test_tools.py — tool unit tests
[ ] Write README.md — setup, usage, architecture, limitations
[ ] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: write_file, write_file



> 🔧 **write_file** — .env.example

> 🔧 **write_file** — requirements.txt

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[-] Write prompts.py — system prompt and schema digest
[ ] Write tools.py — all 9 tool implementations
[ ] Write runner.py — OpenRouter API client wrapper
[ ] Write agent.py — CLI entry point and ReAct loop
[ ] Write tests/test_tools.py — tool unit tests
[ ] Write README.md — setup, usage, architecture, limitations
[ ] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — """
prompts.py — System prompt and schema digest for the Access Investigation Agent.

The schema digest is a deliberately compressed version of SCHEMA.md.
It gives the model just enough to reason about table relationships and
anomaly definitions without sending the entire schema.
"""

SCHEMA_DIGEST = """
## Database snapshot — 2026-08-15T12:00:00Z  (read-only SQLite)

### Key tables

**people** (person_id PK, full_name, primary_email, worker_type, department,
  title, manager_person_id, employment_status[active|ended|leave|prehire],
  start_date, end_date, location)

**idp_accounts** (account_id PK, person_id FK, username, status[active|suspended|deprovisioned],
  created_at, deactivated_at, last_login_at)

**idp_groups** (group_id PK, name, description, management_type[manual|hr_sync|application_sync],
  rule_expression, created_at)

**idp_group_memberships** (membership_id PK, group_id FK, member_type[account|group],
  member_id, source[manual|hr_sync|group_nesting], granted_at, revoked_at)
  — revoked_at IS NULL means active

**idp_app_assignments** (assignment_id PK, application_id FK, principal_type[account|group],
  principal_id, role, granted_at, revoked_at)

**applications** (application_id PK, name, category, sensitivity[standard|sensitive|critical],
  authentication_mode[sso|local|mixed], default_mfa_requirement[required|conditional|optional])

**application_user_access** (access_id PK, application_id FK, idp_account_id FK,
  role, status[active|suspended|revoked], provisioning_source,
  assigned_at, revoked_at,
  mfa_enrollment_status[enrolled|not_enrolled|unknown],
  mfa_methods_json, last_authenticated_at, last_mfa_at)

**workspace_accounts** (account_id PK, person_id FK, primary_email,
  status[active|suspended|archived], created_at, last_login_at)

**workspace_groups** (group_id PK, name, description)

**workspace_group_memberships** (membership_id PK, group_id FK,
  member_type[account|group], member_id, role, source, granted_at, revoked_at)

**workspace_oauth_grants** (grant_id PK, account_id FK, application_name,
  client_id, scopes_json, granted_at, last_used_at, revoked_at)

**drive_resources** (resource_id PK, name, resource_type[file|folder|shared_drive],
  owner_account_id, classification[public|internal|confidential|restricted])

**drive_permissions** (permission_id PK, resource_id FK,
  principal_type[account|group|domain|external_email], principal_id,
  role[viewer|commenter|editor|manager], granted_at, expires_at, revoked_at)

**github_accounts** (account_id PK, person_id FK, login, account_type[user|service],
  status[active|suspended], created_at, last_active_at)

**github_org_memberships** (membership_id PK, account_id FK,
  org_role[member|owner], source, granted_at, revoked_at)

**github_teams** (team_id PK, name, description, source_idp_group_id FK)

**github_team_memberships** (membership_id PK, team_id FK, account_id FK,
  role[member|maintainer], source, granted_at, revoked_at)

**github_repositories** (repository_id PK, name, visibility[private|internal|public],
  sensitivity[standard|sensitive|production_critical], archived[0|1])

**github_team_repo_permissions** (permission_id PK, team_id FK, repository_id FK,
  permission[read|triage|write|maintain|admin], granted_at, revoked_at)

**github_repo_collaborators** (permission_id PK, account_id FK, repository_id FK,
  permission[read|triage|write|maintain|admin], granted_at, expires_at, revoked_at)

**devices** (device_id PK, person_id FK, serial_number, platform, ownership,
  compliance_status[compliant|noncompliant|unknown], enrolled_at, last_check_in_at, retired_at)

**audit_events** (event_id PK, occurred_at, system[hr|idp|workspace|github|mdm],
  event_type, actor_type[account|service|system|unknown], actor_id,
  target_type, target_id, source, outcome[success|failure|partial],
  ip_address, correlation_id, details_json)

### Critical rules
- revoked_at IS NULL  → relationship is still active
- employment_status='ended' + active account = offboarding gap
- group memberships can be nested (member_type='group'); use get_group_members to resolve
- person_id NULL on accounts/devices means unmatched — not necessarily bad
- audit logs are INCOMPLETE; absence of an event does not prove absence of activity
""".strip()

SYSTEM_PROMPT = f"""
You are an Access Investigation Agent for a corporate security team. You help
investigate potential access-control issues by querying a read-only database of
HR, identity, Workspace, GitHub, and device management records.

## Your capabilities

You have access to a set of named tools that query the database. You must only
use these tools — never ask the user for raw data, never assume data you have
not retrieved. If a tool result is truncated, call it again with a narrower
filter or accept the limitation and note it in your answer.

## How to investigate

Think step by step. Start with the broadest relevant tool, interpret the results,
then drill down with more specific tools. Keep track of all record IDs you
discover — they are your evidence.

## Step budget

You have a budget of 12 tool calls per investigation. If you approach the limit,
stop gathering and summarise what you have. Never exceed the budget.

## How to answer

When you have gathered enough evidence (or exhausted the budget), output your
final answer in this exact format:

```json
{{
  "conclusion": "Plain-language summary of what you found.",
  "findings": [
    {{
      "description": "Specific finding with context.",
      "severity": "high|medium|low",
      "evidence_ids": ["id1", "id2"]
    }}
  ],
  "uncertainty": "What you could not determine and why.",
  "steps_used": <integer>
}}
```

Do not include this JSON block until you are ready to give your final answer.
Before the JSON, you may write brief reasoning notes.

## Evidence discipline

- Cite every record ID or event ID that supports a conclusion.
- Clearly separate facts (what the database shows) from inferences.
- If the data is ambiguous or incomplete, say so explicitly in `uncertainty`.
- Never invent or extrapolate record IDs.

## Database summary

{SCHEMA_DIGEST}
""".strip()


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[x] Write prompts.py — system prompt and schema digest
[-] Write tools.py — all 9 tool implementations
[ ] Write runner.py — OpenRouter API client wrapper
[ ] Write agent.py — CLI entry point and ReAct loop
[ ] Write tests/test_tools.py — tool unit tests
[ ] Write README.md — setup, usage, architecture, limitations
[ ] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — """
tools.py — All tool implementations for the Access Investigation Agent.

Design principles:
- Every tool opens the database read-only and applies PRAGMA query_only=ON.
- Results are capped at MAX_ROWS (default 50) to control context size.
- Every result includes a _meta dict with total_count, returned, truncated, query_time_ms.
- Token budget: each result is trimmed to ~2000 tokens worth of text.
- The model never writes SQL; it calls these named functions.
"""

import json
import os
import sqlite3
import time
from typing import Any

DB_PATH = os.environ.get("DB_PATH", "input_data/access_snapshot.sqlite")
MAX_ROWS = 50
# Approximate character budget for result JSON (chars ≈ tokens for ASCII)
CHAR_BUDGET = 6000
# Maximum recursion depth for group expansion
MAX_GROUP_DEPTH = 3


def _connect() -> sqlite3.Connection:
    """Open a read-only connection to the snapshot database."""
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def _trim(result: dict) -> dict:
    """Serialise result to JSON; if over budget, drop rows until it fits."""
    text = json.dumps(result)
    if len(text) <= CHAR_BUDGET:
        return result
    # Trim rows list progressively
    rows_key = next((k for k in result if isinstance(result[k], list)), None)
    if rows_key is None:
        return result
    rows = result[rows_key]
    while rows and len(json.dumps(result)) > CHAR_BUDGET:
        rows = rows[: max(1, len(rows) // 2)]
        result = {**result, rows_key: rows}
    result["_meta"]["truncated"] = True
    result["_meta"]["returned"] = len(rows)
    return result


def _meta(total: int, returned: int, t0: float, truncated: bool = False) -> dict:
    return {
        "total_count": total,
        "returned": returned,
        "truncated": truncated,
        "query_time_ms": round((time.monotonic() - t0) * 1000),
    }


# ---------------------------------------------------------------------------
# Tool 1 — lookup_person
# ---------------------------------------------------------------------------

LOOKUP_PERSON_SCHEMA = {
    "name": "lookup_person",
    "description": (
        "Look up a person by name (full or partial), email address, or person_id. "
        "Returns their HR record and a list of all linked accounts across systems."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Name fragment, email, or person_id to search for.",
            }
        },
        "required": ["query"],
    },
}


def lookup_person(query: str) -> dict:
    t0 = time.monotonic()
    conn = _connect()
    try:
        q = f"%{query}%"
        people = _rows_to_dicts(
            conn.execute(
                """
                SELECT person_id, full_name, primary_email, worker_type, department,
                       title, employment_status, start_date, end_date
                FROM people
                WHERE person_id = ?
                   OR full_name LIKE ?
                   OR primary_email LIKE ?
                ORDER BY full_name
                LIMIT ?
                """,
                (query, q, q, MAX_ROWS),
            ).fetchall()
        )
        if not people:
            return {
                "people": [],
                "_meta": _meta(0, 0, t0),
                "note": "No matching person found.",
            }

        # For each person, collect their linked accounts
        for person in people:
            pid = person["person_id"]
            person["accounts"] = {}

            idp = conn.execute(
                "SELECT account_id, username, status, last_login_at FROM idp_accounts WHERE person_id=?",
                (pid,),
            ).fetchall()
            person["accounts"]["idp"] = _rows_to_dicts(idp)

            ws = conn.execute(
                "SELECT account_id, primary_email, status, last_login_at FROM workspace_accounts WHERE person_id=?",
                (pid,),
            ).fetchall()
            person["accounts"]["workspace"] = _rows_to_dicts(ws)

            gh = conn.execute(
                "SELECT account_id, login, account_type, status, last_active_at FROM github_accounts WHERE person_id=?",
                (pid,),
            ).fetchall()
            person["accounts"]["github"] = _rows_to_dicts(gh)

            dev = conn.execute(
                "SELECT device_id, platform, ownership, compliance_status, retired_at FROM devices WHERE person_id=?",
                (pid,),
            ).fetchall()
            person["accounts"]["devices"] = _rows_to_dicts(dev)

        result = {
            "people": people,
            "_meta": _meta(len(people), len(people), t0),
        }
        return _trim(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 2 — find_offboarding_gaps
# ---------------------------------------------------------------------------

FIND_OFFBOARDING_GAPS_SCHEMA = {
    "name": "find_offboarding_gaps",
    "description": (
        "Find people whose employment has ended (or is on leave) but who still have "
        "at least one active account in the specified system(s). "
        "Returns person details and the offending active accounts."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "statuses": {
                "type": "array",
                "items": {"type": "string", "enum": ["ended", "leave"]},
                "description": "Employment statuses to check. Defaults to ['ended'].",
            },
            "systems": {
                "type": "array",
                "items": {"type": "string", "enum": ["idp", "workspace", "github"]},
                "description": "Systems to check. Defaults to all three.",
            },
        },
        "required": [],
    },
}


def find_offboarding_gaps(
    statuses: list[str] | None = None,
    systems: list[str] | None = None,
) -> dict:
    t0 = time.monotonic()
    if statuses is None:
        statuses = ["ended"]
    if systems is None:
        systems = ["idp", "workspace", "github"]

    conn = _connect()
    try:
        status_placeholders = ",".join("?" * len(statuses))
        people = _rows_to_dicts(
            conn.execute(
                f"""
                SELECT person_id, full_name, primary_email, department,
                       employment_status, end_date
                FROM people
                WHERE employment_status IN ({status_placeholders})
                ORDER BY end_date DESC
                """,
                statuses,
            ).fetchall()
        )

        gaps = []
        for person in people:
            pid = person["person_id"]
            active_accounts: dict[str, list] = {}

            if "idp" in systems:
                rows = conn.execute(
                    "SELECT account_id, username, status FROM idp_accounts WHERE person_id=? AND status='active'",
                    (pid,),
                ).fetchall()
                if rows:
                    active_accounts["idp"] = _rows_to_dicts(rows)

            if "workspace" in systems:
                rows = conn.execute(
                    "SELECT account_id, primary_email, status FROM workspace_accounts WHERE person_id=? AND status='active'",
                    (pid,),
                ).fetchall()
                if rows:
                    active_accounts["workspace"] = _rows_to_dicts(rows)

            if "github" in systems:
                rows = conn.execute(
                    "SELECT account_id, login, account_type, status FROM github_accounts WHERE person_id=? AND status='active'",
                    (pid,),
                ).fetchall()
                if rows:
                    active_accounts["github"] = _rows_to_dicts(rows)

            if active_accounts:
                gaps.append({**person, "active_accounts": active_accounts})

        result = {
            "gaps": gaps[:MAX_ROWS],
            "_meta": _meta(len(gaps), min(len(gaps), MAX_ROWS), t0, len(gaps) > MAX_ROWS),
        }
        return _trim(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 3 — get_person_access_summary
# ---------------------------------------------------------------------------

GET_PERSON_ACCESS_SUMMARY_SCHEMA = {
    "name": "get_person_access_summary",
    "description": (
        "Return a full access summary for a specific person: all accounts, "
        "IdP group memberships, application access (with MFA status), "
        "active drive permissions, and active GitHub collaborator permissions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "person_id": {
                "type": "string",
                "description": "The person_id from the people table.",
            }
        },
        "required": ["person_id"],
    },
}


def get_person_access_summary(person_id: str) -> dict:
    t0 = time.monotonic()
    conn = _connect()
    try:
        person = conn.execute(
            "SELECT person_id, full_name, primary_email, department, employment_status, end_date FROM people WHERE person_id=?",
            (person_id,),
        ).fetchone()
        if not person:
            return {"error": f"No person found with person_id={person_id!r}", "_meta": _meta(0, 0, t0)}

        person = dict(person)

        # IdP accounts + their group memberships
        idp_accounts = _rows_to_dicts(
            conn.execute(
                "SELECT account_id, username, status FROM idp_accounts WHERE person_id=?",
                (person_id,),
            ).fetchall()
        )
        for acct in idp_accounts:
            memberships = conn.execute(
                """
                SELECT m.membership_id, g.group_id, g.name as group_name,
                       g.management_type, m.source, m.granted_at
                FROM idp_group_memberships m
                JOIN idp_groups g ON g.group_id = m.group_id
                WHERE m.member_type='account' AND m.member_id=? AND m.revoked_at IS NULL
                """,
                (acct["account_id"],),
            ).fetchall()
            acct["idp_group_memberships"] = _rows_to_dicts(memberships)

        # Application access
        app_access = _rows_to_dicts(
            conn.execute(
                """
                SELECT aua.access_id, a.application_id, a.name as app_name,
                       a.sensitivity, a.default_mfa_requirement,
                       aua.role, aua.status, aua.mfa_enrollment_status,
                       aua.last_authenticated_at, aua.last_mfa_at
                FROM application_user_access aua
                JOIN applications a ON a.application_id = aua.application_id
                JOIN idp_accounts ia ON ia.account_id = aua.idp_account_id
                WHERE ia.person_id=? AND aua.status='active'
                ORDER BY a.sensitivity DESC, a.name
                """,
                (person_id,),
            ).fetchall()
        )

        # Workspace accounts + drive permissions
        ws_accounts = _rows_to_dicts(
            conn.execute(
                "SELECT account_id, primary_email, status FROM workspace_accounts WHERE person_id=?",
                (person_id,),
            ).fetchall()
        )
        drive_permissions = []
        for ws in ws_accounts:
            perms = conn.execute(
                """
                SELECT dp.permission_id, dr.resource_id, dr.name as resource_name,
                       dr.classification, dp.role, dp.granted_at, dp.expires_at
                FROM drive_permissions dp
                JOIN drive_resources dr ON dr.resource_id = dp.resource_id
                WHERE dp.principal_type='account' AND dp.principal_id=?
                  AND dp.revoked_at IS NULL
                ORDER BY dr.classification DESC
                LIMIT 50
                """,
                (ws["account_id"],),
            ).fetchall()
            drive_permissions.extend(_rows_to_dicts(perms))

        # GitHub collaborator permissions
        gh_accounts = _rows_to_dicts(
            conn.execute(
                "SELECT account_id, login, account_type, status FROM github_accounts WHERE person_id=?",
                (person_id,),
            ).fetchall()
        )
        github_permissions = []
        for gh in gh_accounts:
            collabs = conn.execute(
                """
                SELECT rc.permission_id, r.repository_id, r.name as repo_name,
                       r.sensitivity, r.visibility, rc.permission, rc.granted_at
                FROM github_repo_collaborators rc
                JOIN github_repositories r ON r.repository_id = rc.repository_id
                WHERE rc.account_id=? AND rc.revoked_at IS NULL
                """,
                (gh["account_id"],),
            ).fetchall()
            github_permissions.extend(_rows_to_dicts(collabs))

            team_perms = conn.execute(
                """
                SELECT tm.membership_id, gt.name as team_name,
                       gtr.permission, r.repository_id, r.name as repo_name, r.sensitivity
                FROM github_team_memberships tm
                JOIN github_teams gt ON gt.team_id = tm.team_id
                JOIN github_team_repo_permissions gtr ON gtr.team_id = tm.team_id
                JOIN github_repositories r ON r.repository_id = gtr.repository_id
                WHERE tm.account_id=? AND tm.revoked_at IS NULL AND gtr.revoked_at IS NULL
                """,
                (gh["account_id"],),
            ).fetchall()
            github_permissions.extend([{**dict(r), "_via": "team"} for r in team_perms])

        result = {
            "person": person,
            "idp_accounts": idp_accounts,
            "application_access": app_access,
            "workspace_accounts": ws_accounts,
            "drive_permissions": drive_permissions[:MAX_ROWS],
            "github_accounts": gh_accounts,
            "github_permissions": github_permissions[:MAX_ROWS],
            "_meta": _meta(1, 1, t0),
        }
        return _trim(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 4 — get_mfa_gaps
# ---------------------------------------------------------------------------

GET_MFA_GAPS_SCHEMA = {
    "name": "get_mfa_gaps",
    "description": (
        "Find active users on sensitive or critical applications who are not enrolled in MFA. "
        "Optionally filter by a specific application_id or minimum sensitivity level."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sensitivity": {
                "type": "string",
                "enum": ["sensitive", "critical"],
                "description": "Minimum sensitivity level. Defaults to 'sensitive' (includes both sensitive and critical).",
            },
            "application_id": {
                "type": "string",
                "description": "Optional: restrict to a single application.",
            },
            "mfa_required_only": {
                "type": "boolean",
                "description": "If true, only return gaps for apps where default_mfa_requirement='required'.",
            },
        },
        "required": [],
    },
}


def get_mfa_gaps(
    sensitivity: str = "sensitive",
    application_id: str | None = None,
    mfa_required_only: bool = False,
) -> dict:
    t0 = time.monotonic()
    conn = _connect()
    try:
        sensitivity_filter = (
            "a.sensitivity = 'critical'"
            if sensitivity == "critical"
            else "a.sensitivity IN ('sensitive', 'critical')"
        )
        mfa_filter = "AND a.default_mfa_requirement = 'required'" if mfa_required_only else ""
        app_filter = "AND a.application_id = ?" if application_id else ""
        params: list[Any] = []
        if application_id:
            params.append(application_id)

        query = f"""
            SELECT aua.access_id, a.application_id, a.name as app_name,
                   a.sensitivity, a.default_mfa_requirement,
                   aua.idp_account_id, ia.username, ia.person_id,
                   p.full_name, p.employment_status,
                   aua.mfa_enrollment_status, aua.last_authenticated_at
            FROM application_user_access aua
            JOIN applications a ON a.application_id = aua.application_id
            JOIN idp_accounts ia ON ia.account_id = aua.idp_account_id
            LEFT JOIN people p ON p.person_id = ia.person_id
            WHERE {sensitivity_filter}
              AND aua.status = 'active'
              AND aua.mfa_enrollment_status != 'enrolled'
              {mfa_filter}
              {app_filter}
            ORDER BY a.sensitivity DESC, a.name, p.full_name
        """
        rows = _rows_to_dicts(conn.execute(query, params).fetchall())
        total = len(rows)
        returned_rows = rows[:MAX_ROWS]

        # Summarise by application for quick overview
        by_app: dict[str, dict] = {}
        for row in rows:
            aid = row["application_id"]
            if aid not in by_app:
                by_app[aid] = {
                    "application_id": aid,
                    "app_name": row["app_name"],
                    "sensitivity": row["sensitivity"],
                    "default_mfa_requirement": row["default_mfa_requirement"],
                    "gap_count": 0,
                }
            by_app[aid]["gap_count"] += 1

        result = {
            "summary_by_app": list(by_app.values()),
            "gaps": returned_rows,
            "_meta": _meta(total, len(returned_rows), t0, total > MAX_ROWS),
        }
        return _trim(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 5 — get_audit_events
# ---------------------------------------------------------------------------

GET_AUDIT_EVENTS_SCHEMA = {
    "name": "get_audit_events",
    "description": (
        "Return audit events for a given actor or target ID. "
        "Filter by system, event_type, and/or a since timestamp. "
        "Always provide at least one of actor_id or target_id."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "actor_id": {
                "type": "string",
                "description": "Actor ID to filter by (e.g. an account_id or person_id).",
            },
            "target_id": {
                "type": "string",
                "description": "Target ID to filter by.",
            },
            "system": {
                "type": "string",
                "enum": ["hr", "idp", "workspace", "github", "mdm"],
                "description": "Restrict to events from this system.",
            },
            "event_type": {
                "type": "string",
                "description": "Restrict to this event_type (e.g. 'user.login', 'repository.pushed').",
            },
            "since": {
                "type": "string",
                "description": "ISO 8601 datetime; only return events at or after this time.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of events to return (default 30, max 100).",
            },
        },
        "required": [],
    },
}


def get_audit_events(
    actor_id: str | None = None,
    target_id: str | None = None,
    system: str | None = None,
    event_type: str | None = None,
    since: str | None = None,
    limit: int = 30,
) -> dict:
    t0 = time.monotonic()
    if actor_id is None and target_id is None:
        return {
            "error": "Provide at least one of actor_id or target_id.",
            "_meta": _meta(0, 0, t0),
        }
    limit = min(limit, 100)

    conn = _connect()
    try:
        conditions: list[str] = []
        params: list[Any] = []

        if actor_id:
            conditions.append("actor_id = ?")
            params.append(actor_id)
        if target_id:
            conditions.append("target_id = ?")
            params.append(target_id)
        if system:
            conditions.append("system = ?")
            params.append(system)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if since:
            conditions.append("occurred_at >= ?")
            params.append(since)

        where = " AND ".join(conditions)
        # Count total
        total = conn.execute(
            f"SELECT COUNT(*) FROM audit_events WHERE {where}", params
        ).fetchone()[0]

        params.append(limit)
        rows = _rows_to_dicts(
            conn.execute(
                f"""
                SELECT event_id, occurred_at, system, event_type,
                       actor_type, actor_id, target_type, target_id,
                       outcome, ip_address, details_json
                FROM audit_events
                WHERE {where}
                ORDER BY occurred_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        )
        # Parse details_json inline for readability
        for row in rows:
            try:
                row["details"] = json.loads(row.pop("details_json", "{}"))
            except (json.JSONDecodeError, TypeError):
                pass

        result = {
            "events": rows,
            "_meta": _meta(total, len(rows), t0, total > limit),
        }
        return _trim(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 6 — get_application_summary
# ---------------------------------------------------------------------------

GET_APPLICATION_SUMMARY_SCHEMA = {
    "name": "get_application_summary",
    "description": (
        "Return metadata for an application plus a breakdown of active user access "
        "(with MFA enrollment stats) and the most recent authentication events."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "application_id": {
                "type": "string",
                "description": "The application_id to summarise.",
            },
            "app_name": {
                "type": "string",
                "description": "Partial or full application name to look up if application_id is not known.",
            },
        },
        "required": [],
    },
}


def get_application_summary(
    application_id: str | None = None,
    app_name: str | None = None,
) -> dict:
    t0 = time.monotonic()
    if not application_id and not app_name:
        return {
            "error": "Provide application_id or app_name.",
            "_meta": _meta(0, 0, t0),
        }
    conn = _connect()
    try:
        if application_id:
            app = conn.execute(
                "SELECT * FROM applications WHERE application_id=?", (application_id,)
            ).fetchone()
        else:
            app = conn.execute(
                "SELECT * FROM applications WHERE name LIKE ? ORDER BY name LIMIT 1",
                (f"%{app_name}%",),
            ).fetchone()
        if not app:
            return {"error": "Application not found.", "_meta": _meta(0, 0, t0)}

        app = dict(app)
        aid = app["application_id"]

        # MFA enrollment breakdown
        mfa_stats = _rows_to_dicts(
            conn.execute(
                """
                SELECT mfa_enrollment_status, COUNT(*) as count
                FROM application_user_access
                WHERE application_id=? AND status='active'
                GROUP BY mfa_enrollment_status
                """,
                (aid,),
            ).fetchall()
        )

        # Active users sample
        users = _rows_to_dicts(
            conn.execute(
                """
                SELECT aua.access_id, aua.idp_account_id, ia.username, p.full_name,
                       p.employment_status, aua.role, aua.mfa_enrollment_status,
                       aua.last_authenticated_at
                FROM application_user_access aua
                JOIN idp_accounts ia ON ia.account_id = aua.idp_account_id
                LEFT JOIN people p ON p.person_id = ia.person_id
                WHERE aua.application_id=? AND aua.status='active'
                ORDER BY aua.last_authenticated_at DESC NULLS LAST
                LIMIT ?
                """,
                (aid, MAX_ROWS),
            ).fetchall()
        )

        # Recent authentication events
        auth_events = _rows_to_dicts(
            conn.execute(
                """
                SELECT event_id, occurred_at, actor_id, actor_type, outcome, ip_address, details_json
                FROM audit_events
                WHERE system='idp' AND event_type='application.authentication'
                  AND target_id=?
                ORDER BY occurred_at DESC
                LIMIT 20
                """,
                (aid,),
            ).fetchall()
        )
        for e in auth_events:
            try:
                e["details"] = json.loads(e.pop("details_json", "{}"))
            except (json.JSONDecodeError, TypeError):
                pass

        result = {
            "application": app,
            "mfa_enrollment_stats": mfa_stats,
            "active_users_sample": users,
            "recent_auth_events": auth_events,
            "_meta": _meta(1, 1, t0),
        }
        return _trim(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 7 — get_drive_permissions
# ---------------------------------------------------------------------------

GET_DRIVE_PERMISSIONS_SCHEMA = {
    "name": "get_drive_permissions",
    "description": (
        "Return non-revoked Drive permissions for a specific resource or for all "
        "resources owned/accessible by a given Workspace account. "
        "Flags external_email and domain-wide permissions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "resource_id": {
                "type": "string",
                "description": "Drive resource_id to inspect.",
            },
            "account_id": {
                "type": "string",
                "description": "Workspace account_id — returns permissions on all resources this account has access to.",
            },
            "highlight_external": {
                "type": "boolean",
                "description": "If true, only return external_email or domain permissions.",
            },
        },
        "required": [],
    },
}


def get_drive_permissions(
    resource_id: str | None = None,
    account_id: str | None = None,
    highlight_external: bool = False,
) -> dict:
    t0 = time.monotonic()
    if not resource_id and not account_id:
        return {"error": "Provide resource_id or account_id.", "_meta": _meta(0, 0, t0)}

    conn = _connect()
    try:
        conditions = ["dp.revoked_at IS NULL"]
        params: list[Any] = []

        if resource_id:
            conditions.append("dp.resource_id = ?")
            params.append(resource_id)
        if account_id:
            conditions.append("dp.principal_type = 'account' AND dp.principal_id = ?")
            params.append(account_id)
        if highlight_external:
            conditions.append("dp.principal_type IN ('external_email', 'domain')")

        where = " AND ".join(conditions)
        total = conn.execute(
            f"SELECT COUNT(*) FROM drive_permissions dp WHERE {where}", params
        ).fetchone()[0]

        params.append(MAX_ROWS)
        rows = _rows_to_dicts(
            conn.execute(
                f"""
                SELECT dp.permission_id, dp.resource_id,
                       dr.name as resource_name, dr.classification,
                       dp.principal_type, dp.principal_id, dp.role,
                       dp.granted_at, dp.expires_at
                FROM drive_permissions dp
                JOIN drive_resources dr ON dr.resource_id = dp.resource_id
                WHERE {where}
                ORDER BY dr.classification DESC, dp.principal_type
                LIMIT ?
                """,
                params,
            ).fetchall()
        )

        result = {
            "permissions": rows,
            "_meta": _meta(total, len(rows), t0, total > MAX_ROWS),
        }
        return _trim(result)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 8 — get_group_members
# ---------------------------------------------------------------------------

GET_GROUP_MEMBERS_SCHEMA = {
    "name": "get_group_members",
    "description": (
        "Resolve all members of an IdP group or Workspace group, "
        "recursively expanding nested groups up to 3 levels deep. "
        "Returns both direct and indirect (resolved) account members."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "The group_id to resolve.",
            },
            "group_type": {
                "type": "string",
                "enum": ["idp", "workspace"],
                "description": "Whether this is an IdP or Workspace group.",
            },
        },
        "required": ["group_id", "group_type"],
    },
}


def get_group_members(group_id: str, group_type: str = "idp") -> dict:
    t0 = time.monotonic()
    conn = _connect()
    try:
        if group_type == "idp":
            return _resolve_idp_group(conn, group_id, t0)
        else:
            return _resolve_workspace_group(conn, group_id, t0)
    finally:
        conn.close()


def _resolve_idp_group(conn: sqlite3.Connection, group_id: str, t0: float) -> dict:
    group = conn.execute(
        "SELECT group_id, name, description, management_type FROM idp_groups WHERE group_id=?",
        (group_id,),
    ).fetchone()
    if not group:
        return {"error": f"IdP group {group_id!r} not found.", "_meta": _meta(0, 0, t0)}

    resolved_accounts: list[dict] = []
    visited_groups: set[str] = set()

    def expand(gid: str, depth: int) -> None:
        if depth > MAX_GROUP_DEPTH or gid in visited_groups:
            return
        visited_groups.add(gid)
        members = conn.execute(
            "SELECT member_type, member_id, source FROM idp_group_memberships WHERE group_id=? AND revoked_at IS NULL",
            (gid,),
        ).fetchall()
        for m in members:
            if m["member_type"] == "account":
                acct = conn.execute(
                    "SELECT account_id, username, person_id, status FROM idp_accounts WHERE account_id=?",
                    (m["member_id"],),
                ).fetchone()
                if acct:
                    resolved_accounts.append(
                        {**dict(acct), "_source": m["source"], "_depth": depth}
                    )
            elif m["member_type"] == "group":
                expand(m["member_id"], depth + 1)

    expand(group_id, 0)

    result = {
        "group": dict(group),
        "resolved_accounts": resolved_accounts[:MAX_ROWS],
        "groups_visited": list(visited_groups),
        "_meta": _meta(
            len(resolved_accounts),
            min(len(resolved_accounts), MAX_ROWS),
            t0,
            len(resolved_accounts) > MAX_ROWS,
        ),
    }
    return _trim(result)


def _resolve_workspace_group(conn: sqlite3.Connection, group_id: str, t0: float) -> dict:
    group = conn.execute(
        "SELECT group_id, name, description FROM workspace_groups WHERE group_id=?",
        (group_id,),
    ).fetchone()
    if not group:
        return {"error": f"Workspace group {group_id!r} not found.", "_meta": _meta(0, 0, t0)}

    resolved_accounts: list[dict] = []
    visited_groups: set[str] = set()

    def expand(gid: str, depth: int) -> None:
        if depth > MAX_GROUP_DEPTH or gid in visited_groups:
            return
        visited_groups.add(gid)
        members = conn.execute(
            "SELECT member_type, member_id, role FROM workspace_group_memberships WHERE group_id=? AND revoked_at IS NULL",
            (gid,),
        ).fetchall()
        for m in members:
            if m["member_type"] == "account":
                acct = conn.execute(
                    "SELECT account_id, primary_email, person_id, status FROM workspace_accounts WHERE account_id=?",
                    (m["member_id"],),
                ).fetchone()
                if acct:
                    resolved_accounts.append(
                        {**dict(acct), "_role": m["role"], "_depth": depth}
                    )
            elif m["member_type"] == "group":
                expand(m["member_id"], depth + 1)

    expand(group_id, 0)

    result = {
        "group": dict(group),
        "resolved_accounts": resolved_accounts[:MAX_ROWS],
        "groups_visited": list(visited_groups),
        "_meta": _meta(
            len(resolved_accounts),
            min(len(resolved_accounts), MAX_ROWS),
            t0,
            len(resolved_accounts) > MAX_ROWS,
        ),
    }
    return _trim(result)


# ---------------------------------------------------------------------------
# Tool 9 — run_sql  (escape hatch, disabled unless DEBUG_SQL=true)
# ---------------------------------------------------------------------------

RUN_SQL_SCHEMA = {
    "name": "run_sql",
    "description": (
        "Execute an arbitrary read-only SQL SELECT against the database. "
        "ONLY available in debug mode (DEBUG_SQL=true). "
        "Use only when no other tool can answer the question."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "A SELECT statement to execute. Must not modify data.",
            },
            "limit": {
                "type": "integer",
                "description": "Row limit appended to the query if not already present (default 50).",
            },
        },
        "required": ["sql"],
    },
}


def run_sql(sql: str, limit: int = 50) -> dict:
    t0 = time.monotonic()
    debug = os.environ.get("DEBUG_SQL", "false").lower() == "true"
    if not debug:
        return {
            "error": "run_sql is disabled. Set DEBUG_SQL=true to enable it.",
            "_meta": _meta(0, 0, t0),
        }

    # Basic safety: allow only SELECT
    stripped = sql.strip().lstrip(";").upper()
    if not stripped.startswith("SELECT"):
        return {"error": "Only SELECT statements are allowed.", "_meta": _meta(0, 0, t0)}

    # Append a LIMIT if not already present
    if "LIMIT" not in stripped:
        sql = sql.rstrip("; ") + f" LIMIT {limit}"

    conn = _connect()
    try:
        rows = _rows_to_dicts(conn.execute(sql).fetchall())
        result = {
            "rows": rows,
            "_meta": _meta(len(rows), len(rows), t0),
        }
        return _trim(result)
    except Exception as exc:
        return {"error": str(exc), "_meta": _meta(0, 0, t0)}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool registry — used by agent.py and runner.py
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    LOOKUP_PERSON_SCHEMA,
    FIND_OFFBOARDING_GAPS_SCHEMA,
    GET_PERSON_ACCESS_SUMMARY_SCHEMA,
    GET_MFA_GAPS_SCHEMA,
    GET_AUDIT_EVENTS_SCHEMA,
    GET_APPLICATION_SUMMARY_SCHEMA,
    GET_DRIVE_PERMISSIONS_SCHEMA,
    GET_GROUP_MEMBERS_SCHEMA,
    RUN_SQL_SCHEMA,
]

TOOL_FUNCTIONS: dict[str, Any] = {
    "lookup_person": lookup_person,
    "find_offboarding_gaps": find_offboarding_gaps,
    "get_person_access_summary": get_person_access_summary,
    "get_mfa_gaps": get_mfa_gaps,
    "get_audit_events": get_audit_events,
    "get_application_summary": get_application_summary,
    "get_drive_permissions": get_drive_permissions,
    "get_group_members": get_group_members,
    "run_sql": run_sql,
}


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[x] Write prompts.py — system prompt and schema digest
[x] Write tools.py — all 9 tool implementations
[-] Write runner.py — OpenRouter API client wrapper
[ ] Write agent.py — CLI entry point and ReAct loop
[ ] Write tests/test_tools.py — tool unit tests
[ ] Write README.md — setup, usage, architecture, limitations
[ ] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — """
runner.py — Thin wrapper around the OpenAI-compatible OpenRouter API.

Responsibilities:
- Load the API key from the environment / .env file.
- Provide a single `chat_completion()` call that the ReAct loop uses.
- Convert the OpenRouter response into a normalised format the loop can handle.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.environ.get("MODEL", "google/gemini-2.0-flash-001")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set. "
            "Copy .env.example to .env and fill in your key."
        )
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
    )


def chat_completion(
    messages: list[dict],
    tools: list[dict],
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Send a chat completion request to OpenRouter.

    Returns a normalised dict:
    {
        "role": "assistant",
        "content": str | None,           # text content, if any
        "tool_calls": [                   # list of tool calls, if any
            {
                "id": str,
                "name": str,
                "arguments": dict,
            }
        ]
    }
    """
    client = _get_client()

    # Convert our tool schemas to OpenAI function-call format
    openai_tools = [
        {"type": "function", "function": schema} for schema in tools
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=openai_tools if openai_tools else None,
        tool_choice="auto" if openai_tools else None,
    )

    choice = response.choices[0]
    msg = choice.message

    tool_calls: list[dict] = []
    if msg.tool_calls:
        for tc in msg.tool_calls:
            try:
                arguments = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                arguments = {}
            tool_calls.append(
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": arguments,
                }
            )

    return {
        "role": "assistant",
        "content": msg.content,
        "tool_calls": tool_calls,
    }


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[x] Write prompts.py — system prompt and schema digest
[x] Write tools.py — all 9 tool implementations
[x] Write runner.py — OpenRouter API client wrapper
[-] Write agent.py — CLI entry point and ReAct loop
[ ] Write tests/test_tools.py — tool unit tests
[ ] Write README.md — setup, usage, architecture, limitations
[ ] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: write_file, write_file



> 🔧 **write_file** — """
agent.py — Entry point for the Access Investigation Agent.

Usage:
    python agent.py "Which former employees still have active accounts?"
    python agent.py --steps 15 "Which critical-app users lack MFA?"
    python agent.py --debug "Show all drive permissions for account ws_acc_0042"

The agent runs a ReAct loop:
  1. Send the user question + conversation history to the model.
  2. If the model returns tool calls, execute them and append results.
  3. If the model returns plain text (final answer), print and exit.
  4. Repeat until the step budget is exhausted.

All output goes to stdout. Intermediate reasoning is printed with a prefix
so it can be visually distinguished from the final answer.
"""

import argparse
import json
import os
import sys
import textwrap

from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT
from runner import chat_completion
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

load_dotenv()

DEFAULT_MAX_STEPS = int(os.environ.get("MAX_STEPS", "12"))


def _print_section(title: str, content: str, indent: int = 0) -> None:
    prefix = "  " * indent
    print(f"\n{prefix}{'─' * 60}")
    print(f"{prefix}  {title}")
    print(f"{prefix}{'─' * 60}")
    for line in content.splitlines():
        print(f"{prefix}  {line}")


def _execute_tool(name: str, arguments: dict, debug: bool = False) -> str:
    """Call a tool function and return its JSON-serialised result."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        result = {"error": f"Unknown tool: {name!r}"}
    else:
        try:
            result = fn(**arguments)
        except TypeError as exc:
            result = {"error": f"Invalid arguments for {name!r}: {exc}"}
        except Exception as exc:  # noqa: BLE001
            result = {"error": f"Tool {name!r} raised an exception: {exc}"}

    serialised = json.dumps(result, indent=2, default=str)
    if debug:
        _print_section(
            f"TOOL RESULT  ← {name}({json.dumps(arguments)})",
            textwrap.shorten(serialised, width=2000, placeholder="\n... (truncated)"),
            indent=1,
        )
    return serialised


def run_investigation(question: str, max_steps: int = DEFAULT_MAX_STEPS, debug: bool = False) -> str:
    """
    Run the ReAct loop for a single investigation question.
    Returns the final answer text.
    """
    # Determine which tools to expose (hide run_sql unless DEBUG_SQL is on)
    debug_sql = os.environ.get("DEBUG_SQL", "false").lower() == "true"
    active_schemas = [
        s for s in TOOL_SCHEMAS
        if s["name"] != "run_sql" or debug_sql
    ]

    # Build the initial message list
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    steps_used = 0
    final_answer: str | None = None

    print(f"\n🔍  Investigation: {question}\n")

    while steps_used < max_steps:
        if debug:
            print(f"\n[step {steps_used + 1}/{max_steps}] Calling model …")

        response = chat_completion(messages, active_schemas)

        # Append the assistant turn to history
        # Build the assistant message in OpenAI format for the history
        assistant_msg: dict = {"role": "assistant"}
        if response["content"]:
            assistant_msg["content"] = response["content"]
        if response["tool_calls"]:
            # OpenAI format requires tool_calls as a list of dicts
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"]),
                    },
                }
                for tc in response["tool_calls"]
            ]
        messages.append(assistant_msg)

        if response["tool_calls"]:
            steps_used += len(response["tool_calls"])
            for tc in response["tool_calls"]:
                tool_name = tc["name"]
                tool_args = tc["arguments"]

                print(f"  ↳ {tool_name}({json.dumps(tool_args, separators=(',', ':'))})")

                tool_result = _execute_tool(tool_name, tool_args, debug=debug)

                # Append tool result to history in OpenAI format
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result,
                    }
                )

            # If we're about to exceed the budget, inject a warning
            if steps_used >= max_steps and not response.get("content"):
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Step budget reached ({max_steps} tool calls used). "
                            "Please summarise your findings now in the required JSON format."
                        ),
                    }
                )

        else:
            # No tool calls — the model gave a text response
            final_answer = response["content"] or ""
            break

    # If the loop ended without a final answer (budget exhausted), ask for one
    if final_answer is None:
        print(f"\n  ⚠  Step budget exhausted ({steps_used} calls). Requesting summary …")
        messages.append(
            {
                "role": "user",
                "content": (
                    "You have used all your tool-call steps. "
                    "Summarise the evidence you have gathered in the required JSON format. "
                    "Note any gaps in your uncertainty field."
                ),
            }
        )
        response = chat_completion(messages, [])  # No tools — force text answer
        final_answer = response.get("content") or "(No response from model.)"

    return final_answer


def _print_final_answer(answer: str) -> None:
    """Pretty-print the final answer, extracting the JSON block if present."""
    print("\n" + "═" * 64)
    print("  INVESTIGATION RESULT")
    print("═" * 64)

    # Try to extract JSON block from the answer
    json_start = answer.find("```json")
    json_end = answer.find("```", json_start + 6) if json_start != -1 else -1

    prose_before = answer[:json_start].strip() if json_start != -1 else answer.strip()
    json_block = answer[json_start + 7 : json_end].strip() if json_start != -1 else ""
    prose_after = answer[json_end + 3 :].strip() if json_end != -1 else ""

    if prose_before:
        print(f"\n{prose_before}\n")

    if json_block:
        try:
            parsed = json.loads(json_block)
            print("\n📋  Structured Finding\n")
            print(f"  Conclusion : {parsed.get('conclusion', 'N/A')}")
            print(f"  Steps used : {parsed.get('steps_used', 'N/A')}")
            print(f"  Uncertainty: {parsed.get('uncertainty', 'N/A')}")
            findings = parsed.get("findings", [])
            if findings:
                print(f"\n  Findings ({len(findings)}):")
                for i, f in enumerate(findings, 1):
                    severity = f.get("severity", "?").upper()
                    desc = f.get("description", "")
                    ids = f.get("evidence_ids", [])
                    print(f"\n  [{i}] [{severity}] {desc}")
                    if ids:
                        id_str = ", ".join(str(x) for x in ids[:10])
                        if len(ids) > 10:
                            id_str += f" … (+{len(ids) - 10} more)"
                        print(f"       Evidence IDs: {id_str}")
        except json.JSONDecodeError:
            print(json_block)
    elif not prose_before:
        # No structured block — print raw
        print(answer)

    if prose_after:
        print(f"\n{prose_after}")

    print("\n" + "═" * 64 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Access Investigation Agent — investigate employee access using LLM + tools."
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Investigation question (quoted string). If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_MAX_STEPS,
        metavar="N",
        help=f"Maximum number of tool calls (default {DEFAULT_MAX_STEPS}).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print full tool inputs and outputs during the investigation.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the model (e.g. anthropic/claude-3-5-sonnet).",
    )
    args = parser.parse_args()

    if args.model:
        os.environ["MODEL"] = args.model

    if args.question:
        question = args.question
    else:
        if sys.stdin.isatty():
            print("Enter your investigation question (Ctrl-D to submit):")
        question = sys.stdin.read().strip()

    if not question:
        parser.print_help()
        sys.exit(1)

    answer = run_investigation(question, max_steps=args.steps, debug=args.debug)
    _print_final_answer(answer)


if __name__ == "__main__":
    main()


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[x] Write prompts.py — system prompt and schema digest
[x] Write tools.py — all 9 tool implementations
[x] Write runner.py — OpenRouter API client wrapper
[x] Write agent.py — CLI entry point and ReAct loop
[-] Write tests/test_tools.py — tool unit tests
[ ] Write README.md — setup, usage, architecture, limitations
[ ] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
SELECT p.person_id, p.full_name, p.employment_status
FROM people p
JOIN idp_accounts ia ON ia.person_id = p.person_id
WHERE p.employment_status = 'ended' AND ia.status = 'active'
LIMIT 3;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
SELECT ia.account_id, ia.username FROM idp_accounts ia
JOIN people p ON p.person_id = ia.person_id
WHERE p.employment_status = 'ended' AND ia.status = 'active' LIMIT 1;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
SELECT application_id, name, sensitivity FROM applications WHERE sensitivity='critical' LIMIT 3;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
SELECT group_id, name FROM idp_groups LIMIT 3;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
SELECT group_id, name FROM workspace_groups LIMIT 3;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
SELECT resource_id, name, classification FROM drive_resources LIMIT 3;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
-- A workspace account with drive permissions
SELECT dp.permission_id, dp.principal_id, dr.name FROM drive_permissions dp
JOIN drive_resources dr ON dr.resource_id = dp.resource_id
WHERE dp.revoked_at IS NULL AND dp.principal_type='account' LIMIT 3;
"

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
-- Get an audit event actor_id we can test with
SELECT actor_id FROM audit_events WHERE actor_id IS NOT NULL LIMIT 3;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
-- workspace account for drive perm test
SELECT account_id FROM workspace_accounts LIMIT 3;
" && echo "===" && sqlite3 input_data/access_snapshot.sqlite "
-- Person with ended status for access summary
SELECT person_id FROM people WHERE employment_status='ended' LIMIT 1;
"

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — """
tests/test_tools.py — Unit tests for all tool functions.

These tests run against the real (read-only) SQLite database.
They verify:
  - Return shape (_meta field present, expected keys exist)
  - Correct data values for known fixtures
  - Edge cases: missing person, empty results, truncation
  - read-only safety: tools do not modify the database

Run with:
    python -m pytest tests/ -v
"""

import json
import os
import sys

import pytest

# Ensure project root is on the path when tests are run from a subdirectory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Point at the real database
os.environ.setdefault("DB_PATH", "input_data/access_snapshot.sqlite")
os.environ.setdefault("DEBUG_SQL", "false")

from tools import (  # noqa: E402  (import after sys.path patch)
    find_offboarding_gaps,
    get_application_summary,
    get_audit_events,
    get_drive_permissions,
    get_group_members,
    get_mfa_gaps,
    get_person_access_summary,
    lookup_person,
    run_sql,
)

# ---------------------------------------------------------------------------
# Fixtures: known IDs from the database (verified by direct SQL query)
# ---------------------------------------------------------------------------

# A person whose employment ended but who has an active IdP account
ENDED_PERSON_ID = "per_001941"
ENDED_PERSON_NAME = "Rowan Mercer"
ENDED_PERSON_IDP_ACCOUNT = "idpa_001941"

# A person who is actively employed (no offboarding gap expected)
ACTIVE_PERSON_ID = "per_000279"

# A critical application
CRITICAL_APP_ID = "app_0001"
CRITICAL_APP_NAME = "Google Workspace"

# An IdP group
IDP_GROUP_ID = "idpg_000001"

# A Workspace group
WS_GROUP_ID = "gwg_000001"

# A Workspace account that has drive permissions
WS_ACCOUNT_WITH_PERMS = "gwa_000003"

# An audit event actor
AUDIT_ACTOR_ID = "gha_000002"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def has_meta(result: dict) -> bool:
    return "_meta" in result and "total_count" in result["_meta"]


# ---------------------------------------------------------------------------
# lookup_person
# ---------------------------------------------------------------------------

class TestLookupPerson:
    def test_lookup_by_person_id(self):
        result = lookup_person(ENDED_PERSON_ID)
        assert has_meta(result)
        assert len(result["people"]) == 1
        person = result["people"][0]
        assert person["person_id"] == ENDED_PERSON_ID
        assert ENDED_PERSON_NAME in person["full_name"]
        assert person["employment_status"] == "ended"

    def test_lookup_by_name_fragment(self):
        result = lookup_person("Rowan")
        assert has_meta(result)
        assert any(p["person_id"] == ENDED_PERSON_ID for p in result["people"])

    def test_lookup_returns_accounts(self):
        result = lookup_person(ENDED_PERSON_ID)
        person = result["people"][0]
        assert "accounts" in person
        assert "idp" in person["accounts"]
        assert "workspace" in person["accounts"]
        assert "github" in person["accounts"]
        assert "devices" in person["accounts"]

    def test_lookup_idp_account_present(self):
        result = lookup_person(ENDED_PERSON_ID)
        idp_accounts = result["people"][0]["accounts"]["idp"]
        assert any(a["account_id"] == ENDED_PERSON_IDP_ACCOUNT for a in idp_accounts)

    def test_lookup_no_match(self):
        result = lookup_person("zzz_nonexistent_xyz_12345")
        assert has_meta(result)
        assert result["people"] == []

    def test_lookup_by_email_fragment(self):
        result = lookup_person("rowan.mercer")
        assert has_meta(result)
        assert len(result["people"]) >= 1


# ---------------------------------------------------------------------------
# find_offboarding_gaps
# ---------------------------------------------------------------------------

class TestFindOffboardingGaps:
    def test_default_finds_ended_with_active_idp(self):
        result = find_offboarding_gaps()
        assert has_meta(result)
        gaps = result["gaps"]
        assert len(gaps) > 0
        # Every gap should be an ended person
        for gap in gaps:
            assert gap["employment_status"] in ("ended", "leave")
            assert "active_accounts" in gap

    def test_specific_person_appears_in_gaps(self):
        result = find_offboarding_gaps(statuses=["ended"], systems=["idp"])
        person_ids = [g["person_id"] for g in result["gaps"]]
        assert ENDED_PERSON_ID in person_ids

    def test_filter_by_system_idp_only(self):
        result = find_offboarding_gaps(systems=["idp"])
        for gap in result["gaps"]:
            # Only idp should appear in active_accounts
            assert "idp" in gap["active_accounts"]
            assert "workspace" not in gap["active_accounts"]
            assert "github" not in gap["active_accounts"]

    def test_leave_status_filter(self):
        result = find_offboarding_gaps(statuses=["leave"])
        for gap in result["gaps"]:
            assert gap["employment_status"] == "leave"

    def test_meta_total_count_accurate(self):
        result = find_offboarding_gaps()
        assert result["_meta"]["total_count"] >= result["_meta"]["returned"]

    def test_all_systems(self):
        result = find_offboarding_gaps(systems=["idp", "workspace", "github"])
        assert has_meta(result)
        # We know at least the 3 ended-with-active-idp people exist
        assert result["_meta"]["total_count"] >= 3


# ---------------------------------------------------------------------------
# get_person_access_summary
# ---------------------------------------------------------------------------

class TestGetPersonAccessSummary:
    def test_ended_person_summary(self):
        result = get_person_access_summary(ENDED_PERSON_ID)
        assert has_meta(result)
        assert "person" in result
        assert result["person"]["employment_status"] == "ended"
        assert "idp_accounts" in result
        assert "application_access" in result
        assert "workspace_accounts" in result
        assert "github_accounts" in result

    def test_idp_account_in_summary(self):
        result = get_person_access_summary(ENDED_PERSON_ID)
        idp_ids = [a["account_id"] for a in result["idp_accounts"]]
        assert ENDED_PERSON_IDP_ACCOUNT in idp_ids

    def test_nonexistent_person(self):
        result = get_person_access_summary("per_NONEXISTENT")
        assert "error" in result

    def test_idp_group_memberships_included(self):
        # Any active person should have the memberships key on each idp account
        result = get_person_access_summary(ENDED_PERSON_ID)
        for acct in result["idp_accounts"]:
            assert "idp_group_memberships" in acct

    def test_drive_permissions_included(self):
        result = get_person_access_summary(ENDED_PERSON_ID)
        assert "drive_permissions" in result
        assert isinstance(result["drive_permissions"], list)


# ---------------------------------------------------------------------------
# get_mfa_gaps
# ---------------------------------------------------------------------------

class TestGetMfaGaps:
    def test_returns_gaps(self):
        result = get_mfa_gaps()
        assert has_meta(result)
        assert "gaps" in result
        assert "summary_by_app" in result
        assert result["_meta"]["total_count"] > 0

    def test_all_gaps_on_sensitive_or_critical_apps(self):
        result = get_mfa_gaps(sensitivity="sensitive")
        for gap in result["gaps"]:
            assert gap["sensitivity"] in ("sensitive", "critical")

    def test_critical_only_filter(self):
        result = get_mfa_gaps(sensitivity="critical")
        for gap in result["gaps"]:
            assert gap["sensitivity"] == "critical"

    def test_mfa_required_only_filter(self):
        result = get_mfa_gaps(mfa_required_only=True)
        for gap in result["gaps"]:
            assert gap["default_mfa_requirement"] == "required"

    def test_specific_app_filter(self):
        result = get_mfa_gaps(application_id=CRITICAL_APP_ID)
        for gap in result["gaps"]:
            assert gap["application_id"] == CRITICAL_APP_ID

    def test_gaps_not_enrolled(self):
        result = get_mfa_gaps()
        for gap in result["gaps"]:
            assert gap["mfa_enrollment_status"] != "enrolled"

    def test_summary_by_app_has_gap_counts(self):
        result = get_mfa_gaps()
        for entry in result["summary_by_app"]:
            assert "gap_count" in entry
            assert entry["gap_count"] > 0


# ---------------------------------------------------------------------------
# get_audit_events
# ---------------------------------------------------------------------------

class TestGetAuditEvents:
    def test_requires_actor_or_target(self):
        result = get_audit_events()
        assert "error" in result

    def test_by_actor_id(self):
        result = get_audit_events(actor_id=AUDIT_ACTOR_ID)
        assert has_meta(result)
        assert "events" in result
        assert result["_meta"]["total_count"] > 0

    def test_by_actor_id_events_belong_to_actor(self):
        result = get_audit_events(actor_id=AUDIT_ACTOR_ID, limit=10)
        for event in result["events"]:
            assert event["actor_id"] == AUDIT_ACTOR_ID

    def test_system_filter(self):
        result = get_audit_events(actor_id=AUDIT_ACTOR_ID, system="github")
        for event in result["events"]:
            assert event["system"] == "github"

    def test_limit_respected(self):
        result = get_audit_events(actor_id=AUDIT_ACTOR_ID, limit=5)
        assert len(result["events"]) <= 5

    def test_since_filter(self):
        result = get_audit_events(actor_id=AUDIT_ACTOR_ID, since="2026-07-01T00:00:00Z")
        for event in result["events"]:
            assert event["occurred_at"] >= "2026-07-01T00:00:00Z"

    def test_details_parsed_as_dict(self):
        result = get_audit_events(actor_id=AUDIT_ACTOR_ID, limit=5)
        for event in result["events"]:
            # details should be a dict (parsed from details_json)
            assert "details" in event
            assert isinstance(event["details"], dict)

    def test_events_sorted_descending(self):
        result = get_audit_events(actor_id=AUDIT_ACTOR_ID, limit=10)
        times = [e["occurred_at"] for e in result["events"]]
        assert times == sorted(times, reverse=True)


# ---------------------------------------------------------------------------
# get_application_summary
# ---------------------------------------------------------------------------

class TestGetApplicationSummary:
    def test_by_app_id(self):
        result = get_application_summary(application_id=CRITICAL_APP_ID)
        assert has_meta(result)
        assert "application" in result
        assert result["application"]["application_id"] == CRITICAL_APP_ID
        assert result["application"]["name"] == CRITICAL_APP_NAME

    def test_by_app_name(self):
        result = get_application_summary(app_name="Google Workspace")
        assert has_meta(result)
        assert result["application"]["application_id"] == CRITICAL_APP_ID

    def test_mfa_enrollment_stats_present(self):
        result = get_application_summary(application_id=CRITICAL_APP_ID)
        assert "mfa_enrollment_stats" in result
        stats = {row["mfa_enrollment_status"]: row["count"] for row in result["mfa_enrollment_stats"]}
        # At minimum, some enrollment statuses should be present
        assert len(stats) > 0

    def test_active_users_sample_present(self):
        result = get_application_summary(application_id=CRITICAL_APP_ID)
        assert "active_users_sample" in result
        assert isinstance(result["active_users_sample"], list)

    def test_no_args_returns_error(self):
        result = get_application_summary()
        assert "error" in result

    def test_nonexistent_app(self):
        result = get_application_summary(application_id="app_NONEXISTENT")
        assert "error" in result


# ---------------------------------------------------------------------------
# get_drive_permissions
# ---------------------------------------------------------------------------

class TestGetDrivePermissions:
    def test_requires_resource_or_account(self):
        result = get_drive_permissions()
        assert "error" in result

    def test_by_account_id(self):
        result = get_drive_permissions(account_id=WS_ACCOUNT_WITH_PERMS)
        assert has_meta(result)
        assert "permissions" in result

    def test_highlight_external(self):
        result = get_drive_permissions(account_id=WS_ACCOUNT_WITH_PERMS, highlight_external=True)
        for perm in result["permissions"]:
            assert perm["principal_type"] in ("external_email", "domain")

    def test_no_revoked_permissions_returned(self):
        # All returned permissions should have revoked_at = None (not in result dict because not selected)
        # We verify by checking that the query returns sensible data
        result = get_drive_permissions(account_id=WS_ACCOUNT_WITH_PERMS)
        # The query filters revoked_at IS NULL — just check we got a list
        assert isinstance(result["permissions"], list)

    def test_meta_present(self):
        result = get_drive_permissions(account_id=WS_ACCOUNT_WITH_PERMS)
        assert "_meta" in result


# ---------------------------------------------------------------------------
# get_group_members
# ---------------------------------------------------------------------------

class TestGetGroupMembers:
    def test_idp_group(self):
        result = get_group_members(group_id=IDP_GROUP_ID, group_type="idp")
        assert has_meta(result)
        assert "group" in result
        assert "resolved_accounts" in result
        assert "groups_visited" in result

    def test_idp_group_members_are_dicts(self):
        result = get_group_members(group_id=IDP_GROUP_ID, group_type="idp")
        for member in result["resolved_accounts"]:
            assert "account_id" in member
            assert "username" in member

    def test_workspace_group(self):
        result = get_group_members(group_id=WS_GROUP_ID, group_type="workspace")
        assert has_meta(result)
        assert "group" in result
        assert "resolved_accounts" in result

    def test_nonexistent_idp_group(self):
        result = get_group_members(group_id="idpg_NONEXISTENT", group_type="idp")
        assert "error" in result

    def test_groups_visited_includes_root(self):
        result = get_group_members(group_id=IDP_GROUP_ID, group_type="idp")
        assert IDP_GROUP_ID in result["groups_visited"]


# ---------------------------------------------------------------------------
# run_sql  (escape hatch)
# ---------------------------------------------------------------------------

class TestRunSql:
    def test_disabled_by_default(self):
        os.environ["DEBUG_SQL"] = "false"
        result = run_sql("SELECT 1")
        assert "error" in result
        assert "disabled" in result["error"].lower()

    def test_enabled_returns_rows(self):
        os.environ["DEBUG_SQL"] = "true"
        result = run_sql("SELECT person_id, full_name FROM people LIMIT 3")
        assert has_meta(result)
        assert "rows" in result
        assert len(result["rows"]) == 3
        os.environ["DEBUG_SQL"] = "false"

    def test_non_select_rejected(self):
        os.environ["DEBUG_SQL"] = "true"
        result = run_sql("DROP TABLE people")
        assert "error" in result
        os.environ["DEBUG_SQL"] = "false"

    def test_limit_appended_when_missing(self):
        os.environ["DEBUG_SQL"] = "true"
        # This query has no LIMIT; the tool should add one
        result = run_sql("SELECT person_id FROM people", limit=5)
        assert has_meta(result)
        assert len(result["rows"]) <= 5
        os.environ["DEBUG_SQL"] = "false"


# ---------------------------------------------------------------------------
# Truncation behaviour
# ---------------------------------------------------------------------------

class TestTruncation:
    def test_meta_truncated_flag_present(self):
        """Even when not truncated, the flag should be present."""
        result = find_offboarding_gaps()
        assert "truncated" in result["_meta"]

    def test_result_fits_char_budget(self):
        """Serialised result must be within the CHAR_BUDGET (6000 chars) or
        the _meta.truncated flag must be True."""
        import tools as t_module

        result = get_mfa_gaps()
        serialised = json.dumps(result)
        if len(serialised) > t_module.CHAR_BUDGET:
            assert result["_meta"]["truncated"] is True


### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[x] Write prompts.py — system prompt and schema digest
[x] Write tools.py — all 9 tool implementations
[x] Write runner.py — OpenRouter API client wrapper
[x] Write agent.py — CLI entry point and ReAct loop
[x] Write tests/test_tools.py — tool unit tests
[-] Write README.md — setup, usage, architecture, limitations
[ ] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — # Access Investigation Agent

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

Default: `google/gemini-2.0-flash-001` via OpenRouter.

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


### 🤖 Assistant

> 🔧 called: update_todo_list

Now let's verify everything runs correctly:

> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[x] Write prompts.py — system prompt and schema digest
[x] Write tools.py — all 9 tool implementations
[x] Write runner.py — OpenRouter API client wrapper
[x] Write agent.py — CLI entry point and ReAct loop
[x] Write tests/test_tools.py — tool unit tests
[x] Write README.md — setup, usage, architecture, limitations
[-] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — cd /Users/hongfei/Documents/code/Access-Investigation-Agent && pip install -r requirements.txt -q 2>&1 | tail -5

---

### 👤 User

let's create a virtural environment and install dependencies inside.

---

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python3 -m venv .venv --without-pip && curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3 && .venv/bin/pip install -r requirements.txt

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python3 --version && which python3

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — python3 -m venv .venv --without-pip && curl -sS "https://bootstrap.pypa.io/pip/pip.pyz" -o /tmp/pip.pyz && .venv/bin/python3 /tmp/pip.pyz install pip --upgrade && .venv/bin/pip install -r requirements.txt

### 🤖 Assistant

> 🔧 called: execute_command

The issue is that pip's `truststore` library is trying to parse the macOS version string and failing because `sw_vers` is returning an empty string. This is a known issue with Python 3.14 and certain pip bootstrappers. Let me work around it:

> 🔧 **execute_command** — sw_vers -productVersion && uname -r

---

### 👤 User

never mind, I have setup .venv with uv. Go ahead as planned.

---

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .venv/bin/python -m pytest tests/ -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .venv/bin/pip install pytest -q && .venv/bin/python -m pytest tests/ -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — ls .venv/bin/ | head -20

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .venv/bin/python -m uv pip install pytest 2>&1 || .venv/bin/python -m ensurepip && .venv/bin/python -m pip install pytest -q

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .venv/bin/python -m pip install pytest -q 2>&1 && .venv/bin/python -m pytest tests/ -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

Tests are running. The suite timed out mid-run only because of the combined `pip install` in the same command. Let me run the tests alone:

> 🔧 **execute_command** — .venv/bin/python -m pytest tests/ -v 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

The test runner is hanging at `test_returns_gaps`. Let me check what's happening with that test:

> 🔧 **execute_command** — .venv/bin/python -c "
import os
os.environ['DB_PATH'] = 'input_data/access_snapshot.sqlite'
from tools import get_mfa_gaps
import json, time
t = time.monotonic()
r = get_mfa_gaps()
print('elapsed:', round(time.monotonic()-t, 2), 's')
print('total:', r['_meta']['total_count'])
print('returned:', r['_meta']['returned'])
print('truncated:', r['_meta']['truncated'])
" 2>&1

### 🤖 Assistant

> 🔧 called: read_file

The `_trim` function is hanging. It must be caught in an infinite loop when trimming the large `gaps` list. Let me inspect the logic:

> 🔧 **read_file** — tools.py

### 🤖 Assistant

> 🔧 called: apply_diff

The bug: when there's only 1 row left but the serialised result is still over budget (because the `_meta.truncated = True` line is *outside* the loop and `summary_by_app` is also a large list that `_trim` never touches), `max(1, 1//2) = 1` and the loop never terminates. There are two issues:

1. The `while` loop bottoms out at 1 row and can't go below, creating an infinite loop.
2. `_trim` only trims the *first* list key — for `get_mfa_gaps` that's `summary_by_app`, not `gaps`.

Fix both:

> 🔧 **apply_diff** — tools.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now also update the truncation test since `summary_by_app` is the first list key in `get_mfa_gaps` — the `returned` count in `_meta` will reflect that list, not `gaps`. Let me fix the test to be precise:

> 🔧 **apply_diff** — tests/test_tools.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — tests/test_tools.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — tests/test_tools.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — tests/test_tools.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — tests/test_tools.py

### 🤖 Assistant

> 🔧 called: execute_command

Now run just the fast tests first (skipping the ones we already saw pass) to confirm the fix:

> 🔧 **execute_command** — .venv/bin/python -m pytest tests/ -v --timeout=30 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — .venv/bin/python -m pip install pytest-timeout -q 2>&1 && .venv/bin/python -m pytest tests/ -v --timeout=20 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

51/54 passing. Three failures to fix:

1. **`test_lookup_by_name_fragment`** — "Rowan" matches multiple people and `per_001941` is getting trimmed out by `_trim`. The result is too large and the `people` list gets halved. Fix: increase the char budget, or for this tool don't use `_trim` since each person entry is small but the total is borderline.

2. **`test_mfa_enrollment_stats_present`** — `mfa_enrollment_stats` is a list key so `_trim` is zeroing it out. It's a tiny list (3 rows max) — we should exclude it from trimming.

3. **`test_groups_visited_includes_root`** — `groups_visited` is a `set` being returned as a `list` via `list(visited_groups)`, but the group gets visited only if it has members. Let me check:

> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "
SELECT COUNT(*) FROM idp_group_memberships WHERE group_id='idpg_000001' AND revoked_at IS NULL;
"

### 🤖 Assistant

> 🔧 called: execute_command

The group has members. The issue is that `_trim` halves `groups_visited` (it's a list) down to zero. Let me fix all three issues:

1. Exclude small metadata lists (`mfa_enrollment_stats`, `groups_visited`, `summary_by_app`) from trimming — only trim the primary data list (`people`, `gaps`, `events`, `active_users_sample`, `resolved_accounts`, `permissions`).
2. Fix the `groups_visited` list — it was being trimmed away entirely.
3. Fix the name-fragment test — same root cause; `people` list is big and the trim path is hitting it incorrectly. Actually the `people` list for "Rowan" should be small (≤3 rows). Let me check:

> 🔧 **execute_command** — sqlite3 input_data/access_snapshot.sqlite "SELECT COUNT(*) FROM people WHERE full_name LIKE '%Rowan%';"

### 🤖 Assistant

> 🔧 called: apply_diff

33 people named Rowan — with all their nested account sub-lists, the JSON blows past 6000 chars. The test expectation is wrong (it assumes `per_001941` survives trimming). The right fix is to make `_trim` smarter: trim nested sub-lists inside each person entry first, or just raise `CHAR_BUDGET` slightly, or fix the test to not assume order survives heavy trimming.

The cleanest fix across all three issues is to make `_trim` only trim the *primary* list (the largest one), and protect small auxiliary lists. The real solution is a dedicated trim key per tool:

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:38
-------
def _trim(result: dict) -> dict:
    """Serialise result to JSON; if over budget, trim all list values until it fits."""
    if len(json.dumps(result, default=str)) <= CHAR_BUDGET:
        return result

    # Collect all list keys (skip _meta itself)
    list_keys = [k for k, v in result.items() if isinstance(v, list) and k != "_meta"]
    if not list_keys:
        return result

    # Halve every list on each pass until we fit or every list is empty
    while list_keys and len(json.dumps(result, default=str)) > CHAR_BUDGET:
        still_shrinkable = False
        for k in list_keys:
            current = result[k]
            if len(current) > 1:
                result = {**result, k: current[: len(current) // 2]}
                still_shrinkable = True
            elif len(current) == 1:
                # One row still too big — drop it entirely
                result = {**result, k: []}
        if not still_shrinkable:
            break  # nothing left to trim

    result["_meta"]["truncated"] = True
    # Update returned count using the primary data list (first non-empty, or first)
    primary_key = list_keys[0]
    result["_meta"]["returned"] = len(result[primary_key])
    return result
=======
# Keys that are small summary/metadata lists and must not be trimmed.
_PROTECTED_LIST_KEYS = frozenset(
    {"mfa_enrollment_stats", "summary_by_app", "groups_visited", "recent_auth_events"}
)


def _trim(result: dict, primary_key: str | None = None) -> dict:
    """
    Serialise result to JSON; if over budget, trim the primary data list.

    primary_key: the list key to trim (e.g. 'people', 'gaps', 'events').
    If not supplied, the first non-protected list key is used.
    Protected lists (small summary/metadata lists) are never trimmed.
    """
    if len(json.dumps(result, default=str)) <= CHAR_BUDGET:
        return result

    # Determine which key to trim
    if primary_key is None:
        primary_key = next(
            (k for k, v in result.items() if isinstance(v, list) and k not in _PROTECTED_LIST_KEYS),
            None,
        )
    if primary_key is None or primary_key not in result:
        return result  # nothing trimmable

    rows = result[primary_key]
    while len(json.dumps(result, default=str)) > CHAR_BUDGET:
        if len(rows) > 1:
            rows = rows[: len(rows) // 2]
        elif len(rows) == 1:
            rows = []
        else:
            break  # already empty, can't shrink further
        result = {**result, primary_key: rows}

    result["_meta"]["truncated"] = True
    result["_meta"]["returned"] = len(rows)
    return result
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: apply_diff

Now fix the name-fragment test — it should check that *some* person named Rowan is returned, not specifically `per_001941` (which may be trimmed when there are 33 Rowans):

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:91
-------
    def test_lookup_by_name_fragment(self):
        result = lookup_person("Rowan")
        assert has_meta(result)
        assert any(p["person_id"] == ENDED_PERSON_ID for p in result["people"])
=======
    def test_lookup_by_name_fragment(self):
        result = lookup_person("Rowan")
        assert has_meta(result)
        # 33 people named "Rowan" exist; at least some should be returned
        assert len(result["people"]) > 0
        assert all("Rowan" in p["full_name"] for p in result["people"])
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: grep

Now also update the `test_result_fits_char_budget` — the `_trim` on `get_mfa_gaps` now protects `summary_by_app`, so the result might still technically be over budget if `summary_by_app` alone is large. But `summary_by_app` for 6 apps is tiny. Let me also pass the explicit primary key in `get_mfa_gaps` to make the trim deterministic:

> 🔧 **grep** — return _trim\(result\)

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — tools.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — tools.py

### 🤖 Assistant

> 🔧 called: apply_diff

Pass explicit primary keys where the auto-detection order would be wrong:

> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:509
-------
        result = {
            "summary_by_app": list(by_app.values()),
            "gaps": returned_rows,
            "_meta": _meta(total, len(returned_rows), t0, total > MAX_ROWS),
        }
        return _trim(result)
=======
        result = {
            "summary_by_app": list(by_app.values()),
            "gaps": returned_rows,
            "_meta": _meta(total, len(returned_rows), t0, total > MAX_ROWS),
        }
        return _trim(result, primary_key="gaps")
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: execute_command

Now run the tests again:

> 🔧 **execute_command** — .venv/bin/python -m pytest tests/ -v --timeout=20 2>&1

### 🤖 Assistant

> 🔧 called: execute_command

**54/54 passing in 0.14s.** Let me also do a quick import check on all modules:

> 🔧 **execute_command** — .venv/bin/python -c "import tools; import prompts; import runner; import agent; print('All modules import OK')" 2>&1

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Write requirements.txt and .env.example
[x] Write prompts.py — system prompt and schema digest
[x] Write tools.py — all 9 tool implementations
[x] Write runner.py — OpenRouter API client wrapper
[x] Write agent.py — CLI entry point and ReAct loop
[x] Write tests/test_tools.py — tool unit tests
[x] Write README.md — setup, usage, architecture, limitations
[x] Verify the code runs end-to-end (import check + tool smoke test)


### 🤖 Assistant

All done. Here's a summary of everything that was built and the one bug fixed:

---

## What was built

| File | Purpose |
|---|---|
| [`agent.py`](agent.py) | CLI entry point; runs the ReAct loop with step budget and structured final-answer printing |
| [`tools.py`](tools.py) | 9 SQL-backed tools: `lookup_person`, `find_offboarding_gaps`, `get_person_access_summary`, `get_mfa_gaps`, `get_audit_events`, `get_application_summary`, `get_drive_permissions`, `get_group_members`, `run_sql` |
| [`prompts.py`](prompts.py) | System prompt + 600-token schema digest injected at turn 0 |
| [`runner.py`](runner.py) | Thin OpenRouter wrapper over the `openai` SDK |
| [`tests/test_tools.py`](tests/test_tools.py) | 54 unit tests across all 9 tools — **54/54 pass** |
| [`README.md`](README.md) | Setup, usage, architecture, known limitations |
| [`requirements.txt`](requirements.txt) | `openai`, `python-dotenv` |
| [`.env.example`](.env.example) | Key template; `.env` is git-ignored |

### Bug caught and fixed during tests

[`_trim()`](tools.py) had an infinite loop: when one list row remained but the JSON was still over budget, `max(1, 1//2) == 1` made it loop forever. The fix trims the *primary* data list only, protects small metadata lists (`mfa_enrollment_stats`, `summary_by_app`, `groups_visited`), and breaks cleanly when the list is empty.

### Usage

```bash
cp .env.example .env   # fill in OPENROUTER_API_KEY
python agent.py "Which former employees still have active accounts?"
python agent.py "Which users on critical apps are not enrolled in MFA?"
python agent.py --debug --steps 15 "Show drive permissions for ended employees"
```

---

### 👤 User

read `bob_prompts/3-Testing.md` for a couple of light tasks.

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — bob_prompts/3-Testing.md

### 🤖 Assistant

> 🔧 called: read_file

Two quick tasks. Let me do both in parallel:

> 🔧 **read_file** — PROJECT.md

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — """
demo.py — Run the two prepared investigation demos without typing the full commands.

Usage:
    python demo.py             # run all demos in sequence
    python demo.py 1           # run only demo 1
    python demo.py 2           # run only demo 2
    python demo.py 1 2         # run demos 1 and 2
"""

import sys

from agent import run_investigation, _print_final_answer

DEMOS = [
    {
        "id": 1,
        "title": "Offboarding Residual Access",
        "question": "Which former employees still have active accounts?",
        "kwargs": {},
    },
    {
        "id": 2,
        "title": "MFA Gap Analysis",
        "question": "Which users on critical apps are not enrolled in MFA?",
        "kwargs": {},
    },
]


def run_demo(demo: dict) -> None:
    print(f"\n{'═' * 64}")
    print(f"  DEMO {demo['id']} — {demo['title']}")
    print(f"{'═' * 64}")
    answer = run_investigation(demo["question"], **demo["kwargs"])
    _print_final_answer(answer)


def main() -> None:
    if len(sys.argv) > 1:
        requested = set(sys.argv[1:])
        selected = [d for d in DEMOS if str(d["id"]) in requested]
        if not selected:
            print(f"Unknown demo IDs: {sys.argv[1:]}. Available: {[d['id'] for d in DEMOS]}")
            sys.exit(1)
    else:
        selected = DEMOS

    for demo in selected:
        run_demo(demo)


if __name__ == "__main__":
    main()


### 🤖 Assistant

> 🔧 called: apply_diff

Now update `PROJECT.md` with implementation status and the debugging gotchas:

> 🔧 **apply_diff** — PROJECT.md

### 🤖 Assistant

Done. Here's what was added:

**[`demo.py`](demo.py)** — runs either or both prepared investigations without typing the full question:
```bash
python demo.py      # both demos
python demo.py 1    # offboarding gaps only  
python demo.py 2    # MFA gaps only
```

**[`PROJECT.md`](PROJECT.md)** — now has a full status header at the top with:
- A file-by-file implementation status table
- A copy-paste quick-start block for the next session
- Five documented debugging gotchas with problem/fix/symptom details:
  1. `_trim()` infinite loop at 1 row
  2. `summary_by_app` being zeroed by trimming
  3. `groups_visited` emptied by trimming (same root cause)
  4. Over-specific name-fragment test assumption
  5. Python 3.14 / pip bootstrap failure on macOS → use `uv`

---

### 👤 User

Let's check if the endpoint or model name are correct. We are getting 404 on `python demo.py 1`

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — runner.py

### 🤖 Assistant

> 🔧 called: execute_command

Let me verify the model ID and endpoint against OpenRouter's live API:

> 🔧 **execute_command** — source .venv/bin/activate && python -c "
from dotenv import load_dotenv; load_dotenv()
import os, urllib.request, json
key = os.environ.get('OPENROUTER_API_KEY','')
req = urllib.request.Request('https://openrouter.ai/api/v1/models', headers={'Authorization': f'Bearer {key}'})
data = json.loads(urllib.request.urlopen(req).read())
# find gemini-2.0-flash models
matches = [m['id'] for m in data['data'] if 'gemini-2.0-flash' in m['id']]
print('\n'.join(sorted(matches)[:20]))
" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — source .venv/bin/activate && python -c "
from dotenv import load_dotenv; load_dotenv()
import os, urllib.request, json
key = os.environ.get('OPENROUTER_API_KEY','')
print('Key present:', bool(key))
req = urllib.request.Request('https://openrouter.ai/api/v1/models', headers={'Authorization': f'Bearer {key}'})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
matches = [m['id'] for m in data.get('data', []) if 'gemini' in m['id'].lower()]
print('Gemini models:')
for m in sorted(matches):
    print(' ', m)
" 2>&1

### 🤖 Assistant

> 🔧 called: apply_diff

`google/gemini-2.0-flash-001` no longer exists on OpenRouter. The current equivalent is `google/gemini-2.5-flash` — fast, cheap, 1M context, strong function-calling. Updating the default:

> 🔧 **apply_diff** — runner.py

### 🤖 Assistant

> 🔧 called: search_and_replace, search_and_replace

Also update the two places that document the model name:

> 🔧 **search_and_replace** — README.md

> 🔧 **search_and_replace** — PROJECT.md

### 🤖 Assistant

The model `google/gemini-2.0-flash-001` is no longer listed on OpenRouter. Changed the default to `google/gemini-2.5-flash` in [`runner.py`](runner.py:18), [`PROJECT.md`](PROJECT.md), and [`README.md`](README.md). `python demo.py 1` should now connect successfully.

---

### 👤 User

read `bob_prompts/4-Discussion.md`

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — bob_prompts/4-Discussion.md

### 🤖 Assistant

> 🔧 called: read_file

Good question. Let me look at the current demo.py and agent.py to understand the exact context before giving a grounded recommendation:

> 🔧 **read_file** — demo.py

### 🤖 Assistant

Here's my honest design assessment:

---

## Design recommendation: Option 2 (structured fallback output)

**Option 1 — interactive follow-up loop** is the right long-term direction but has non-trivial implementation cost in the current framework:

- `run_investigation()` in [`agent.py`](agent.py) is a pure function: one question → one answer. To support back-and-forth, it would need to be restructured into a stateful session that persists message history between calls, plus a read loop on stdin.
- More importantly, the problem in demo 3 is not a user-input problem — it is a **tool gap**. The model correctly diagnosed that `get_drive_permissions` requires a specific account or resource ID, and there is no tool to enumerate all Drive permissions for a cohort of people. Adding a conversation loop would let the user confirm "yes, do the alternative" — but it would not fix the underlying investigation capability. It adds UI complexity without addressing the root cause.
- For the *exercise*, interactive mode also works against the submission format: the examples need to be self-contained, reproducible, and pipeable to a file.

**Option 2 — structured fallback output** fits better because:

- The root cause is a missing tool (`find_drive_permissions_for_cohort` or broadening `find_offboarding_gaps` to include drive findings). The model is actually doing the right thing: correctly identifying the gap and suggesting an alternative. We should harvest that signal, not paper over it.
- It requires only a small, focused change: instruct the model (via the system prompt) to emit a specific `cannot_proceed` block when it lacks the tools to answer a question, with a machine-readable suggestion.
- The output is still a structured final answer, consistent with the existing contract. The demo output becomes a feature demonstration of the agent's self-awareness about its own limitations — which is actually great to show in the review.
- Zero restructuring of the agent loop or the demo harness.

---

## Concrete plan for Option 2

Add one paragraph to the system prompt in [`prompts.py`](prompts.py) instructing the model that when it cannot proceed, it must still emit the JSON final-answer block but with a `cannot_proceed` key:

```json
{
  "conclusion": "I cannot answer this question with the available tools.",
  "findings": [],
  "cannot_proceed": {
    "reason": "No tool can enumerate drive permissions across a cohort of people.",
    "missing_capability": "A tool like find_drive_permissions_for_cohort(person_ids) that joins ended employees → workspace_accounts → drive_permissions would enable this.",
    "alternative_command": "python agent.py \"Which former employees still have active accounts?\""
  },
  "uncertainty": "...",
  "steps_used": 1
}
```

Then [`_print_final_answer()`](agent.py) in `agent.py` detects the `cannot_proceed` key and renders it clearly. The output becomes:

```
📋  Structured Finding

  Conclusion : I cannot answer this question with the available tools.

  ⚠  Cannot Proceed
     Reason     : No tool can enumerate drive permissions across a cohort.
     Missing    : A tool like find_drive_permissions_for_cohort(...)...
     Alternative: python agent.py "Which former employees still have active accounts?"
```

This is low effort (two small edits: `prompts.py` + `_print_final_answer`), keeps the architecture clean, and turns a dead-end into a useful and honest output that's good to show in the review.

---

Want me to implement Option 2 now?

---

### 👤 User

yes go ahead

---

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — prompts.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — prompts.py

### 🤖 Assistant

> 🔧 called: apply_diff

Now I have the full picture. Two edits: add the `cannot_proceed` instruction to [`prompts.py`](prompts.py) and add the rendering block to [`agent.py`](agent.py).

> 🔧 **apply_diff** — prompts.py

### 🤖 Assistant

> 🔧 called: read_file

Now add the `cannot_proceed` rendering block to `_print_final_answer` in [`agent.py`](agent.py):

> 🔧 **read_file** — agent.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — agent.py

### 🤖 Assistant

> 🔧 called: apply_diff



> 🔧 **apply_diff** — <<<<<<< SEARCH
:start_line:189
-------
    if json_block:
        try:
            parsed = json.loads(json_block)
            print("\n📋  Structured Finding\n")
            print(f"  Conclusion : {parsed.get('conclusion', 'N/A')}")
            print(f"  Steps used : {parsed.get('steps_used', 'N/A')}")
            print(f"  Uncertainty: {parsed.get('uncertainty', 'N/A')}")
            findings = parsed.get("findings", [])
            if findings:
                print(f"\n  Findings ({len(findings)}):")
                for i, f in enumerate(findings, 1):
                    severity = f.get("severity", "?").upper()
                    desc = f.get("description", "")
                    ids = f.get("evidence_ids", [])
                    print(f"\n  [{i}] [{severity}] {desc}")
                    if ids:
                        id_str = ", ".join(str(x) for x in ids[:10])
                        if len(ids) > 10:
                            id_str += f" … (+{len(ids) - 10} more)"
                        print(f"       Evidence IDs: {id_str}")
        except json.JSONDecodeError:
            print(json_block)
=======
    if json_block:
        try:
            parsed = json.loads(json_block)
            cp = parsed.get("cannot_proceed")
            if cp:
                print("\n⚠️   Cannot Proceed\n")
                print(f"  Conclusion : {parsed.get('conclusion', 'N/A')}")
                print(f"  Steps used : {parsed.get('steps_used', 'N/A')}")
                print(f"\n  Reason     : {cp.get('reason', 'N/A')}")
                print(f"\n  Missing    : {cp.get('missing_capability', 'N/A')}")
                alt = cp.get("alternative_command", "")
                if alt:
                    print(f"\n  Alternative:\n    {alt}")
            else:
                print("\n📋  Structured Finding\n")
                print(f"  Conclusion : {parsed.get('conclusion', 'N/A')}")
                print(f"  Steps used : {parsed.get('steps_used', 'N/A')}")
                print(f"  Uncertainty: {parsed.get('uncertainty', 'N/A')}")
                findings = parsed.get("findings", [])
                if findings:
                    print(f"\n  Findings ({len(findings)}):")
                    for i, f in enumerate(findings, 1):
                        severity = f.get("severity", "?").upper()
                        desc = f.get("description", "")
                        ids = f.get("evidence_ids", [])
                        print(f"\n  [{i}] [{severity}] {desc}")
                        if ids:
                            id_str = ", ".join(str(x) for x in ids[:10])
                            if len(ids) > 10:
                                id_str += f" … (+{len(ids) - 10} more)"
                            print(f"       Evidence IDs: {id_str}")
        except json.JSONDecodeError:
            print(json_block)
>>>>>>> REPLACE


### 🤖 Assistant

> 🔧 called: execute_command

Now verify the import still works cleanly and run the tests:

> 🔧 **execute_command** — .venv/bin/python -c "import agent; import prompts; print('OK')" && .venv/bin/python -m pytest tests/ -v --timeout=20 2>&1

### 🤖 Assistant

54/54 still passing. Here's what changed:

**[`prompts.py`](prompts.py)** — added a "When you cannot proceed" section to the system prompt instructing the model to emit the final-answer JSON immediately with a `cannot_proceed` object instead of asking a free-form question. The object has three fields: `reason`, `missing_capability` (with a suggested tool name), and `alternative_command` (a ready-to-paste CLI command).

**[`agent.py`](agent.py:189)** — `_print_final_answer` now checks for `cannot_proceed` in the parsed JSON and renders it with a distinct `⚠️  Cannot Proceed` header, showing reason, missing capability, and the alternative command on separate labelled lines. Normal findings still render exactly as before.

When `python demo.py 3` runs again, instead of an ambiguous interactive prompt the output will look like:

```
⚠️   Cannot Proceed

  Conclusion : The available tools require a specific account_id or resource_id…
  Steps used : 1

  Reason     : No tool can enumerate drive permissions across all ended employees at once.

  Missing    : A tool like find_drive_permissions_for_ended_employees() that joins
               people → workspace_accounts → drive_permissions for all ended people
               would enable this investigation.

  Alternative:
    python agent.py "Which former employees still have active accounts?"
```