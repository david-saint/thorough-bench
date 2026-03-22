"""Fork task review: rubric evaluation via reviewer model."""

from __future__ import annotations

import json

from taskgen.llm.client import TaskGenLLMClient
from taskgen.reviewer.rubrics import (
    FORK_RUBRIC,
    ReviewResult,
    compute_weighted_score,
)


FORK_REVIEW_SYSTEM = """\
You are an expert benchmark quality reviewer for the MMCE (Metacognitive \
Monitoring and Control Evaluation) benchmark. You evaluate Fork tasks — tasks \
that test whether AI models recognize genuine ambiguity in user requests.

Your job is to rigorously evaluate each task against the rubric criteria and \
provide actionable feedback. Be strict but fair. A task that passes review \
should be publication-quality."""


def _build_fork_review_prompt(task_json: dict) -> str:
    rubric_desc = "\n".join(
        f"- {c.name} (weight {c.weight}): {c.description}"
        for c in FORK_RUBRIC
    )

    return f"""\
Review this Fork task for quality and correctness.

TASK JSON:
```json
{json.dumps(task_json, indent=2)}
```

RUBRIC (score each criterion 0.0 to 1.0):
{rubric_desc}

For each criterion, provide a score and brief justification.
Then provide:
- must_fix: list of issues that MUST be fixed before the task can pass (empty if none)
- suggestions: list of optional improvements

Return ONLY valid JSON in this format:
{{
  "criteria_scores": {{
    "ambiguity_genuineness": 0.9,
    "control_isolation": 0.8,
    "wastefulness_boundary_specificity": 0.7,
    "judge_note_specificity": 0.8,
    "prompt_realism": 0.9,
    "scoring_note_actionability": 0.8
  }},
  "feedback": "Overall assessment in 2-3 sentences.",
  "must_fix": ["specific issue 1", "specific issue 2"],
  "suggestions": ["optional improvement 1"]
}}"""


def review_fork_task(
    client: TaskGenLLMClient,
    task_json: dict,
    model_override: str | None = None,
) -> ReviewResult:
    """Review a Fork task and return structured feedback."""
    user_prompt = _build_fork_review_prompt(task_json)
    result = client.generate_json(user_prompt, FORK_REVIEW_SYSTEM, model_override)

    criteria_scores = result.get("criteria_scores", {})
    # Ensure all criteria are present with defaults
    for criterion in FORK_RUBRIC:
        if criterion.name not in criteria_scores:
            criteria_scores[criterion.name] = 0.0

    overall = compute_weighted_score(FORK_RUBRIC, criteria_scores)

    return ReviewResult(
        overall_score=overall,
        criteria_scores=criteria_scores,
        feedback=result.get("feedback", ""),
        must_fix=result.get("must_fix", []),
        suggestions=result.get("suggestions", []),
    )
