"""
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
    {
        "id": 3,
        "title": "Drive Permissions",
        "question": "Show drive permissions for ended employees",
        "kwargs": {"debug": True, "max_steps": 15},
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
