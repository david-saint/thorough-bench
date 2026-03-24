"""Result persistence: save task results, run metadata, and summary CSV."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from mmce.harness.schema import Task, TaskResult


class RunMeta(BaseModel):
    """Metadata for a single benchmark run."""
    run_id: str
    timestamp: str
    model_under_test: str
    judge_model: str = ""
    tasks_evaluated: list[str] = Field(default_factory=list)
    composite_ct: float | None = None
    composite_ac: float | None = None
    prompt_variant: str = ""


def create_run_dir(base_dir: str | Path, model_name: str) -> Path:
    """Create a timestamped run directory and return its path."""
    base_dir = Path(base_dir)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    safe_model = model_name.replace("/", "_").replace(" ", "_")
    run_dir = base_dir / f"{ts}_{safe_model}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_task_result(run_dir: str | Path, result: TaskResult) -> Path:
    """Write a TaskResult as JSON. Returns the written path."""
    run_dir = Path(run_dir)
    path = run_dir / f"{result.task_id}_result.json"
    path.write_text(result.model_dump_json(indent=2))
    return path


def save_run_meta(run_dir: str | Path, meta: RunMeta) -> Path:
    """Write RunMeta as JSON. Returns the written path."""
    run_dir = Path(run_dir)
    path = run_dir / "run_meta.json"
    path.write_text(meta.model_dump_json(indent=2))
    return path


def save_summary_csv(
    run_dir: str | Path,
    results: list[TaskResult],
    tasks: list[Task],
) -> Path:
    """Write a flattened summary CSV with per-item and per-control outcomes."""
    run_dir = Path(run_dir)
    task_map = {t.task_id: t for t in tasks}

    # Collect all item_ids and control_ids across tasks
    all_item_ids: list[str] = []
    all_control_ids: list[str] = []
    for t in tasks:
        for item in t.gold_atomic_items:
            if item.item_id not in all_item_ids:
                all_item_ids.append(item.item_id)
        for cp in t.control_prompts:
            if cp.control_prompt_id not in all_control_ids:
                all_control_ids.append(cp.control_prompt_id)

    fieldnames = [
        "task_id", "dimension_alias", "ac", "ct", "ni",
        *[f"{iid}_credit" for iid in all_item_ids],
        *[f"{cid}_success" for cid in all_control_ids],
    ]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()

    for result in results:
        task_def = task_map.get(result.task_id)
        row: dict[str, str | float] = {
            "task_id": result.task_id,
            "dimension_alias": result.dimension_alias,
            "ac": result.absolute_coverage,
            "ct": result.conditional_thoroughness if result.conditional_thoroughness is not None else "",
            "ni": result.noise_index,
        }

        # Item credits
        fork_map = {v.item_id: v for v in result.judgments.fork_verdicts}
        guardian_map = {v.item_id: v for v in result.judgments.guardian_verdicts}

        for iid in all_item_ids:
            if iid in fork_map:
                v = fork_map[iid]
                item = _find_item(task_def, iid) if task_def else None
                value_i = item.value_i if item else 1.0
                row[f"{iid}_credit"] = value_i * v.execution_score * v.correct
            elif iid in guardian_map:
                v = guardian_map[iid]
                item = _find_item(task_def, iid) if task_def else None
                value_i = item.value_i if item else 1.0
                row[f"{iid}_credit"] = value_i * v.complete * v.correct
            else:
                row[f"{iid}_credit"] = ""

        # Control successes
        ctrl_map = {v.control_prompt_id: v for v in result.judgments.control_verdicts}
        for cid in all_control_ids:
            if cid in ctrl_map:
                row[f"{cid}_success"] = ctrl_map[cid].success
            else:
                row[f"{cid}_success"] = ""

        writer.writerow(row)

    path = run_dir / "summary.csv"
    path.write_text(buf.getvalue())
    return path


def _find_item(task_def: Task | None, item_id: str):
    """Find an atomic item by id in a task."""
    if task_def is None:
        return None
    for item in task_def.gold_atomic_items:
        if item.item_id == item_id:
            return item
    return None
