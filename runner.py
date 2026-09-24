"""
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

DEFAULT_MODEL = os.environ.get("MODEL", "google/gemini-2.5-flash")
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
