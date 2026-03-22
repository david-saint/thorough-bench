"""OpenRouter client with JSON mode, reasoning, cost tracking, and retries."""

from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass, field

import openai
from openai import OpenAI


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""


@dataclass
class CostTracker:
    calls: list[TokenUsage] = field(default_factory=list)

    def record(self, usage: TokenUsage) -> None:
        self.calls.append(usage)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self.calls)

    @property
    def total_completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self.calls)

    def summary_by_model(self) -> dict[str, dict[str, int]]:
        by_model: dict[str, dict[str, int]] = {}
        for c in self.calls:
            if c.model not in by_model:
                by_model[c.model] = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}
            by_model[c.model]["prompt_tokens"] += c.prompt_tokens
            by_model[c.model]["completion_tokens"] += c.completion_tokens
            by_model[c.model]["calls"] += 1
        return by_model


class TaskGenLLMClient:
    """OpenRouter client extended for task generation workloads."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "anthropic/claude-opus-4.6",
        timeout: float = 300.0,
        reasoning_effort: str = "xhigh",
    ):
        self.api_key = api_key or os.environ["OPENROUTER_API_KEY"]
        self.model = model
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort
        self.cost_tracker = CostTracker()
        self._client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            timeout=timeout,
        )

    def generate(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        model_override: str | None = None,
    ) -> str:
        """Send a prompt and return raw response text.

        Retries up to 5 times with exponential backoff + jitter on rate-limit
        or connection errors. Auth errors are not retried.
        """
        model = model_override or self.model
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        last_error: Exception | None = None
        for attempt in range(5):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    extra_body={
                        "reasoning": {"effort": self.reasoning_effort},
                        "include_reasoning": True,
                    },
                )

                # Track token usage
                if response.usage:
                    self.cost_tracker.record(TokenUsage(
                        prompt_tokens=response.usage.prompt_tokens or 0,
                        completion_tokens=response.usage.completion_tokens or 0,
                        total_tokens=response.usage.total_tokens or 0,
                        model=model,
                    ))

                return response.choices[0].message.content or ""

            except openai.AuthenticationError:
                raise
            except (openai.RateLimitError, openai.APIConnectionError) as e:
                last_error = e
                if attempt < 4:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(backoff)

        raise last_error  # type: ignore[misc]

    def generate_json(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        model_override: str | None = None,
    ) -> dict:
        """Generate and parse a JSON response, with retry on parse failures."""
        last_error: Exception | None = None
        current_user = user_prompt

        for attempt in range(3):
            raw = self.generate(current_user, system_prompt, model_override)
            try:
                return _parse_json(raw)
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                if attempt < 2:
                    current_user = (
                        f"{user_prompt}\n\n"
                        f"YOUR PREVIOUS RESPONSE WAS NOT VALID JSON. "
                        f"Error: {e}\n"
                        f"Please return ONLY valid JSON, no other text."
                    )

        raise ValueError(
            f"Failed to get valid JSON after 3 attempts: {last_error}"
        )


def _extract_json_object(text: str) -> str:
    """Extract the first balanced JSON object from text."""
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found")
    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            if in_string:
                escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("Unbalanced braces in JSON")


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from response, handling markdown fences."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        candidate = match.group(1)
    else:
        candidate = _extract_json_object(text)
    return json.loads(candidate)
