"""Registry-driven @kbench.task generation from YAML task definitions.

Each YAML task becomes a scored task function, and each control prompt
becomes a separate boolean task for capability baselining.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from mmce.harness.judge import judge_control, judge_task
from mmce.harness.loader import load_all_tasks, load_task
from mmce.harness.scorer import score_task

TASKS_DIR = Path(__file__).parent.parent / "tasks"

try:
    import kaggle_benchmarks as kbench
    SDK_AVAILABLE = True
except (ImportError, RuntimeError):
    kbench = None  # type: ignore[assignment]
    SDK_AVAILABLE = False


# --- Framework-agnostic entry points ---

def run_mmce_task(
    task_path: str | Path,
    llm_prompt_fn: Callable[[str], str],
    judge_prompt_fn: Callable[[str], str],
    new_chat_fn: Callable | None = None,
) -> float:
    """Run the full MMCE pipeline for a single task.

    Args:
        task_path: Path to the task YAML file.
        llm_prompt_fn: Sends a prompt to the model under test, returns response.
        judge_prompt_fn: Sends a prompt to the judge LLM, returns response.
        new_chat_fn: Optional callable to create a new chat context for controls.
            Signature: new_chat_fn(chat_id) -> context manager.
            If None, controls are run in the same context.

    Returns:
        The conditional thoroughness score (or absolute coverage if CT is N/A).
    """
    task_def = load_task(task_path)

    # 1. Get main response
    main_response = llm_prompt_fn(task_def.prompt)

    # 2. Get control responses (each in its own chat context)
    control_responses = {}
    for cp in task_def.control_prompts:
        if new_chat_fn is not None:
            with new_chat_fn(cp.control_prompt_id):
                control_responses[cp.control_prompt_id] = llm_prompt_fn(cp.prompt)
        else:
            control_responses[cp.control_prompt_id] = llm_prompt_fn(cp.prompt)

    # 3. Judge everything
    judgments = judge_task(task_def, main_response, control_responses, judge_prompt_fn)

    # 4. Score
    result = score_task(task_def, judgments)

    # Return CT if available, otherwise AC
    if result.conditional_thoroughness is not None:
        return result.conditional_thoroughness
    return result.absolute_coverage


def run_control_task(
    task_path: str | Path,
    control_prompt_id: str,
    llm_prompt_fn: Callable[[str], str],
    judge_prompt_fn: Callable[[str], str],
) -> bool:
    """Run a single control prompt as a standalone task.

    Returns True if the model succeeds on the control.
    """
    task_def = load_task(task_path)
    cp = task_def.get_control(control_prompt_id)

    response = llm_prompt_fn(cp.prompt)
    verdict = judge_control(cp, response, judge_prompt_fn)

    return verdict.success == 1


# --- Dynamic SDK task generation ---

def _make_mmce_task(task_def):
    """Generate a @kbench.task for a scored MMCE task."""
    def task_fn(llm) -> float:
        main_response = llm.prompt(task_def.prompt)
        control_responses = {}
        for cp in task_def.control_prompts:
            with kbench.chats.new(cp.control_prompt_id):
                control_responses[cp.control_prompt_id] = llm.prompt(cp.prompt)
        judgments = judge_task(
            task_def, main_response, control_responses,
            lambda text: kbench.judge_llm.prompt(text),
        )
        result = score_task(task_def, judgments)
        if result.conditional_thoroughness is not None:
            return result.conditional_thoroughness
        return result.absolute_coverage

    task_fn.__name__ = task_def.task_id
    task_fn.__doc__ = f"MMCE: {task_def.task_id}"

    if SDK_AVAILABLE:
        return kbench.task(name=task_def.task_id, version=1)(task_fn)
    return task_fn


def _make_control_task(task_def, cp):
    """Generate a @kbench.task for a control prompt."""
    def control_fn(llm) -> bool:
        response = llm.prompt(cp.prompt)
        verdict = judge_control(
            cp, response,
            lambda text: kbench.judge_llm.prompt(text),
        )
        return verdict.success == 1

    control_fn.__name__ = cp.control_prompt_id
    control_fn.__doc__ = f"MMCE control: {cp.control_prompt_id}"

    if SDK_AVAILABLE:
        return kbench.task(name=cp.control_prompt_id, version=1)(control_fn)
    return control_fn


# --- Module-level registration ---

TASK_REGISTRY: dict[str, Callable] = {}
CONTROL_REGISTRY: dict[str, Callable] = {}

_ns = globals()
for _td in load_all_tasks(TASKS_DIR):
    _fn = _make_mmce_task(_td)
    TASK_REGISTRY[_td.task_id] = _fn
    _ns[_td.task_id] = _fn
    for _cp in _td.control_prompts:
        _cfn = _make_control_task(_td, _cp)
        CONTROL_REGISTRY[_cp.control_prompt_id] = _cfn
        _ns[_cp.control_prompt_id] = _cfn
del _ns
