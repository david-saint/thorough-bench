"""Persistent state: completed tasks, failures, coverage, cost tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from taskgen.validation.coverage import CoverageState


@dataclass
class FailedScenario:
    scenario_summary: str
    dimension: str
    iterations: int
    final_error: str


@dataclass
class ProgressState:
    fork_task_ids: list[str] = field(default_factory=list)
    guardian_task_ids: list[str] = field(default_factory=list)
    failed_scenarios: list[FailedScenario] = field(default_factory=list)
    coverage: CoverageState = field(default_factory=CoverageState)
    token_usage: dict[str, dict[str, int]] = field(default_factory=dict)
    last_updated: str = ""

    @property
    def fork_count(self) -> int:
        return len(self.fork_task_ids)

    @property
    def guardian_count(self) -> int:
        return len(self.guardian_task_ids)

    def record_success(self, task_id: str, dimension: str) -> None:
        if dimension == "fork":
            self.fork_task_ids.append(task_id)
        else:
            self.guardian_task_ids.append(task_id)
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def record_failure(
        self, summary: str, dimension: str, iterations: int, error: str
    ) -> None:
        self.failed_scenarios.append(FailedScenario(
            scenario_summary=summary,
            dimension=dimension,
            iterations=iterations,
            final_error=error,
        ))
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def update_token_usage(self, by_model: dict[str, dict[str, int]]) -> None:
        for model, usage in by_model.items():
            if model not in self.token_usage:
                self.token_usage[model] = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}
            for key in ("prompt_tokens", "completion_tokens", "calls"):
                self.token_usage[model][key] += usage.get(key, 0)

    def to_dict(self) -> dict:
        return {
            "fork_task_ids": self.fork_task_ids,
            "guardian_task_ids": self.guardian_task_ids,
            "failed_scenarios": [
                {
                    "scenario_summary": f.scenario_summary,
                    "dimension": f.dimension,
                    "iterations": f.iterations,
                    "final_error": f.final_error,
                }
                for f in self.failed_scenarios
            ],
            "coverage": self.coverage.to_dict(),
            "token_usage": self.token_usage,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProgressState:
        state = cls()
        state.fork_task_ids = data.get("fork_task_ids", [])
        state.guardian_task_ids = data.get("guardian_task_ids", [])
        state.failed_scenarios = [
            FailedScenario(**f) for f in data.get("failed_scenarios", [])
        ]
        state.coverage = CoverageState.from_dict(data.get("coverage", {}))
        state.token_usage = data.get("token_usage", {})
        state.last_updated = data.get("last_updated", "")
        return state


def save_progress(state: ProgressState, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2))


def load_progress(path: str | Path) -> ProgressState:
    path = Path(path)
    if not path.exists():
        return ProgressState()
    data = json.loads(path.read_text())
    return ProgressState.from_dict(data)
