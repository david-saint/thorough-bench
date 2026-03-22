"""Guardian task creation and revision."""

from __future__ import annotations

from taskgen.creator.prompts import (
    build_guardian_creation_prompt,
    build_guardian_revision_prompt,
)
from taskgen.llm.client import TaskGenLLMClient
from taskgen.scenarios.registry import ScenarioBrief


def create_guardian_task(
    client: TaskGenLLMClient,
    scenario: ScenarioBrief,
    task_id: str,
    model_override: str | None = None,
) -> dict:
    """Create a new Guardian task from a scenario brief. Returns raw dict."""
    system, user = build_guardian_creation_prompt(
        scenario_domain=scenario.domain,
        scenario_action=scenario.action,
        scenario_time_pressure=scenario.time_pressure,
        scenario_constraint=scenario.constraint,
        task_id=task_id,
    )
    return client.generate_json(user, system, model_override)


def revise_guardian_task(
    client: TaskGenLLMClient,
    previous_json: dict,
    must_fix: list[str],
    suggestions: list[str],
    model_override: str | None = None,
) -> dict:
    """Revise a Guardian task based on reviewer feedback. Returns raw dict."""
    system, user = build_guardian_revision_prompt(previous_json, must_fix, suggestions)
    return client.generate_json(user, system, model_override)
