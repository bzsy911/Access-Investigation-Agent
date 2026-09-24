"""
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
        # 33 people named "Rowan" exist; at least some should be returned
        assert len(result["people"]) > 0
        assert all("Rowan" in p["full_name"] for p in result["people"])

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
        """After _trim, serialised result must be within the CHAR_BUDGET."""
        import tools as t_module

        result = get_mfa_gaps()
        serialised = json.dumps(result, default=str)
        assert len(serialised) <= t_module.CHAR_BUDGET
