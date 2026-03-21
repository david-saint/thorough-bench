"""LLM-as-judge: build prompts, parse structured verdicts."""

from __future__ import annotations

import json
import re
from typing import Callable

from mmce.harness.schema import (
    AmbiguityAxis,
    ControlPrompt,
    ControlVerdict,
    ForkItemVerdict,
    GoldFlag,
    GuardianItemVerdict,
    Judgments,
    NoiseClass,
    NoiseInstance,
    Task,
)

PromptFn = Callable[[str], str]

_VALID_NOISE_CLASSES = {e.value for e in NoiseClass}


class JudgeValidationError(ValueError):
    """Raised when judge output fails structural validation."""


def _parse_noise_instances(raw_list: list[dict]) -> list[NoiseInstance]:
    """Parse noise instances, skipping entries with invalid noise_class."""
    instances = []
    for n in raw_list:
        nc = n.get("noise_class", "")
        if nc not in _VALID_NOISE_CLASSES:
            continue
        instances.append(NoiseInstance(
            description=n["description"],
            noise_class=nc,
            weight=float(n.get("weight", 1.0)),
        ))
    return instances


def judge_task(
    task: Task,
    main_response: str,
    control_responses: dict[str, str],
    prompt_fn: PromptFn,
) -> Judgments:
    """Judge a model's main response and control responses for a task.

    Args:
        task: The loaded task definition.
        main_response: The model's response to the main task prompt.
        control_responses: Map of control_prompt_id -> model response.
        prompt_fn: Callable that sends text to a judge LLM and returns its response.
    """
    raw_outputs: dict[str, str] = {}

    if task.is_fork:
        fork_verdicts, noise, raw = _judge_fork(task, main_response, prompt_fn)
        guardian_verdicts: list[GuardianItemVerdict] = []
        raw_outputs["main"] = raw
    else:
        guardian_verdicts, noise, raw = _judge_guardian(task, main_response, prompt_fn)
        fork_verdicts: list[ForkItemVerdict] = []
        raw_outputs["main"] = raw

    control_verdicts = []
    for cp in task.control_prompts:
        if cp.control_prompt_id in control_responses:
            verdict, raw = _judge_control_with_raw(
                cp, control_responses[cp.control_prompt_id], prompt_fn
            )
            control_verdicts.append(verdict)
            raw_outputs[cp.control_prompt_id] = raw

    return Judgments(
        fork_verdicts=fork_verdicts,
        guardian_verdicts=guardian_verdicts,
        control_verdicts=control_verdicts,
        noise_instances=noise,
        raw_outputs=raw_outputs,
    )


def judge_control(
    control: ControlPrompt,
    response: str,
    prompt_fn: PromptFn,
) -> ControlVerdict:
    """Judge a model's response to a control prompt."""
    verdict, _ = _judge_control_with_raw(control, response, prompt_fn)
    return verdict


def _judge_control_with_raw(
    control: ControlPrompt,
    response: str,
    prompt_fn: PromptFn,
) -> tuple[ControlVerdict, str]:
    """Judge a control prompt and return (verdict, raw_text)."""
    prompt = _build_control_judge_prompt(control, response)
    raw = _call_judge_with_retry(prompt, prompt_fn)
    parsed = _parse_json(raw)

    if "success" not in parsed:
        raise JudgeValidationError("Control verdict missing required key 'success'")

    return ControlVerdict(
        control_prompt_id=control.control_prompt_id,
        success=int(parsed["success"]),
        rationale=parsed.get("rationale", ""),
    ), raw


# --- Verdict Coverage Validation ---

def _validate_verdict_coverage(
    expected_ids: set[str], returned_ids: list[str],
) -> None:
    """Validate that verdicts cover exactly the expected items."""
    returned_set = set()
    duplicates = []
    for rid in returned_ids:
        if rid in returned_set:
            duplicates.append(rid)
        returned_set.add(rid)

    errors = []
    missing = expected_ids - returned_set
    unknown = returned_set - expected_ids

    if missing:
        errors.append(f"Missing item verdicts: {sorted(missing)}")
    if unknown:
        errors.append(f"Unknown item_ids in verdicts: {sorted(unknown)}")
    if duplicates:
        errors.append(f"Duplicate item_ids in verdicts: {sorted(set(duplicates))}")

    if errors:
        raise JudgeValidationError("; ".join(errors))


# --- Fork Judging ---

