"""
runner.py — Thin wrapper around the OpenAI-compatible OpenRouter API.

Responsibilities:
- Load the API key from the environment / .env file.
- Provide a single ``chat_completion()`` call that the ReAct loop uses.
- Convert the OpenRouter response into a normalised dict the loop can consume.

OpenRouter exposes an OpenAI-compatible endpoint, so we use the ``openai``
Python SDK pointed at ``https://openrouter.ai/api/v1``.  The API key is read
from the ``OPENROUTER_API_KEY`` environment variable (see ``.env.example``).
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.environ.get("MODEL", "google/gemini-2.5-flash")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _get_client() -> OpenAI:
    """Instantiate an OpenAI client pointed at the OpenRouter base URL.

    Raises:
        OSError: if ``OPENROUTER_API_KEY`` is not set in the environment.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise OSError(
            "OPENROUTER_API_KEY is not set. "
            "Copy .env.example to .env and fill in your key."
        )
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
    )


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Send a chat completion request to OpenRouter and return a normalised response.

    Args:
        messages: Conversation history in OpenAI message format.
        tools:    List of tool schemas (``TOOL_SCHEMAS`` entries from ``tools.py``).
                  Pass an empty list to suppress tool calling and force a text reply.
        model:    Model identifier recognised by OpenRouter (default ``DEFAULT_MODEL``).

    Returns:
        A dict with keys:
        - ``"role"``       – always ``"assistant"``
        - ``"content"``    – text reply from the model, or ``None`` if the model
                             responded with tool calls only
        - ``"tool_calls"`` – list of ``{"id", "name", "arguments"}`` dicts,
                             empty when the model produced no tool calls
    """
    client = _get_client()

    # Convert our tool schemas to the OpenAI function-call wrapper format.
    # When no tools are available we omit both parameters entirely so the SDK
    # type overloads resolve correctly (passing None would fail type checking).
    openai_tools = [{"type": "function", "function": schema} for schema in tools]

    kwargs: dict[str, Any] = {"model": model, "messages": messages}
    if openai_tools:
        kwargs["tools"] = openai_tools
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)  # type: ignore[arg-type]

    choice = response.choices[0]
    msg = choice.message

    tool_calls: list[dict[str, Any]] = []
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
