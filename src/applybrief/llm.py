"""LLM provider abstraction via LiteLLM.

Single env var picks the model: APPLYBRIEF_MODEL.
LiteLLM uses the provider's own env var for the API key
(ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, etc.).

Default: anthropic/claude-haiku-4-5 (sweet-spot cost/quality).
Set APPLYBRIEF_MODEL=groq/llama-3.1-70b-versatile for free tier,
or ollama/llama3.1 for fully local.
"""

from __future__ import annotations

import os

import litellm

DEFAULT_MODEL = "anthropic/claude-haiku-4-5"


def complete(system: str, user: str, *, model: str | None = None, max_tokens: int = 4096) -> str:
    """Single round-trip completion. Returns plain text."""
    model = model or os.getenv("APPLYBRIEF_MODEL", DEFAULT_MODEL)
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
