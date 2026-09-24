# Access Investigation Agent — Submission

---

## 1. Setup Instructions

### Prerequisites

- Python 3.11 or later
- An OpenRouter API key (provided separately in `token.txt`)

### Install

```bash
# Clone / unzip the repository, then:
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt    # includes runtime + dev tools
```

Or with `uv` (faster, uses the pinned lock file):

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements-dev.lock
```

### Configure the API key

```bash
cp .env.example .env
# Edit .env and set:
#   OPENROUTER_API_KEY=<your key from token.txt>
```

The key is read from the `OPENROUTER_API_KEY` environment variable and never
written to source code.  `.env` is listed in `.gitignore`.

### Run an investigation

```bash
# Ad-hoc question
python agent.py "Which former employees still have active accounts?"

# With debug output (prints every tool call and result)
python agent.py --debug "Which users on critical apps are not enrolled in MFA?"

# Run all prepared demos (3 successful + 3 adversarial)
python demo.py

# Run only the successful demos
python demo.py success

# Run a specific demo by ID
python demo.py 1
```

### Run the tests

```bash
python -m pytest tests/ -v
```

All 54 tests run against the real (read-only) SQLite database and complete in
under one second.

---

## 2. Scope and Architecture

### Scope

The problem space is broad — any access-control question across five connected
systems.  I narrowed it to three high-value investigation workflows that are
fully answerable from the snapshot data:

| # | Workflow | Why |
|---|---|---|
| 1 | **Offboarding gaps** | Classic SOC finding; clear anomaly definition; every result has concrete IDs |
| 2 | **MFA gap analysis** | Contained to two tables; direct risk signal on critical apps |
| 3 | **Post-termination activity** | Combines offboarding data with the audit trail; shows multi-hop reasoning |

The remaining investigation types — privilege escalation, OAuth scope sprawl,
external Drive sharing — are listed in "What to build next" and are covered by
the adversarial demos that expose current tool limits.

### Architecture

```
agent.py          CLI entry point; runs the ReAct loop
  │
  ├── runner.py   OpenRouter API wrapper (thin openai SDK shim)
  ├── tools.py    Nine named tools that query the read-only SQLite database
  └── prompts.py  System prompt + compact schema digest injected at turn 0
```

**Pattern: ReAct (Reason + Act) loop, single-threaded.**

The agent iterates: send messages → receive tool calls → execute tools →
append results → repeat.  The loop terminates when the model emits a plain-text
final answer or the step budget (default 12 tool calls) is exhausted.

A single-agent ReAct loop was the right choice here:
- The investigation is inherently iterative: a first query surfaces an anomaly,
  follow-ups gather corroborating evidence.
- The data is relational and fragmented across tables.  No single query answers
  a full question; the agent must chain lookups.
- No planning phase benefits from a multi-agent split.  One capable model in a
  loop is simpler and more auditable.

**Model: `google/gemini-2.5-flash` via OpenRouter.**

Chosen for its 1 M token context window (holds many tool results simultaneously),
strong function-calling support, and low cost.

**Tool design.**

Nine SQL-backed tools with parameterised queries.  The model never writes raw
SQL — it calls named tools with structured arguments.  Each tool:
- Opens the database read-only (`PRAGMA query_only = ON`).
- Returns a `_meta` dict with `total_count`, `returned`, `truncated`, and
  `query_time_ms`.
- Trims its output to ~6,000 characters to prevent context overflow.

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

**Context management.**

- A compact schema digest (~600 tokens) is injected into the system prompt —
  table names, key columns, and the joins that matter.  Not the full `SCHEMA.md`.
- Tool results are capped at ~6,000 characters each.
- The step budget bounds total context per investigation.
- No RAG, no trajectory summarisation: Gemini's 1 M window is sufficient for
  a single session.

**Output contract.**

Every final answer is a structured JSON block:

```json
{
  "conclusion": "Plain-language summary.",
  "findings": [
    {
      "description": "Specific finding with context.",
      "severity": "high|medium|low",
      "evidence_ids": ["id1", "id2"]
    }
  ],
  "uncertainty": "What could not be determined and why.",
  "steps_used": 4
}
```

When the available tools cannot answer the question, the model is required to
emit a `cannot_proceed` block instead of asking a free-form question or going
silent — see the adversarial demos.

---

## 3. Example Investigations

### Investigation 1 — Offboarding Residual Access

**Question:** "Which former employees still have active accounts?"

**Tool calls made (4 steps):**
1. `find_offboarding_gaps({})` — retrieve all ended employees with active accounts
2. `lookup_person({"query": "per_001945"})` — verify Ariel Chen's accounts
3. `lookup_person({"query": "per_001941"})` — verify Rowan Mercer's accounts
4. `lookup_person({"query": "per_001942"})` — verify Talia Brooks's accounts

**Agent output:**

```
📋  Structured Finding

  Conclusion : Three former employees, Ariel Chen, Rowan Mercer, and Talia Brooks,
               still have active accounts across various systems despite their
               employment having ended.
  Steps used : 4
  Uncertainty: The reason for the active accounts after the end of employment is
               not determined by the available tools.

  Findings (3):

  [1] [HIGH] Ariel Chen (per_001945) has an active GitHub account (gha_001945),
       an active IdP account (idpa_001945), and an active Workspace account
       (gwa_001945) even though her employment ended on 2026-08-03.
       Evidence IDs: per_001945, gha_001945, idpa_001945, gwa_001945

  [2] [HIGH] Rowan Mercer (per_001941) has an active GitHub account (gha_001941),
       an active IdP account (idpa_001941), and an active Workspace account
       (gwa_001941) despite employment ending on 2026-07-25. Last GitHub activity
       was 2026-07-30.
       Evidence IDs: per_001941, gha_001941, idpa_001941, gwa_001941

  [3] [HIGH] Talia Brooks (per_001942) has an active GitHub account (gha_001942)
       and an active IdP account (idpa_001942) despite employment ending on
       2026-07-08. Her Workspace account is archived.
       Evidence IDs: per_001942, gha_001942, idpa_001942
