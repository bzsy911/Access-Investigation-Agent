"""
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
        return _trim(result, primary_key="gaps")
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
