"""Central configuration for the task generation harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TaskGenConfig:
    num_fork_tasks: int = 35
    num_guardian_tasks: int = 35
    max_iterations: int = 3
    creator_model: str = "anthropic/claude-opus-4.6"
    reviewer_model: str = "openai/gpt-5.4"
    scenario_model: str = "google/gemini-3.1-pro-preview"
    reasoning_effort: str = "xhigh"
    review_pass_threshold: float = 0.8
    dedup_threshold: float = 0.85
    rotate_models: bool = True
    output_dir: str = "mmce/tasks"
    progress_file: str = "taskgen/state/progress.json"
    dry_run: bool = False
    dry_run_dir: str = ""
    resume: bool = False

    # Model rotation: swap creator/reviewer every N tasks for diversity
    rotation_interval: int = 3

    def get_models_for_task(self, task_index: int) -> tuple[str, str]:
        """Return (creator_model, reviewer_model) with optional rotation."""
        if self.rotate_models and (task_index // self.rotation_interval) % 2 == 1:
            return self.reviewer_model, self.creator_model
        return self.creator_model, self.reviewer_model

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)

    @property
    def progress_path(self) -> Path:
        return Path(self.progress_file)
