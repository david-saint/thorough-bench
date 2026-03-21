"""Load and validate MMCE task YAML files into typed Pydantic models."""

from __future__ import annotations

from pathlib import Path

import yaml

from mmce.harness.schema import AmbiguityAxis, GoldFlag, Task

DIMENSION_EXPECTED_CONSTRUCTS: dict[str, str] = {
    "fork": "uncertainty_monitoring",
    "guardian": "knowledge_boundary_detection",
}


def load_task(path: str | Path) -> Task:
    """Load a single task YAML file into a validated Task model."""
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)
    task = Task.model_validate(data)
    _validate_references(task)
    return task


def load_all_tasks(tasks_dir: str | Path) -> list[Task]:
    """Load all task YAML files from a directory tree."""
    tasks_dir = Path(tasks_dir)
    tasks = []
    for yaml_path in sorted(tasks_dir.rglob("*.yaml")):
        tasks.append(load_task(yaml_path))
    return tasks


def _validate_references(task: Task) -> None:
    """Validate referential integrity, uniqueness, and consistency."""
    # --- Non-empty items ---
    if len(task.gold_atomic_items) < 1:
        raise ValueError(f"Task {task.task_id}: gold_atomic_items must not be empty")

    # --- item_id uniqueness ---
    item_ids: list[str] = [item.item_id for item in task.gold_atomic_items]
    seen_item_ids: set[str] = set()
    for iid in item_ids:
        if iid in seen_item_ids:
            raise ValueError(
                f"Task {task.task_id}: duplicate item_id {iid!r} in gold_atomic_items"
            )
        seen_item_ids.add(iid)

    # --- control_prompt_id uniqueness ---
    seen_control_ids: set[str] = set()
    for cp in task.control_prompts:
        if cp.control_prompt_id in seen_control_ids:
            raise ValueError(
                f"Task {task.task_id}: duplicate control_prompt_id {cp.control_prompt_id!r}"
            )
        seen_control_ids.add(cp.control_prompt_id)

    # --- dimension_alias consistency ---
    if task.dimension_alias == "fork":
        for item in task.gold_atomic_items:
            if not isinstance(item, AmbiguityAxis):
                raise ValueError(
                    f"Task {task.task_id}: dimension_alias is 'fork' but item "
                    f"{item.item_id!r} is {type(item).__name__}, expected AmbiguityAxis"
                )
    elif task.dimension_alias == "guardian":
        for item in task.gold_atomic_items:
            if not isinstance(item, GoldFlag):
                raise ValueError(
                    f"Task {task.task_id}: dimension_alias is 'guardian' but item "
                    f"{item.item_id!r} is {type(item).__name__}, expected GoldFlag"
                )

    # --- constructs_present / dimension_alias coherence ---
    expected_construct = DIMENSION_EXPECTED_CONSTRUCTS.get(task.dimension_alias)
    if expected_construct and expected_construct not in task.constructs_present:
        raise ValueError(
            f"Task {task.task_id}: dimension_alias {task.dimension_alias!r} expects "
            f"construct {expected_construct!r} in constructs_present, "
            f"got {task.constructs_present}"
        )

    # --- control_prompt_id references ---
    control_ids = seen_control_ids
    for item in task.gold_atomic_items:
        if item.control_prompt_id not in control_ids:
            raise ValueError(
                f"Task {task.task_id}: item {item.item_id} references "
                f"control_prompt_id {item.control_prompt_id!r} which does not exist. "
                f"Available: {control_ids}"
            )

    # --- tests_item_ids references ---
    item_id_set = seen_item_ids
    for cp in task.control_prompts:
        for ref_id in cp.tests_item_ids:
            if ref_id not in item_id_set:
                raise ValueError(
                    f"Task {task.task_id}: control {cp.control_prompt_id} references "
                    f"tests_item_id {ref_id!r} which does not exist. "
                    f"Available: {item_id_set}"
                )