```

Full output: [`examples/investigation_1_offboarding.txt`](examples/investigation_1_offboarding.txt)

---

### Investigation 2 — MFA Gap Analysis

**Question:** "Which users on critical apps are not enrolled in MFA?"

**Tool calls made (1 step):**
1. `get_mfa_gaps({"sensitivity": "critical"})` — retrieve all active users on
   critical apps with non-enrolled MFA status, with per-app summary

**Agent output (selected findings):**

```
📋  Structured Finding

  Conclusion : Multiple users lack MFA enrollment on critical applications like
               AWS Console and Corporate VPN. The full list is truncated; initial
               findings indicate a significant number of affected users.
  Steps used : 1
  Uncertainty: The initial query returned a truncated list; the full extent of
               the problem is unknown without a more targeted per-app query.

  Findings (3):

  [1] [HIGH] Fatima Robinson (per_000498) is not enrolled in MFA for AWS Console
       (app_0008), a critical application.
       Evidence IDs: per_000498, idpa_000498, aua_001969, app_0008

  [2] [HIGH] Maya Robinson (per_000198) is not enrolled in MFA for AWS Console
       (app_0008), a critical application.
       Evidence IDs: per_000198, idpa_000198, aua_000779, app_0008

  [3] [MEDIUM] Several other users have 'unknown' MFA enrollment status for
       critical applications, which also poses a security risk.
       Evidence IDs: per_000351, idpa_000351, aua_001381, per_001251, idpa_001251,
                     aua_004948, per_002004, idpa_002004, aua_007936 … (+14 more)
```

Full output: [`examples/investigation_2_mfa_gaps.txt`](examples/investigation_2_mfa_gaps.txt)

---

### Investigation 3 — Post-Termination Activity Deep Dive

**Question:** "Show me the full access profile for Rowan Mercer: all accounts,
group memberships, application access, and any audit events after their
employment ended."

**Tool calls made (6 steps):**
1. `lookup_person({"query": "Rowan Mercer"})` — resolve person_id
2. `get_person_access_summary({"person_id": "per_001941"})` — full access snapshot
3. `get_audit_events({"actor_id": "idpa_001941", "since": "2026-07-25T00:00:00Z"})` — IdP events post-termination
4. `get_audit_events({"actor_id": "gha_001941", "system": "github", "since": "2026-07-25T00:00:00Z"})` — GitHub events post-termination
5. `get_audit_events({"actor_id": "gwa_001941", "system": "workspace", "since": "2026-07-25T00:00:00Z"})` — Workspace events post-termination
6. `find_offboarding_gaps({"systems": ["idp","workspace","github"], "statuses": ["ended"]})` — corroborate

**Agent output:**

```
📋  Structured Finding

  Conclusion : Rowan Mercer, whose employment ended on 2026-07-25, still has active
               accounts in IdP, Workspace, and GitHub. There is evidence of activity
               on their GitHub and Workspace accounts after their end date.
  Steps used : 6
  Uncertainty: The exact nature of the accessed GitHub repositories and Drive
               resource is unknown without further investigation.

  Findings (3):

  [1] [HIGH] Rowan Mercer has active IdP, Workspace, and GitHub accounts despite
       employment ending on 2026-07-25. This indicates a failed offboarding.
       Evidence IDs: per_001941, idpa_001941, gwa_001941, gha_001941

  [2] [HIGH] Rowan Mercer's GitHub account (gha_001941) pushed to 'identity-service'
       repository (ghr_000001) on 2026-08-14T18:36:44Z and fetched ghr_000039 on
       2026-08-10T05:46:39Z — both after the employment end date.
       Evidence IDs: gha_001941, evt_00048004, evt_00014550, ghr_000001, ghr_000039

  [3] [HIGH] Rowan Mercer's Workspace account (gwa_001941) viewed a Drive resource
       (drv_000110) on 2026-08-12T01:31:13Z and had a successful login on
       2026-08-05T02:04:06Z — both after the employment end date.
       Evidence IDs: gwa_001941, evt_00018627, evt_00023825, drv_000110
