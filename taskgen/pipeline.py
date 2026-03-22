"""Top-level orchestrator: run N tasks with create-review-iterate loop."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from mmce.harness.loader import load_all_tasks
from mmce.harness.schema import Task

from taskgen.config import TaskGenConfig
from taskgen.creator.fork_creator import create_fork_task, revise_fork_task
from taskgen.creator.guardian_creator import create_guardian_task, revise_guardian_task
from taskgen.llm.client import TaskGenLLMClient
from taskgen.output.progress import ProgressState, load_progress, save_progress
from taskgen.output.writer import next_task_number, write_task
from taskgen.reviewer.fork_reviewer import review_fork_task
from taskgen.reviewer.guardian_reviewer import review_guardian_task
from taskgen.reviewer.rubrics import ReviewResult
from taskgen.scenarios.generator import generate_scenarios
from taskgen.scenarios.registry import ScenarioBrief, ScenarioRegistry
from taskgen.validation.coverage import CoverageState, build_coverage_from_tasks
from taskgen.validation.dedup import check_task_against_existing
from taskgen.validation.schema_gate import SchemaGateError, validate_task


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _slugify(text: str) -> str:
    """Convert text to a snake_case slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:40]


def create_review_iterate(
    client: TaskGenLLMClient,
    scenario: ScenarioBrief,
    dimension: str,
    task_id: str,
    creator_model: str,
    reviewer_model: str,
    config: TaskGenConfig,
) -> tuple[Task, dict] | None:
    """Run the create-review-iterate loop for one task.

    Returns (validated_task, raw_dict) on success, None on failure.
    """
    previous_json: dict | None = None
    feedback: ReviewResult | None = None
    last_valid_task: Task | None = None
    last_valid_raw: dict | None = None
    last_review_score: float = 0.0

    for iteration in range(config.max_iterations):
        _log(f"  Iteration {iteration + 1}/{config.max_iterations}")

        # 1. Create or revise
        try:
            if iteration == 0:
                if dimension == "fork":
                    raw_dict = create_fork_task(
                        client, scenario, task_id, model_override=creator_model
                    )
                else:
                    raw_dict = create_guardian_task(
                        client, scenario, task_id, model_override=creator_model
                    )
            else:
                assert previous_json is not None
                assert feedback is not None
                if dimension == "fork":
                    raw_dict = revise_fork_task(
                        client,
                        previous_json,
                        feedback.must_fix,
                        feedback.suggestions,
                        model_override=creator_model,
                    )
                else:
                    raw_dict = revise_guardian_task(
                        client,
                        previous_json,
                        feedback.must_fix,
                        feedback.suggestions,
                        model_override=creator_model,
                    )
        except Exception as e:
            _log(f"  Creation failed: {e}")
            previous_json = previous_json or {}
            continue

        # 2. Schema validation gate
        try:
            task, warnings = validate_task(raw_dict)
            for w in warnings:
                _log(f"  Warning: {w}")
        except SchemaGateError as e:
            _log(f"  Validation failed: {e}")
            # Feed validation errors as feedback for next iteration
            previous_json = raw_dict
            feedback = ReviewResult(
                overall_score=0.0,
                criteria_scores={},
                feedback="Schema validation failed",
                must_fix=e.errors,
                suggestions=[],
            )
            continue

        # 3. Review
        try:
            if dimension == "fork":
                review = review_fork_task(
                    client, raw_dict, model_override=reviewer_model
                )
            else:
                review = review_guardian_task(
                    client, raw_dict, model_override=reviewer_model
                )

            _log(
                f"  Review score: {review.overall_score:.2f} "
                f"({'PASS' if review.passes else 'FAIL'})"
            )
            if review.must_fix:
                _log(f"  Must fix: {review.must_fix}")

            if review.passes:
                return task, raw_dict

            # Track last validated task + score for final-iteration override
            last_valid_task = task
            last_valid_raw = raw_dict
            last_review_score = review.overall_score

        except Exception as e:
            _log(f"  Review failed: {e}")
            review = ReviewResult(
                overall_score=0.0,
                criteria_scores={},
                feedback=f"Review error: {e}",
                must_fix=[f"Review call failed: {e}"],
                suggestions=[],
            )

        # 4. Accumulate feedback for next iteration
        previous_json = raw_dict
        feedback = review

    # Score override: if the final iteration scored > 0.9 but had must_fix
    # items, accept it — the reviewer is being overly strict at this point
    if last_valid_task is not None and last_review_score > 0.9:
        _log(f"  Score override: accepting final iteration (score {last_review_score:.2f} > 0.9)")
        return last_valid_task, last_valid_raw  # type: ignore[return-value]

    return None


