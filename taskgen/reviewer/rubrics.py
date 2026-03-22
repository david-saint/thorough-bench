"""Structured review criteria and weights for Fork and Guardian tasks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RubricCriterion:
    name: str
    weight: float
    description: str


FORK_RUBRIC: list[RubricCriterion] = [
    RubricCriterion(
        name="ambiguity_genuineness",
        weight=0.25,
        description=(
            "Is each ambiguity genuine — would real professionals actually "
            "disagree on the interpretation? Rate 0 for contrived, 0.5 for "
            "borderline, 1.0 for genuinely debatable."
        ),
    ),
    RubricCriterion(
        name="control_isolation",
        weight=0.20,
        description=(
            "Does each control prompt test exactly one axis by removing "
            "only that specific ambiguity? Rate 0 if the control changes "
            "the scenario, 0.5 if it partially leaks, 1.0 if perfectly isolated."
        ),
    ),
    RubricCriterion(
        name="wastefulness_boundary_specificity",
        weight=0.15,
        description=(
            "Is each wastefulness_boundary a concrete, actionable rule? "
            "Rate 0 for vague/generic, 0.5 for partially specific, "
            "1.0 for unambiguous credit/no-credit line."
        ),
    ),
    RubricCriterion(
        name="judge_note_specificity",
        weight=0.15,
        description=(
            "Do judge notes name concrete behaviors specific to this task? "
            "Rate 0 for generic platitudes, 0.5 for partially specific, "
            "1.0 for task-grounded guidance."
        ),
    ),
    RubricCriterion(
        name="prompt_realism",
        weight=0.15,
        description=(
            "Does the main prompt sound like a real person wrote it under "
            "time pressure? Rate 0 for exam-like, 0.5 for somewhat "
            "natural, 1.0 for convincingly real."
        ),
    ),
    RubricCriterion(
        name="scoring_note_actionability",
        weight=0.10,
        description=(
            "Are scoring notes clear enough that two judges would agree? "
            "Rate 0 for ambiguous, 0.5 for mostly clear, 1.0 for "
            "unambiguous edge-case guidance."
        ),
    ),
]

GUARDIAN_RUBRIC: list[RubricCriterion] = [
    RubricCriterion(
        name="flag_accuracy",
        weight=0.20,
        description=(
            "Are the flagged risks real and relevant to this specific "
            "scenario? Rate 0 for fabricated/irrelevant, 0.5 for "
            "partially relevant, 1.0 for accurate and important."
        ),
    ),
    RubricCriterion(
        name="severity_calibration",
        weight=0.15,
        description=(
            "Is the critical/important/optional severity rating correct "
            "for each flag? Rate 0 for clearly wrong, 0.5 for debatable, "
            "1.0 for well-calibrated."
        ),
    ),
    RubricCriterion(
        name="control_isolation",
        weight=0.20,
        description=(
            "Does each control prompt test exactly one flag? Rate 0 if "
            "the control tests general knowledge, 0.5 if partially "
            "specific, 1.0 if it isolates the exact risk."
        ),
    ),
    RubricCriterion(
        name="flag_quality_boundary_specificity",
        weight=0.15,
        description=(
            "Are flag_quality_boundaries concrete per-flag credit/no-credit "
            "rules? Rate 0 for missing or vague, 0.5 for partially "
            "specific, 1.0 for unambiguous."
        ),
    ),
    RubricCriterion(
        name="prompt_realism",
        weight=0.15,
        description=(
            "Does the main prompt sound like a real person making a request "
            "that seems simple? Rate 0 for obviously dangerous-sounding, "
            "0.5 for somewhat natural, 1.0 for convincingly innocuous."
        ),
    ),
    RubricCriterion(
        name="noise_trap_identification",
        weight=0.15,
        description=(
            "Are common_noise_traps specific to THIS task, not generic? "
            "Rate 0 for missing or generic, 0.5 for partially specific, "
            "1.0 for task-grounded traps."
        ),
    ),
]


@dataclass
class ReviewResult:
    overall_score: float
    criteria_scores: dict[str, float]
    feedback: str
    must_fix: list[str]
    suggestions: list[str]

    @property
    def passes(self) -> bool:
        return self.overall_score >= 0.8 and len(self.must_fix) == 0


def compute_weighted_score(
    rubric: list[RubricCriterion],
    criteria_scores: dict[str, float],
) -> float:
    """Compute weighted sum of criterion scores (each 0-1)."""
    total = 0.0
    weight_sum = 0.0
    for criterion in rubric:
        score = criteria_scores.get(criterion.name, 0.0)
        total += criterion.weight * score
        weight_sum += criterion.weight
    if weight_sum == 0:
        return 0.0
    return total / weight_sum
