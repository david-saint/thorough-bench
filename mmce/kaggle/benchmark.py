"""Kaggle Benchmarks SDK assembly.

Groups all MMCE tasks into a benchmark with metadata for the Kaggle platform.
When running locally without the SDK, provides a mock runner.
"""

from __future__ import annotations

from pathlib import Path

from mmce.harness.loader import load_all_tasks
from mmce.harness.judge import judge_task, judge_control
from mmce.harness.scorer import score_task, compute_composite
from mmce.harness.schema import TaskResult
from mmce.harness.results import (
    RunMeta,
    create_run_dir,
    save_task_result,
    save_run_meta,
    save_summary_csv,
)

# Trigger SDK task registration on import
import mmce.kaggle.tasks  # noqa: F401

TASKS_DIR = Path(__file__).parent.parent / "tasks"
RESULTS_DIR = Path(__file__).parent.parent / "results"


# --- Benchmark metadata ---

BENCHMARK_META = {
    "name": "mmce",
    "title": "Metacognitive Monitoring and Control Evaluation",
    "description": (
        "Measures whether AI models detect ambiguity, surface hidden risks, "
        "and verify their own work — conditional on demonstrated capability."
    ),
    "track": "metacognition",
    "version": 1,
    "constructs": ["uncertainty_monitoring", "knowledge_boundary_detection"],
    "composite_weights": {
        "uncertainty_monitoring": 0.50,
        "knowledge_boundary_detection": 0.50,
    },
}


def run_benchmark_locally(
    prompt_fn,
    judge_fn,
    tasks_dir: str | Path | None = None,
    model_name: str = "unknown",
    judge_model: str = "",
    save_results: bool = True,
) -> list[TaskResult]:
    """Run the full MMCE benchmark locally (without Kaggle SDK).

    Args:
        prompt_fn: Callable that sends text to the model under test.
        judge_fn: Callable that sends text to the judge LLM.
        tasks_dir: Path to task YAML directory. Defaults to mmce/tasks/.
        model_name: Name of the model under test (for result persistence).
        save_results: Whether to save results to disk.

    Returns:
        List of TaskResult for each task.
    """
    tasks_dir = Path(tasks_dir) if tasks_dir else TASKS_DIR
    tasks = load_all_tasks(tasks_dir)
    results = []

    for task_def in tasks:
        print(f"Running task: {task_def.task_id}")

        # Get main response
        main_response = prompt_fn(task_def.prompt)

        # Get control responses
        control_responses = {}
        for cp in task_def.control_prompts:
            print(f"  Control: {cp.control_prompt_id}")
            control_responses[cp.control_prompt_id] = prompt_fn(cp.prompt)

        # Judge
        judgments = judge_task(task_def, main_response, control_responses, judge_fn)

        # Score
        result = score_task(task_def, judgments)
        results.append(result)

        ct_str = f"{result.conditional_thoroughness:.3f}" if result.conditional_thoroughness is not None else "N/A"
        print(f"  AC={result.absolute_coverage:.3f} CT={ct_str} NI={result.noise_index:.3f}")

    # Compute composite
    composite = compute_composite(results)
    _print_composite(composite)

    # Persist results
    if save_results:
        run_dir = create_run_dir(RESULTS_DIR, model_name)
        for result in results:
            save_task_result(run_dir, result)

        meta = RunMeta(
            run_id=run_dir.name,
            timestamp=run_dir.name.split("_")[0],
            model_under_test=model_name,
            judge_model=judge_model,
            tasks_evaluated=[r.task_id for r in results],
            composite_ct=composite["composite_ct"],
            composite_ac=composite["composite_ac"],
        )
        save_run_meta(run_dir, meta)
        save_summary_csv(run_dir, results, tasks)
        print(f"\nResults saved to: {run_dir}")

    return results


def _print_composite(composite: dict) -> None:
    """Print the MMCE composite score from compute_composite output."""
    ct = composite.get("composite_ct")
    ac = composite.get("composite_ac")

    if ct is not None:
        print(f"\nComposite CT: {ct:.3f}")
    if ac is not None:
        print(f"Composite AC: {ac:.3f}")

    per_construct = composite.get("per_construct", {})
    for construct, vals in per_construct.items():
        ct_str = f"{vals['ct']:.3f}" if vals["ct"] is not None else "N/A"
        print(f"  {construct}: CT={ct_str} AC={vals['ac']:.3f} (n={vals['n']})")


# --- SDK integration helpers ---

def get_task_registry() -> dict[str, dict]:
    """Return a registry of all tasks for SDK wiring.

    Returns a dict of task_id -> {path, task_type, controls: [...]}
    Used by notebook or SDK wrappers to generate @kbench.task functions.
    """
    tasks = load_all_tasks(TASKS_DIR)
    registry = {}

    for task_def in tasks:
        controls = []
        for cp in task_def.control_prompts:
            controls.append({
                "control_prompt_id": cp.control_prompt_id,
                "name": cp.control_prompt_id,
            })

        registry[task_def.task_id] = {
            "path": str(TASKS_DIR / task_def.dimension_alias / f"{task_def.task_id}.yaml"),
            "task_type": task_def.dimension_alias,
            "constructs": task_def.constructs_present,
            "controls": controls,
        }

    return registry