```

Full output: [`examples/investigation_3_person_deep_dive.txt`](examples/investigation_3_person_deep_dive.txt)

---

## 4. How I Checked Whether the Agent Was Working

### 4a. Unit tests (54 tests, `tests/test_tools.py`)

Every tool function is tested against the real SQLite database:

- **Shape tests**: `_meta` field present, expected keys exist, list types correct.
- **Value tests**: Known fixtures (e.g. `per_001941` is in offboarding gaps,
  `idpa_001941` appears in the person's IdP accounts).
- **Filter tests**: `systems=["idp"]` returns only IdP accounts; `sensitivity="critical"`
  returns only critical-app gaps; `limit=5` returns at most 5 events.
- **Edge cases**: Missing person → `{"error": ...}`; no actor/target → `{"error": ...}`;
  `run_sql` disabled → `{"error": "disabled"}`.
- **Truncation tests**: After `_trim`, serialised result fits within `CHAR_BUDGET`;
  `_meta.truncated` flag is set when rows were removed.

Run with: `python -m pytest tests/ -v` → 54/54 pass in < 1 second.

### 4b. Smoke tests (manual)

Both core investigations were run against the live API and the cited IDs were
verified by direct SQLite queries:

```bash
sqlite3 input_data/access_snapshot.sqlite \
  "SELECT person_id, full_name, employment_status FROM people WHERE person_id='per_001941';"
# → per_001941 | Rowan Mercer | ended

sqlite3 input_data/access_snapshot.sqlite \
  "SELECT account_id, status FROM idp_accounts WHERE person_id='per_001941';"
# → idpa_001941 | active
```

Every `evidence_id` in the three investigation outputs above was verified this way.

### 4c. Adversarial / failure-mode testing

The `DEMOS_ADVERSARIAL` list in `demo.py` (demos 4–6) tests three distinct
failure modes:

| Demo | Question | Expected behaviour |
|---|---|---|
| 4 | Drive permissions for all ended employees | `cannot_proceed` — tool requires a specific account/resource ID |
| 5 | OAuth scope sprawl | `cannot_proceed` — no tool surfaces `workspace_oauth_grants` |
| 6 | Unusual IP login detection | `cannot_proceed` — no IP allowlist or geolocation data available |

Run with: `python demo.py adversarial`

### 4d. Truncation correctness

`TestTruncation::test_result_fits_char_budget` calls `get_mfa_gaps()` (the
tool with the largest result set — 242 gaps) and asserts that the returned JSON
is within `CHAR_BUDGET` (6,000 chars).  `test_meta_truncated_flag_present`
checks the `truncated` flag is always present in `_meta`, even when no trimming
occurred.

---

## 5. Known Limitations and What to Build Next

### Known limitations

| Limitation | Impact |
|---|---|
| **Nested group depth cap (3)** | Groups nested more than 3 levels deep may have unresolved indirect members; `get_group_members` notes the cap in its return value |
| **Incomplete audit logs** | Absence of an event does not prove absence of activity; the system prompt instructs the agent to qualify such conclusions |
| **Snapshot only** | Data is frozen at `2026-08-15T12:00:00Z`; no real-time changes are visible |
| **`person_id` nulls** | Accounts without a matched person are excluded from person-centric queries; the agent notes this gap but does not attempt fuzzy matching |
| **No cohort-level permission queries** | Tools like `get_drive_permissions` require a specific account or resource ID; bulk enumeration (e.g. "all ended employees' Drive permissions") is not supported — the agent correctly reports this via `cannot_proceed` |
| **`workspace_oauth_grants` not surfaced** | No tool queries OAuth grants; broad-scope third-party access cannot be investigated |
| **No cross-system dedup** | A person with multiple accounts may appear multiple times in some aggregate queries |
| **`run_sql` disabled by default** | Advanced ad-hoc queries require `DEBUG_SQL=true`; this is intentional for safety |

### What to build next

1. **`find_github_repo_permissions` tool** — query `github_repo_collaborators`
   and `github_team_repo_permissions` globally, filterable by repository
   sensitivity and permission level.  This would enable the "admin access on
   sensitive repos" investigation that currently triggers `cannot_proceed`.

2. **`get_oauth_grants` tool** — surface `workspace_oauth_grants` rows with
   scope analysis.  Enables the OAuth scope sprawl investigation.

3. **`find_offboarding_drive_gaps` tool** — enumerate ended employees' Workspace
   accounts and join to `drive_permissions` in a single query, returning the
   cohort-level view that `get_drive_permissions` cannot provide alone.

4. **Privilege escalation investigation** — detect accounts with admin roles
   added recently by joining `idp_group_memberships` and `audit_events`.

5. **Confidence scoring** — attach a numeric confidence score to each finding
   based on how many corroborating evidence sources agree (e.g. both the
   snapshot and the audit log confirm a finding → higher confidence).

6. **Automated anomaly report** — run all investigations on a schedule and
   generate a daily HTML summary of open offboarding gaps and MFA gaps.
