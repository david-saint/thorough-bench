"""Track scenario pool, coverage, and dedup state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScenarioBrief:
    domain: str
    action: str
    time_pressure: str
    constraint: str
    dimension: str  # "fork" or "guardian"
    target_categories: list[str] = field(default_factory=list)
    summary: str = ""

    def __post_init__(self) -> None:
        if not self.summary:
            self.summary = f"{self.domain}: {self.action}"


class ScenarioRegistry:
    """In-memory scenario pool with dedup and coverage tracking."""

    def __init__(self) -> None:
        self._scenarios: list[ScenarioBrief] = []
        self._used_summaries: set[str] = set()

    @property
    def scenarios(self) -> list[ScenarioBrief]:
        return list(self._scenarios)

    @property
    def all_summaries(self) -> list[str]:
        return [s.summary for s in self._scenarios]

    def add(self, scenario: ScenarioBrief) -> bool:
        """Add a scenario if it's not a near-duplicate. Returns True if added."""
        normalized = scenario.summary.lower().strip()
        if normalized in self._used_summaries:
            return False
        self._scenarios.append(scenario)
        self._used_summaries.add(normalized)
        return True

    def add_batch(self, scenarios: list[ScenarioBrief]) -> int:
        """Add multiple scenarios, returning count of actually added."""
        added = 0
        for s in scenarios:
            if self.add(s):
                added += 1
        return added

    def pop_next(self, dimension: str) -> ScenarioBrief | None:
        """Pop the next unused scenario for the given dimension."""
        for i, s in enumerate(self._scenarios):
            if s.dimension == dimension:
                return self._scenarios.pop(i)
        return None

    def count(self, dimension: str | None = None) -> int:
        if dimension is None:
            return len(self._scenarios)
        return sum(1 for s in self._scenarios if s.dimension == dimension)
