"""
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
