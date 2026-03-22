"""Pydantic + loader validation + quality checks for generated tasks."""

from __future__ import annotations

from pydantic import ValidationError

from mmce.harness.loader import _validate_references
from mmce.harness.schema import AmbiguityAxis, GoldFlag, Task


class SchemaGateError(Exception):
    """Raised when a task fails schema or quality validation."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _normalize_judge_notes(raw_dict: dict) -> dict:
    """Fix common LLM output issues before Pydantic validation.

    The creator model consistently outputs flag_quality_boundaries and
    common_noise_traps as {name: text} dicts instead of [text] lists.
    Convert them to the expected list[str] format.
    """
    jn = raw_dict.get("judge_notes")
    if not isinstance(jn, dict):
        return raw_dict

    for field in ("flag_quality_boundaries", "common_noise_traps"):
        val = jn.get(field)
        if isinstance(val, dict):
            # Convert {flag_name: "boundary text"} → ["flag_name: boundary text"]
            jn[field] = [f"{k}: {v}" for k, v in val.items()]

    return raw_dict


def validate_task(raw_dict: dict) -> tuple[Task, list[str]]:
    """Validate a raw task dict. Returns (Task, warnings) or raises SchemaGateError."""
    errors: list[str] = []
    warnings: list[str] = []

    # 0. Normalize common LLM output quirks
    raw_dict = _normalize_judge_notes(raw_dict)

    # 1. Pydantic schema validation
    try:
        task = Task.model_validate(raw_dict)
    except ValidationError as e:
        errors.append(f"Schema validation failed: {e}")
        raise SchemaGateError(errors)

    # 2. Referential integrity (from loader)
    try:
        _validate_references(task)
    except ValueError as e:
        errors.append(f"Reference validation failed: {e}")
        raise SchemaGateError(errors)

    # 3. Quality checks
    # Minimum items
    if len(task.gold_atomic_items) < 2:
        errors.append(
            f"gold_atomic_items has {len(task.gold_atomic_items)} items, need >= 2"
        )

    # Fork-specific checks
    if task.is_fork:
        axes = task.ambiguity_axes
        blocking_count = sum(1 for a in axes if a.blocking)
        if blocking_count < 1:
            errors.append("Fork task must have at least 1 blocking axis")

        for axis in axes:
            if len(axis.ambiguity) < 50:
                errors.append(
                    f"Axis {axis.item_id}: ambiguity text too short "
                    f"({len(axis.ambiguity)} chars, need >= 50)"
                )
            if len(axis.wastefulness_boundary) < 30:
                errors.append(
                    f"Axis {axis.item_id}: wastefulness_boundary too short "
                    f"({len(axis.wastefulness_boundary)} chars, need >= 30)"
                )

    # Guardian-specific checks
    if task.is_guardian:
        flags = task.gold_flags
        critical_count = sum(1 for f in flags if f.severity.value == "critical")
        if critical_count < 1:
            errors.append("Guardian task must have at least 1 critical severity flag")

        if not task.judge_notes.flag_quality_boundaries:
            errors.append("Guardian task must have flag_quality_boundaries in judge_notes")
        if not task.judge_notes.common_noise_traps:
            errors.append("Guardian task must have common_noise_traps in judge_notes")

        for flag in flags:
            if len(flag.rationale) < 30:
                errors.append(
                    f"Flag {flag.item_id}: rationale too short "
                    f"({len(flag.rationale)} chars, need >= 30)"
                )

    # Control prompt quality
    for cp in task.control_prompts:
        if cp.prompt.strip() == task.prompt.strip():
            errors.append(
                f"Control {cp.control_prompt_id}: prompt is identical to main prompt"
            )
        # Check meaningful difference (at least 10% different characters)
        main_set = set(task.prompt.lower().split())
        ctrl_set = set(cp.prompt.lower().split())
        if main_set and ctrl_set:
            overlap = len(main_set & ctrl_set) / max(len(main_set), len(ctrl_set))
            if overlap > 0.95:
                warnings.append(
                    f"Control {cp.control_prompt_id}: prompt is very similar "
                    f"to main prompt (overlap {overlap:.0%})"
                )

    # Task ID convention
    dimension = task.dimension_alias
    if not task.task_id.startswith(f"{dimension}_st_"):
        errors.append(
            f"task_id {task.task_id!r} does not follow "
            f"'{dimension}_st_{{NNN}}_{{slug}}' convention"
        )

    if errors:
        raise SchemaGateError(errors)

    return task, warnings