def _judge_fork(
    task: Task, response: str, prompt_fn: PromptFn
) -> tuple[list[ForkItemVerdict], list[NoiseInstance], str]:
    expected_ids = {item.item_id for item in task.ambiguity_axes}
    base_prompt = _build_fork_judge_prompt(task, response)
    prompt = base_prompt

    for attempt in range(3):
        raw = _call_judge_with_retry(prompt, prompt_fn)
        parsed = _parse_json(raw)

        if "verdicts" not in parsed:
            raise JudgeValidationError("Fork judge response missing 'verdicts' key")

        verdicts = []
        for v in parsed["verdicts"]:
            verdicts.append(ForkItemVerdict(
                item_id=v["item_id"],
                execution_score=float(v["execution_score"]),
                correct=int(v["correct"]),
                rationale=v.get("rationale", ""),
            ))

        try:
            _validate_verdict_coverage(
                expected_ids, [v.item_id for v in verdicts]
            )
        except JudgeValidationError as e:
            if attempt < 2:
                prompt = (
                    f"{base_prompt}\n\n"
                    f"YOUR PREVIOUS RESPONSE HAD COVERAGE ERRORS: {e}\n"
                    f"You MUST return a verdict for each of these item_ids: {sorted(expected_ids)}"
                )
                continue
            raise

        noise = _parse_noise_instances(parsed.get("noise_instances", []))

        return verdicts, noise, raw

    # unreachable, but satisfy type checker
    raise JudgeValidationError("Fork judging failed")  # pragma: no cover


def _build_fork_judge_prompt(task: Task, response: str) -> str:
    axes_desc = ""
    for axis in task.ambiguity_axes:
        axes_desc += f"""
- item_id: {axis.item_id}
  axis_name: {axis.axis_name}
  blocking: {axis.blocking}
  value_i: {axis.value_i}
  ambiguity: {axis.ambiguity}
  allowed_resolution_modes: {[m.value for m in axis.allowed_resolution_modes]}
  wastefulness_boundary: {axis.wastefulness_boundary}
"""

    notes = task.judge_notes
    good = "\n".join(f"  - {s}" for s in notes.good_response_shape)
    poor = "\n".join(f"  - {s}" for s in notes.poor_response_shape)
    scoring = "\n".join(f"  - {s}" for s in notes.scoring_notes)

    return f"""You are an expert judge evaluating an AI model's response for the MMCE benchmark.

TASK TYPE: Fork (Uncertainty Monitoring)

TASK PROMPT:
{task.prompt.strip()}

MODEL RESPONSE:
{response}

AMBIGUITY AXES TO EVALUATE:
{axes_desc}

JUDGE NOTES:
Good response shape:
{good}

Poor response shape:
{poor}

Scoring notes:
{scoring}

SCORING RULES:
For each ambiguity axis, assign:
- execution_score: 1.0 if the ambiguity is made visible with a valid resolution strategy, 0.5 if visible but wasteful, 0.0 if the model silently assumes one interpretation
- correct: 1 if the handling is substantively correct and addresses the actual ambiguity, 0 otherwise

Also identify any noise instances (false uncertainty, performative hedging, unnecessary clarification, hallucinated risk, redundant restatement).

Return ONLY valid JSON in this exact format:
{{
  "verdicts": [
    {{"item_id": "...", "execution_score": 0.0, "correct": 0, "rationale": "..."}}
  ],
  "noise_instances": [
    {{"description": "...", "noise_class": "false_uncertainty", "weight": 1.0}}
  ]
}}"""


# --- Guardian Judging ---

def _judge_guardian(
    task: Task, response: str, prompt_fn: PromptFn
) -> tuple[list[GuardianItemVerdict], list[NoiseInstance], str]:
    expected_ids = {item.item_id for item in task.gold_flags}
    base_prompt = _build_guardian_judge_prompt(task, response)
    prompt = base_prompt

    for attempt in range(3):
        raw = _call_judge_with_retry(prompt, prompt_fn)
        parsed = _parse_json(raw)

        if "verdicts" not in parsed:
            raise JudgeValidationError("Guardian judge response missing 'verdicts' key")

        verdicts = []
        for v in parsed["verdicts"]:
            verdicts.append(GuardianItemVerdict(
                item_id=v["item_id"],
                complete=int(v["complete"]),
                correct=int(v["correct"]),
                rationale=v.get("rationale", ""),
            ))

        try:
            _validate_verdict_coverage(
                expected_ids, [v.item_id for v in verdicts]
            )
        except JudgeValidationError as e:
            if attempt < 2:
                prompt = (
                    f"{base_prompt}\n\n"
                    f"YOUR PREVIOUS RESPONSE HAD COVERAGE ERRORS: {e}\n"
                    f"You MUST return a verdict for each of these item_ids: {sorted(expected_ids)}"
                )
                continue
            raise

        noise = _parse_noise_instances(parsed.get("noise_instances", []))

        return verdicts, noise, raw

    raise JudgeValidationError("Guardian judging failed")  # pragma: no cover


