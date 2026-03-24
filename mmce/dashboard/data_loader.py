"""Load all benchmark runs from mmce/results/ into normalized DataFrames."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from mmce.harness.loader import load_all_tasks
from mmce.harness.schema import (
    AmbiguityAxis,
    GoldFlag,
    Task,
    TaskResult,
)

RESULTS_DIR = Path(__file__).parent.parent / "results"
TASKS_DIR = Path(__file__).parent.parent / "tasks"


@dataclass
class DashboardData:
    """Container for all normalized DataFrames."""

    runs_df: pd.DataFrame
    tasks_df: pd.DataFrame
    items_df: pd.DataFrame
    noise_df: pd.DataFrame
    controls_df: pd.DataFrame
    task_defs: dict[str, Task] = field(default_factory=dict)

    def filter_runs(self, run_ids: list[str]) -> "DashboardData":
        """Return a filtered copy including only the specified run_ids."""
        return DashboardData(
            runs_df=self.runs_df[self.runs_df["run_id"].isin(run_ids)].copy(),
            tasks_df=self.tasks_df[self.tasks_df["run_id"].isin(run_ids)].copy(),
            items_df=self.items_df[self.items_df["run_id"].isin(run_ids)].copy(),
            noise_df=self.noise_df[self.noise_df["run_id"].isin(run_ids)].copy(),
            controls_df=self.controls_df[self.controls_df["run_id"].isin(run_ids)].copy(),
            task_defs=self.task_defs,
        )


def _short_model_name(full_name: str) -> str:
    """Extract short model name: 'openai/gpt-5.4-nano' -> 'gpt-5.4-nano'."""
    return full_name.split("/", 1)[-1] if "/" in full_name else full_name


def load_all_runs(
    results_dir: Path = RESULTS_DIR,
    tasks_dir: Path = TASKS_DIR,
) -> DashboardData:
    """Scan results directory and build normalized DataFrames."""
    # Load task definitions for metadata (value_i, severity, blocking)
    task_defs: dict[str, Task] = {}
    if tasks_dir.exists():
        for task in load_all_tasks(tasks_dir):
            task_defs[task.task_id] = task

    # Build item metadata lookup: item_id -> {value_i, severity, blocking}
    item_meta: dict[str, dict] = {}
    for task in task_defs.values():
        for item in task.gold_atomic_items:
            meta: dict = {"value_i": item.value_i}
            if isinstance(item, AmbiguityAxis):
                meta["blocking"] = item.blocking
                meta["severity"] = None
            elif isinstance(item, GoldFlag):
                meta["blocking"] = None
                meta["severity"] = item.severity.value
            item_meta[item.item_id] = meta

    runs_rows: list[dict] = []
    tasks_rows: list[dict] = []
    items_rows: list[dict] = []
    noise_rows: list[dict] = []
    controls_rows: list[dict] = []

    for meta_path in sorted(results_dir.glob("*/run_meta.json")):
        run_dir = meta_path.parent
        meta = json.loads(meta_path.read_text())

        run_id = meta["run_id"]
        model_full = meta["model_under_test"]
        model = _short_model_name(model_full)

        runs_rows.append({
            "run_id": run_id,
            "model": model,
            "model_full": model_full,
            "judge": meta.get("judge_model", ""),
            "timestamp": meta["timestamp"],
            "n_tasks": len(meta.get("tasks_evaluated", [])),
            "composite_ct": meta.get("composite_ct"),
            "composite_ac": meta.get("composite_ac"),
            "prompt_variant": meta.get("prompt_variant", ""),
        })

        # Parse each task result
        for result_path in sorted(run_dir.glob("*_result.json")):
            raw = json.loads(result_path.read_text())
            result = TaskResult.model_validate(raw)

            tasks_rows.append({
                "run_id": run_id,
                "model": model,
                "task_id": result.task_id,
                "dimension": result.dimension_alias,
                "ac": result.absolute_coverage,
                "ct": result.conditional_thoroughness,
                "ni": result.noise_index,
                "refusal": getattr(result, "refusal", False),
            })

            # Fork verdicts
            for v in result.judgments.fork_verdicts:
                im = item_meta.get(v.item_id, {})
                value_i = im.get("value_i", 1.0)
                credit = value_i * v.execution_score * v.correct
                items_rows.append({
                    "run_id": run_id,
                    "model": model,
                    "task_id": result.task_id,
                    "item_id": v.item_id,
                    "dimension": "fork",
                    "execution_score": v.execution_score,
                    "complete": None,
                    "correct": v.correct,
                    "credit": credit,
                    "value_i": value_i,
                    "capable": result.capability_map.get(v.item_id, 0),
                    "volunteered": 1 if credit > 0 else 0,
                    "rationale": v.rationale,
                    "severity": None,
                    "blocking": im.get("blocking"),
                })

            # Guardian verdicts
            for v in result.judgments.guardian_verdicts:
                im = item_meta.get(v.item_id, {})
                value_i = im.get("value_i", 1.0)
                credit = value_i * v.complete * v.correct
                items_rows.append({
                    "run_id": run_id,
                    "model": model,
                    "task_id": result.task_id,
                    "item_id": v.item_id,
                    "dimension": "guardian",
                    "execution_score": None,
                    "complete": v.complete,
                    "correct": v.correct,
                    "credit": credit,
                    "value_i": value_i,
                    "capable": result.capability_map.get(v.item_id, 0),
                    "volunteered": 1 if credit > 0 else 0,
                    "rationale": v.rationale,
                    "severity": im.get("severity"),
                    "blocking": None,
                })

            # Noise instances
            for n in result.judgments.noise_instances:
                noise_rows.append({
                    "run_id": run_id,
                    "model": model,
                    "task_id": result.task_id,
                    "description": n.description,
                    "noise_class": n.noise_class.value,
                    "weight": n.weight,
                })

            # Control verdicts
            for c in result.judgments.control_verdicts:
                controls_rows.append({
                    "run_id": run_id,
                    "model": model,
                    "task_id": result.task_id,
                    "control_prompt_id": c.control_prompt_id,
                    "success": c.success,
                    "rationale": c.rationale,
                })

    return DashboardData(
        runs_df=pd.DataFrame(runs_rows) if runs_rows else pd.DataFrame(),
        tasks_df=pd.DataFrame(tasks_rows) if tasks_rows else pd.DataFrame(),
        items_df=pd.DataFrame(items_rows) if items_rows else pd.DataFrame(),
        noise_df=pd.DataFrame(noise_rows) if noise_rows else pd.DataFrame(),
        controls_df=pd.DataFrame(controls_rows) if controls_rows else pd.DataFrame(),
        task_defs=task_defs,
    )


def get_latest_per_model(runs_df: pd.DataFrame) -> list[str]:
    """Return run_ids for the most recent run of each unique model."""
    if runs_df.empty:
        return []
    latest = runs_df.sort_values("timestamp").groupby("model").last().reset_index()
    return latest["run_id"].tolist()
