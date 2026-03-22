"""Coverage tracking across ambiguity categories, risk families, and domains."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from mmce.harness.schema import Task

from taskgen.scenarios.taxonomies import (
    FORK_AMBIGUITY_CATEGORIES,
    GUARDIAN_RISK_FAMILIES,
)


@dataclass
class CoverageState:
    fork_total: int = 0
    fork_anchors: int = 0
    fork_ambiguity_counts: Counter = field(default_factory=Counter)
    fork_domain_counts: Counter = field(default_factory=Counter)

    guardian_total: int = 0
    guardian_risk_counts: Counter = field(default_factory=Counter)
    guardian_domain_counts: Counter = field(default_factory=Counter)

    def record_fork_task(self, task: Task, domain: str = "") -> None:
        self.fork_total += 1
        if task.calibration_anchor:
            self.fork_anchors += 1
        if domain:
            self.fork_domain_counts[domain] += 1
        # Infer ambiguity categories from axis names
        for axis in task.ambiguity_axes:
            self.fork_ambiguity_counts[axis.axis_name] += 1

    def record_guardian_task(self, task: Task, domain: str = "") -> None:
        self.guardian_total += 1
        if domain:
            self.guardian_domain_counts[domain] += 1
        for flag in task.gold_flags:
            self.guardian_risk_counts[flag.flag_name] += 1

    @property
    def fork_anchor_pct(self) -> float:
        if self.fork_total == 0:
            return 0.0
        return self.fork_anchors / self.fork_total

    def fork_priorities(self) -> list[str]:
        """Return underrepresented ambiguity categories for scenario generation."""
        all_cats = [c.name for c in FORK_AMBIGUITY_CATEGORIES]
        if not self.fork_ambiguity_counts:
            return all_cats

        min_count = min(self.fork_ambiguity_counts.values()) if self.fork_ambiguity_counts else 0
        priorities = []
        for cat in all_cats:
            if self.fork_ambiguity_counts.get(cat, 0) <= min_count:
                priorities.append(cat)
        return priorities

    def guardian_priorities(self) -> list[str]:
        """Return underrepresented risk families for scenario generation."""
        all_fams = [f.name for f in GUARDIAN_RISK_FAMILIES]
        if not self.guardian_risk_counts:
            return all_fams

        # Target: min 4 per family
        priorities = []
        for fam in all_fams:
            if self.guardian_risk_counts.get(fam, 0) < 4:
                priorities.append(fam)
        return priorities

    def summary(self) -> str:
        lines = []
        lines.append(f"=== Fork Coverage ({self.fork_total} tasks) ===")
        lines.append(f"  Calibration anchors: {self.fork_anchors} ({self.fork_anchor_pct:.0%})")
        lines.append("  Ambiguity categories:")
        for cat in FORK_AMBIGUITY_CATEGORIES:
            count = self.fork_ambiguity_counts.get(cat.name, 0)
            lines.append(f"    {cat.name}: {count}")
        if self.fork_domain_counts:
            lines.append("  Domains:")
            for domain, count in self.fork_domain_counts.most_common():
                lines.append(f"    {domain}: {count}")

        lines.append(f"\n=== Guardian Coverage ({self.guardian_total} tasks) ===")
        lines.append("  Risk families:")
        for fam in GUARDIAN_RISK_FAMILIES:
            count = self.guardian_risk_counts.get(fam.name, 0)
            lines.append(f"    {fam.name}: {count}")
        if self.guardian_domain_counts:
            lines.append("  Domains:")
            for domain, count in self.guardian_domain_counts.most_common():
                lines.append(f"    {domain}: {count}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "fork_total": self.fork_total,
            "fork_anchors": self.fork_anchors,
            "fork_ambiguity_counts": dict(self.fork_ambiguity_counts),
            "fork_domain_counts": dict(self.fork_domain_counts),
            "guardian_total": self.guardian_total,
            "guardian_risk_counts": dict(self.guardian_risk_counts),
            "guardian_domain_counts": dict(self.guardian_domain_counts),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CoverageState:
        state = cls()
        state.fork_total = data.get("fork_total", 0)
        state.fork_anchors = data.get("fork_anchors", 0)
        state.fork_ambiguity_counts = Counter(data.get("fork_ambiguity_counts", {}))
        state.fork_domain_counts = Counter(data.get("fork_domain_counts", {}))
        state.guardian_total = data.get("guardian_total", 0)
        state.guardian_risk_counts = Counter(data.get("guardian_risk_counts", {}))
        state.guardian_domain_counts = Counter(data.get("guardian_domain_counts", {}))
        return state


def build_coverage_from_tasks(tasks: list[Task]) -> CoverageState:
    """Build coverage state from a list of existing tasks."""
    state = CoverageState()
    for task in tasks:
        if task.is_fork:
            state.record_fork_task(task)
        elif task.is_guardian:
            state.record_guardian_task(task)
    return state