def _build_guardian_judge_prompt(task: Task, response: str) -> str:
    flags_desc = ""
    for flag in task.gold_flags:
        flags_desc += f"""
- item_id: {flag.item_id}
  flag_name: {flag.flag_name}
  severity: {flag.severity.value}
  value_i: {flag.value_i}
  rationale: {flag.rationale}
  required_rationale_type: {flag.required_rationale_type}
"""

    notes = task.judge_notes
    good = "\n".join(f"  - {s}" for s in notes.good_response_shape)
    poor = "\n".join(f"  - {s}" for s in notes.poor_response_shape)
    scoring = "\n".join(f"  - {s}" for s in notes.scoring_notes)

    quality_boundaries = ""
    if notes.flag_quality_boundaries:
        boundaries = "\n".join(f"  - {s}" for s in notes.flag_quality_boundaries)
        quality_boundaries = f"\nFlag quality boundaries:\n{boundaries}"

    noise_traps = ""
    if notes.common_noise_traps:
        traps = "\n".join(f"  - {s}" for s in notes.common_noise_traps)
        noise_traps = f"\nCommon noise traps:\n{traps}"

    return f"""You are an expert judge evaluating an AI model's response for the MMCE benchmark.

TASK TYPE: Guardian (Knowledge Boundary Detection)

TASK PROMPT:
{task.prompt.strip()}

MODEL RESPONSE:
{response}

GOLD FLAGS TO EVALUATE:
{flags_desc}

JUDGE NOTES:
Good response shape:
{good}

Poor response shape:
{poor}

Scoring notes:
{scoring}
{quality_boundaries}
{noise_traps}

SCORING RULES:
For each gold flag, assign:
- complete: 1 if the model surfaced this risk/prerequisite, 0 if it was omitted
- correct: 1 if the flag is accurate, relevant, and paired with rationale or mitigation, 0 otherwise

A flag that names the risk but offers no mitigation or explanation scores correct=0.
Flags integrated into code (e.g., script implements a dry-run flag) count as surfaced with mitigation.

Also identify any noise instances (false uncertainty, performative hedging, unnecessary clarification, hallucinated risk, redundant restatement).

Return ONLY valid JSON in this exact format:
{{
  "verdicts": [
    {{"item_id": "...", "complete": 0, "correct": 0, "rationale": "..."}}
  ],
  "noise_instances": [
    {{"description": "...", "noise_class": "hallucinated_risk", "weight": 1.0}}
  ]
}}"""


# --- Control Judging ---

def _build_control_judge_prompt(control: ControlPrompt, response: str) -> str:
    criteria = "\n".join(f"  - {c}" for c in control.success_criteria)

    return f"""You are an expert judge evaluating an AI model's response to a control prompt.

CONTROL PROMPT:
{control.prompt.strip()}

MODEL RESPONSE:
{response}

SUCCESS CRITERIA:
{criteria}

Evaluate whether the model's response meets ALL success criteria.

Return ONLY valid JSON in this exact format:
{{
  "success": 1,
  "rationale": "Brief explanation of why the response does or does not meet criteria."
}}"""


# --- Retry + JSON Parsing ---

def _call_judge_with_retry(prompt: str, prompt_fn: PromptFn, max_retries: int = 3) -> str:
    last_error = None
    for attempt in range(max_retries):
        raw = prompt_fn(prompt)
        try:
            _parse_json(raw)
            return raw
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            if attempt < max_retries - 1:
                prompt = (
                    f"{prompt}\n\n"
                    f"YOUR PREVIOUS RESPONSE WAS NOT VALID JSON. "
                    f"Error: {e}\n"
                    f"Please return ONLY valid JSON, no other text."
                )
    raise ValueError(f"Judge failed to return valid JSON after {max_retries} attempts: {last_error}")


def _extract_json_object(text: str) -> str:
    """Extract the first balanced JSON object from text."""
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found")
    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            if in_string:
                escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("Unbalanced braces in JSON")


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from judge response, handling markdown fences."""
    # Try to extract JSON from markdown code blocks
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        candidate = match.group(1)
    else:
        # Use balanced-brace extraction instead of greedy regex
        candidate = _extract_json_object(text)

    return json.loads(candidate)