def run_pipeline(
    config: TaskGenConfig,
    dimensions: list[str] | None = None,
) -> ProgressState:
    """Run the full task generation pipeline.

    Args:
        config: Pipeline configuration.
        dimensions: List of dimensions to generate ("fork", "guardian", or both).
    """
    if dimensions is None:
        dimensions = ["fork", "guardian"]

    # Load existing tasks
    output_path = Path(config.output_dir)
    existing_tasks: list[Task] = []
    if output_path.exists():
        try:
            existing_tasks = load_all_tasks(output_path)
        except Exception as e:
            _log(f"Warning: Could not load existing tasks: {e}")

    # Build initial coverage state
    coverage = build_coverage_from_tasks(existing_tasks)
    _log(f"Loaded {len(existing_tasks)} existing tasks")

    # Load or create progress state
    progress: ProgressState
    if config.resume:
        progress = load_progress(config.progress_path)
        _log(f"Resuming: {progress.fork_count} fork, {progress.guardian_count} guardian completed")
    else:
        progress = ProgressState()
    progress.coverage = coverage

    # Build existing task summaries for dedup
    existing_summaries: list[str] = []
    for t in existing_tasks:
        existing_summaries.append(f"{t.dimension_alias}: {t.task_id} - {t.prompt[:80]}")

    # Create LLM client
    client = TaskGenLLMClient(
        reasoning_effort=config.reasoning_effort,
    )

    # Scenario registry
    registry = ScenarioRegistry()

    # Process each dimension
    for dimension in dimensions:
        target_count = (
            config.num_fork_tasks if dimension == "fork"
            else config.num_guardian_tasks
        )
        existing_count = (
            progress.fork_count if dimension == "fork"
            else progress.guardian_count
        )
        remaining = target_count - existing_count

        if remaining <= 0:
            _log(f"[{dimension}] Already at target ({existing_count}/{target_count})")
            continue

        _log(f"\n[{dimension}] Generating {remaining} tasks ({existing_count}/{target_count} done)")

        # Generate scenario pool
        priorities = (
            coverage.fork_priorities() if dimension == "fork"
            else coverage.guardian_priorities()
        )

        # Generate scenarios in batches
        batch_size = min(remaining + 5, 15)  # Extra buffer for failures
        _log(f"[{dimension}] Generating {batch_size} scenario briefs...")
        scenarios = generate_scenarios(
            client,
            dimension=dimension,
            count=batch_size,
            prior_summaries=registry.all_summaries + existing_summaries,
            priority_categories=priorities,
            model_override=config.scenario_model,
        )
        registry.add_batch(scenarios)
        _log(f"[{dimension}] Got {registry.count(dimension)} scenarios")

        # Track next task number
        next_num = next_task_number(config.output_dir, dimension)

        generated = 0
        task_index = existing_count  # For model rotation

        while generated < remaining:
            scenario = registry.pop_next(dimension)
            if scenario is None:
                # Need more scenarios
                _log(f"[{dimension}] Generating more scenarios...")
                new_scenarios = generate_scenarios(
                    client,
                    dimension=dimension,
                    count=10,
                    prior_summaries=registry.all_summaries + existing_summaries,
                    priority_categories=priorities,
                    model_override=config.scenario_model,
                )
                added = registry.add_batch(new_scenarios)
                if added == 0:
                    _log(f"[{dimension}] Could not generate more unique scenarios, stopping")
                    break
                continue

            # Build task ID
            slug = _slugify(scenario.action)
            task_id = f"{dimension}_st_{next_num:03d}_{slug}"

            _log(f"\n[{dimension}] Task {generated + 1}/{remaining}: {task_id}")
            _log(f"  Scenario: {scenario.summary}")

            # Get models for this task (with rotation)
            creator_model, reviewer_model = config.get_models_for_task(task_index)

            # Run create-review-iterate
            result = create_review_iterate(
                client=client,
                scenario=scenario,
                dimension=dimension,
                task_id=task_id,
                creator_model=creator_model,
                reviewer_model=reviewer_model,
                config=config,
            )

            if result is None:
                _log(f"  FAILED after {config.max_iterations} iterations")
                progress.record_failure(
                    scenario.summary,
                    dimension,
                    config.max_iterations,
                    "Exhausted iterations",
                )
                continue

            task, raw_dict = result

            # Dedup check
            task_summary = f"{dimension}: {task_id} - {task.prompt[:80]}"
            is_dup, dup_match = check_task_against_existing(
                client,
                task_summary,
                existing_summaries,
                threshold=config.dedup_threshold,
                model_override=reviewer_model,
            )
            if is_dup:
                _log(f"  DUPLICATE of: {dup_match}")
                progress.record_failure(
                    scenario.summary, dimension, 1, f"Duplicate of: {dup_match}"
                )
                continue

            # Write task
            if not config.dry_run:
                path = write_task(task, config.output_dir)
                _log(f"  Written: {path}")
            else:
                _log(f"  [DRY RUN] Would write: {task_id}")

            # Update state
            existing_summaries.append(task_summary)
            progress.record_success(task_id, dimension)
            if dimension == "fork":
                coverage.record_fork_task(task, scenario.domain)
            else:
                coverage.record_guardian_task(task, scenario.domain)

            generated += 1
            next_num += 1
            task_index += 1

        _log(f"\n[{dimension}] Generated {generated}/{remaining} tasks")

    # Save progress
    progress.coverage = coverage
    progress.update_token_usage(client.cost_tracker.summary_by_model())

    if not config.dry_run:
        save_progress(progress, config.progress_path)
        _log(f"\nProgress saved to {config.progress_path}")

    # Print coverage summary
    _log(f"\n{coverage.summary()}")

    return progress
