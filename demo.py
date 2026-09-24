"""
demo.py — Run prepared investigation demos to showcase agent capabilities and limits.

Two demo categories:
  - Successful demos: investigations the agent handles end-to-end with findings and evidence IDs.
  - Adversarial demos: questions that expose tool limits and trigger the structured
    cannot_proceed fallback output, showing how the agent fails gracefully.

Usage:
    python demo.py                # run all demos in sequence (successful first, then adversarial)
    python demo.py success        # run only successful demos
    python demo.py adversarial    # run only adversarial demos
    python demo.py 1 2            # run specific demos by ID (IDs are unique across both lists)
"""

import sys

from agent import _print_final_answer, run_investigation

# ---------------------------------------------------------------------------
# Successful investigations — the agent produces findings with evidence IDs
# ---------------------------------------------------------------------------

DEMOS_SUCCESSFUL = [
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
    {
        "id": 3,
        "title": "Post-Termination Activity Deep Dive",
        "question": (
            "Show me the full access profile for Rowan Mercer: all accounts, "
            "group memberships, application access, and any audit events after "
            "their employment ended."
        ),
        "kwargs": {},
    },
]

# ---------------------------------------------------------------------------
# Adversarial investigations — the agent hits a tool limit and explains why,
# triggering the structured cannot_proceed fallback response.
# ---------------------------------------------------------------------------

DEMOS_ADVERSARIAL = [
    {
        "id": 4,
        "title": "Drive Permissions Across All Ended Employees (tool gap)",
        "question": "Show drive permissions for all ended employees",
        "kwargs": {},
        "expected_behaviour": (
            "get_drive_permissions requires a specific account_id or resource_id — "
            "it cannot enumerate permissions across an entire cohort. "
            "The agent should emit cannot_proceed with an alternative command."
        ),
    },
    {
        "id": 5,
        "title": "OAuth Scope Sprawl (unsupported query pattern)",
        "question": (
            "Which users have granted third-party OAuth applications access to "
            "their Workspace account with broad or sensitive scopes?"
        ),
        "kwargs": {},
        "expected_behaviour": (
            "No tool surfaces workspace_oauth_grants data. "
            "The agent should recognise this gap and emit cannot_proceed "
            "with a suggested get_oauth_grants tool."
        ),
    },
    {
        "id": 6,
        "title": "Unusual IP Login Detection (out of scope)",
        "question": (
            "Find all users who authenticated from IP addresses outside our "
            "known corporate IP ranges in the last 30 days."
        ),
        "kwargs": {},
        "expected_behaviour": (
            "The agent has no IP allowlist or geolocation data, and audit logs are "
            "incomplete. It should emit cannot_proceed explaining the missing "
            "IP-baseline capability rather than speculating."
        ),
    },
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

_ALL_DEMOS = DEMOS_SUCCESSFUL + DEMOS_ADVERSARIAL
_DEMO_BY_ID = {str(d["id"]): d for d in _ALL_DEMOS}


def run_demo(demo: dict) -> None:
    category = "SUCCESSFUL" if demo in DEMOS_SUCCESSFUL else "ADVERSARIAL"
    print(f"\n{'═' * 64}")
    print(f"  DEMO {demo['id']} [{category}] — {demo['title']}")
    if "expected_behaviour" in demo:
        print(f"  Expected: {demo['expected_behaviour']}")
    print(f"{'═' * 64}")
    answer = run_investigation(demo["question"], **demo["kwargs"])
    _print_final_answer(answer)


def main() -> None:
    args = sys.argv[1:]

    if not args:
        selected = _ALL_DEMOS
    elif args == ["success"]:
        selected = DEMOS_SUCCESSFUL
    elif args == ["adversarial"]:
        selected = DEMOS_ADVERSARIAL
    else:
        selected = []
        unknown = []
        for arg in args:
            if arg in _DEMO_BY_ID:
                selected.append(_DEMO_BY_ID[arg])
            else:
                unknown.append(arg)
        if unknown:
            valid = sorted(_DEMO_BY_ID.keys(), key=int)
            print(f"Unknown demo IDs: {unknown}. Available: {valid}")
            sys.exit(1)

    for demo in selected:
        run_demo(demo)


if __name__ == "__main__":
    main()
