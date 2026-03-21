"""OpenRouter client for local MMCE development."""

from __future__ import annotations

import os
import time

import openai
from openai import OpenAI


class OpenRouterClient:
    """Thin wrapper around OpenRouter's OpenAI-compatible API."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "anthropic/claude-sonnet-4",
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.environ["OPENROUTER_API_KEY"]
        self.model = model
        self.timeout = timeout
        self._client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            timeout=timeout,
        )

    def prompt(self, text: str, system_prompt: str | None = None) -> str:
        """Send a single-turn prompt and return the response text.

        Retries up to 3 times on rate-limit or connection errors with
        exponential backoff (1s, 2s, 4s). Auth errors are not retried.
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                return response.choices[0].message.content or ""
            except openai.AuthenticationError:
                raise
            except (openai.RateLimitError, openai.APIConnectionError) as e:
                last_error = e
                if attempt < 2:
                    time.sleep(2**attempt)  # 1s, 2s

        raise last_error  # type: ignore[misc]
