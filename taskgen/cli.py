"""CLI entry point: generate, validate, coverage, scenarios."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from taskgen.config import TaskGenConfig


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate tasks using the create-review-iterate pipeline."""
    from taskgen.pipeline import run_pipeline

    config = TaskGenConfig(
        num_fork_tasks=args.count if args.dimension in ("fork", "both") else 0,
        num_guardian_tasks=args.count if args.dimension in ("guardian", "both") else 0,
        max_iterations=args.max_iterations,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        resume=args.resume,
    )
    if args.creator_model:
        config.creator_model = args.creator_model
    if args.reviewer_model:
        config.reviewer_model = args.reviewer_model
    if args.scenario_model:
        config.scenario_model = args.scenario_model

    dimensions = (
        ["fork", "guardian"] if args.dimension == "both"
        else [args.dimension]
    )

    progress = run_pipeline(config, dimensions)
    print(
        f"\nDone: {progress.fork_count} fork, {progress.guardian_count} guardian tasks",
        file=sys.stderr,
    )


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate all existing task YAMLs."""
    from mmce.harness.loader import load_all_tasks

    tasks_dir = Path(args.output_dir)
    if not tasks_dir.exists():
        print(f"Tasks directory not found: {tasks_dir}", file=sys.stderr)
        sys.exit(1)

    tasks = load_all_tasks(tasks_dir)
    print(f"Validated {len(tasks)} tasks successfully")

    # Run additional quality checks
    from taskgen.validation.schema_gate import validate_task

    errors = 0
    for task in tasks:
        raw = task.model_dump(mode="json")
        try:
            _, warnings = validate_task(raw)
            for w in warnings:
                print(f"  Warning [{task.task_id}]: {w}")
        except Exception as e:
            print(f"  ERROR [{task.task_id}]: {e}", file=sys.stderr)
            errors += 1

    if errors:
        print(f"\n{errors} task(s) failed quality checks", file=sys.stderr)
        sys.exit(1)
    else:
        print("All tasks pass quality checks")


def cmd_coverage(args: argparse.Namespace) -> None:
    """Show current coverage statistics."""
    from mmce.harness.loader import load_all_tasks

    from taskgen.validation.coverage import build_coverage_from_tasks

    tasks_dir = Path(args.output_dir)
    if not tasks_dir.exists():
        print(f"Tasks directory not found: {tasks_dir}", file=sys.stderr)
        sys.exit(1)

    tasks = load_all_tasks(tasks_dir)
    coverage = build_coverage_from_tasks(tasks)
    print(coverage.summary())


def cmd_scenarios(args: argparse.Namespace) -> None:
    """Preview scenario briefs (requires OPENROUTER_API_KEY)."""
    from taskgen.llm.client import TaskGenLLMClient
    from taskgen.scenarios.generator import generate_scenarios

    client = TaskGenLLMClient(
        model=args.scenario_model or "google/gemini-3.1-pro-preview",
    )

    scenarios = generate_scenarios(
        client,
        dimension=args.dimension,
        count=args.count,
        prior_summaries=[],
        priority_categories=[],
        model_override=args.scenario_model,
    )

    for i, s in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i} ---")
        print(f"  Domain: {s.domain}")
        print(f"  Action: {s.action}")
        print(f"  Time pressure: {s.time_pressure}")
        print(f"  Constraint: {s.constraint}")
        print(f"  Target categories: {', '.join(s.target_categories)}")
        print(f"  Summary: {s.summary}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="taskgen",
        description="MMCE task generation harness",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- generate ---
    gen = subparsers.add_parser("generate", help="Generate tasks")
    gen.add_argument(
        "--dimension", choices=["fork", "guardian", "both"], default="both",
        help="Which dimension(s) to generate",
    )
    gen.add_argument(
        "--count", type=int, default=35,
        help="Number of tasks per dimension",
    )
    gen.add_argument(
        "--max-iterations", type=int, default=3,
        help="Max create-review-iterate depth",
    )
    gen.add_argument("--creator-model", help="Override creator model")
    gen.add_argument("--reviewer-model", help="Override reviewer model")
    gen.add_argument("--scenario-model", help="Override scenario model")
    gen.add_argument(
        "--output-dir", default="mmce/tasks",
        help="Output directory for task YAMLs",
    )
    gen.add_argument(
        "--dry-run", action="store_true",
        help="Validate and review but don't write files",
    )
    gen.add_argument(
        "--resume", action="store_true",
        help="Resume from previous progress state",
    )
    gen.set_defaults(func=cmd_generate)

    # --- validate ---
    val = subparsers.add_parser("validate", help="Validate all task YAMLs")
    val.add_argument(
        "--output-dir", default="mmce/tasks",
        help="Tasks directory to validate",
    )
    val.set_defaults(func=cmd_validate)

    # --- coverage ---
    cov = subparsers.add_parser("coverage", help="Show coverage statistics")
    cov.add_argument(
        "--output-dir", default="mmce/tasks",
        help="Tasks directory to analyze",
    )
    cov.set_defaults(func=cmd_coverage)

    # --- scenarios ---
    scn = subparsers.add_parser("scenarios", help="Preview scenario briefs")
    scn.add_argument(
        "--dimension", choices=["fork", "guardian"], required=True,
        help="Dimension for scenarios",
    )
    scn.add_argument(
        "--count", type=int, default=5,
        help="Number of scenarios to generate",
    )
    scn.add_argument("--scenario-model", help="Override scenario model")
    scn.set_defaults(func=cmd_scenarios)

    args = parser.parse_args()
    args.func(args)
