"""MMCE scoring: Absolute Coverage, Conditional Thoroughness, Noise Index.

Implements MMCE spec section 7.2 formulas.
"""

from __future__ import annotations

from mmce.harness.schema import (
    AmbiguityAxis,
    ControlVerdict,
    ForkItemVerdict,
    GoldFlag,
    GuardianItemVerdict,
    Judgments,
    Task,
    TaskResult,
)

# Default construct weights for single-turn track (spec section 7.3)
DEFAULT_CONSTRUCT_WEIGHTS = {
    "uncertainty_monitoring": 0.50,
    "knowledge_boundary_detection": 0.50,
}

# dimension_alias -> construct name mapping
DIMENSION_TO_CONSTRUCT = {
    "fork": "uncertainty_monitoring",
    "guardian": "knowledge_boundary_detection",
}


def score_task(task: Task, judgments: Judgments) -> TaskResult:
    """Compute all MMCE scores for a single task evaluation."""
    capability_map = _build_capability_map(task, judgments)

    if task.is_fork:
        ac, ct = _score_fork(task, judgments, capability_map)
    else:
        ac, ct = _score_guardian(task, judgments, capability_map)

    noise_index = _compute_noise_index(task, judgments)

    return TaskResult(
        task_id=task.task_id,
        absolute_coverage=ac,
        conditional_thoroughness=ct,
        noise_index=noise_index,
        judgments=judgments,
        capability_map=capability_map,
        dimension_alias=task.dimension_alias,
        constructs_present=list(task.constructs_present),
    )


def compute_composite(
    results: list[TaskResult],
    weights: dict[str, float] | None = None,
) -> dict:
    """Compute construct-level and overall composite scores.

    Groups results by dimension_alias -> construct, averages CT per construct,
    then computes weighted composite per spec section 7.3.

    Returns dict with:
        composite_ct, composite_ac, per_construct: {construct: {ct, ac, n}}
    """
    if weights is None:
        weights = DEFAULT_CONSTRUCT_WEIGHTS

    # Group results by construct
    construct_results: dict[str, list[TaskResult]] = {}
    for r in results:
        construct = DIMENSION_TO_CONSTRUCT.get(r.dimension_alias, r.dimension_alias)
        construct_results.setdefault(construct, []).append(r)

    per_construct: dict[str, dict] = {}
    for construct, group in construct_results.items():
        ct_values = [r.conditional_thoroughness for r in group if r.conditional_thoroughness is not None]
        ac_values = [r.absolute_coverage for r in group]

        avg_ct = sum(ct_values) / len(ct_values) if ct_values else None
        avg_ac = sum(ac_values) / len(ac_values) if ac_values else 0.0

        per_construct[construct] = {
            "ct": avg_ct,
            "ac": avg_ac,
            "n": len(group),
        }

    # Weighted composite CT
    weighted_ct_num = 0.0
    weighted_ct_den = 0.0
    weighted_ac_num = 0.0
    weighted_ac_den = 0.0

    for construct, vals in per_construct.items():
        w = weights.get(construct, 0.0)
        if vals["ct"] is not None:
            weighted_ct_num += w * vals["ct"]
            weighted_ct_den += w
        weighted_ac_num += w * vals["ac"]
        weighted_ac_den += w

    composite_ct = weighted_ct_num / weighted_ct_den if weighted_ct_den > 0 else None
    composite_ac = weighted_ac_num / weighted_ac_den if weighted_ac_den > 0 else None

    return {
        "composite_ct": composite_ct,
        "composite_ac": composite_ac,
        "per_construct": per_construct,
    }


def _build_capability_map(task: Task, judgments: Judgments) -> dict[str, int]:
    """Compute capable_i = max(control_success, full_task_success) per item.

    capable_i = 1 if:
    - the model succeeds on the matched control, OR
    - the model succeeds on the item in the full task
    """
    # Build lookup: control_prompt_id -> success
    control_success = {}
    for cv in judgments.control_verdicts:
        control_success[cv.control_prompt_id] = cv.success

    # Build lookup: item_id -> full task success
    task_success = {}
    for v in judgments.fork_verdicts:
        task_success[v.item_id] = 1 if (v.execution_score == 1.0 and v.correct == 1) else 0
    for v in judgments.guardian_verdicts:
        task_success[v.item_id] = 1 if (v.complete == 1 and v.correct == 1) else 0

    capability_map = {}
    for item in task.gold_atomic_items:
        cs = control_success.get(item.control_prompt_id, 0)
        ts = task_success.get(item.item_id, 0)
        capability_map[item.item_id] = max(cs, ts)

    return capability_map


def _score_fork(
    task: Task,
    judgments: Judgments,
    capability_map: dict[str, int],
) -> tuple[float, float | None]:
    """Score Fork (Uncertainty Monitoring) task."""
    verdict_map = {v.item_id: v for v in judgments.fork_verdicts}

    numerator = 0.0
    denominator_ac = 0.0
    denominator_ct = 0.0

    for item in task.ambiguity_axes:
        v = verdict_map.get(item.item_id)
        if v is None:
            # Missing verdict = 0 credit
            denominator_ac += item.value_i
            denominator_ct += item.value_i * capability_map.get(item.item_id, 0)
            continue

        credit = item.value_i * v.execution_score * v.correct
        numerator += credit
        denominator_ac += item.value_i
        denominator_ct += item.value_i * capability_map.get(item.item_id, 0)

    ac = numerator / denominator_ac if denominator_ac > 0 else 0.0
    ct = numerator / denominator_ct if denominator_ct > 0 else None

    return ac, ct


def _score_guardian(
    task: Task,
    judgments: Judgments,
    capability_map: dict[str, int],
) -> tuple[float, float | None]:
    """Score Guardian (Knowledge Boundary Detection) task."""
    verdict_map = {v.item_id: v for v in judgments.guardian_verdicts}

    numerator = 0.0
    denominator_ac = 0.0
    denominator_ct = 0.0

    for item in task.gold_flags:
        v = verdict_map.get(item.item_id)
        if v is None:
            denominator_ac += item.value_i
            denominator_ct += item.value_i * capability_map.get(item.item_id, 0)
            continue

        credit = item.value_i * v.complete * v.correct
        numerator += credit
        denominator_ac += item.value_i
        denominator_ct += item.value_i * capability_map.get(item.item_id, 0)

    ac = numerator / denominator_ac if denominator_ac > 0 else 0.0
    ct = numerator / denominator_ct if denominator_ct > 0 else None

    return ac, ct


def _compute_noise_index(task: Task, judgments: Judgments) -> float:
    """Noise Index = sum(noise_weight_j) / max(sum(value_i), 1)."""
    total_noise = sum(n.weight for n in judgments.noise_instances)
    total_value = max(task.total_value(), 1.0)
    return total_noise / total_value
