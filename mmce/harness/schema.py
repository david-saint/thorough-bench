"""Pydantic v2 models mirroring the MMCE YAML task structure."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator


# --- Enums ---

class Severity(str, Enum):
    critical = "critical"
    important = "important"
    optional = "optional"


class ResolutionMode(str, Enum):
    highly_targeted_clarifying_question = "highly_targeted_clarifying_question"
    explicit_assumption = "explicit_assumption"
    explicit_branch_coverage = "explicit_branch_coverage"


class NoiseClass(str, Enum):
    false_uncertainty = "false_uncertainty"
    performative_hedging = "performative_hedging"
    unnecessary_clarification = "unnecessary_clarification"
    hallucinated_risk = "hallucinated_risk"
    redundant_restatement = "redundant_restatement"
    audit_theater = "audit_theater"


# --- Atomic Items (discriminated union on item_type) ---

class AmbiguityAxis(BaseModel):
    item_id: str
    item_type: Literal["ambiguity_axis"]
    axis_name: str
    blocking: bool
    value_i: float = Field(gt=0)
    ambiguity: str
    allowed_resolution_modes: list[ResolutionMode]
    wastefulness_boundary: str
    control_prompt_id: str


class GoldFlag(BaseModel):
    item_id: str
    item_type: Literal["gold_flag"]
    flag_name: str
    severity: Severity
    value_i: float = Field(gt=0)
    rationale: str
    required_rationale_type: str
    control_prompt_id: str


AtomicItem = Annotated[
    Union[AmbiguityAxis, GoldFlag],
    Field(discriminator="item_type"),
]


# --- Control Prompts ---

class ControlPrompt(BaseModel):
    control_prompt_id: str
    tests_item_ids: list[str]
    prompt: str
    success_criteria: list[str]


# --- Judge Notes ---

class JudgeNotes(BaseModel):
    good_response_shape: list[str]
    poor_response_shape: list[str]
    scoring_notes: list[str]
    flag_quality_boundaries: list[str] | None = None
    common_noise_traps: list[str] | None = None


# --- Task ---

class Task(BaseModel):
    task_id: str
    scenario_id: str
    track: str
    constructs_present: list[str]
    dimension_alias: str
    prompt: str
    gold_atomic_items: list[AtomicItem]
    control_prompts: list[ControlPrompt]
    judge_notes: JudgeNotes
    task_class: str | None = None
    calibration_anchor: bool | None = None
    anchor_reason: str | None = None
    control_family_ids: list[str] | None = None

    @property
    def is_fork(self) -> bool:
        return self.dimension_alias == "fork"

    @property
    def is_guardian(self) -> bool:
        return self.dimension_alias == "guardian"

    @property
    def ambiguity_axes(self) -> list[AmbiguityAxis]:
        return [item for item in self.gold_atomic_items if isinstance(item, AmbiguityAxis)]

    @property
    def gold_flags(self) -> list[GoldFlag]:
        return [item for item in self.gold_atomic_items if isinstance(item, GoldFlag)]

    def get_control(self, control_prompt_id: str) -> ControlPrompt:
        for cp in self.control_prompts:
            if cp.control_prompt_id == control_prompt_id:
                return cp
        raise KeyError(f"Control prompt {control_prompt_id!r} not found")

    def total_value(self) -> float:
        return sum(item.value_i for item in self.gold_atomic_items)


# --- Judge Output Models ---

class ForkItemVerdict(BaseModel):
    item_id: str
    execution_score: float = Field(description="0.0, 0.5, or 1.0")
    correct: int = Field(ge=0, le=1, description="0 or 1")
    rationale: str

    @field_validator("execution_score")
    @classmethod
    def _check_execution_score(cls, v: float) -> float:
        if v not in {0.0, 0.5, 1.0}:
            raise ValueError(f"execution_score must be 0.0, 0.5, or 1.0, got {v}")
        return v


class GuardianItemVerdict(BaseModel):
    item_id: str
    complete: int = Field(ge=0, le=1, description="0 or 1")
    correct: int = Field(ge=0, le=1, description="0 or 1")
    rationale: str


class ControlVerdict(BaseModel):
    control_prompt_id: str
    success: int = Field(ge=0, le=1, description="0 or 1")
    rationale: str


class NoiseInstance(BaseModel):
    description: str
    noise_class: NoiseClass
    weight: float = Field(default=1.0, gt=0)


class Judgments(BaseModel):
    """All judge verdicts for a single task evaluation."""
    fork_verdicts: list[ForkItemVerdict] = Field(default_factory=list)
    guardian_verdicts: list[GuardianItemVerdict] = Field(default_factory=list)
    control_verdicts: list[ControlVerdict] = Field(default_factory=list)
    noise_instances: list[NoiseInstance] = Field(default_factory=list)
    raw_outputs: dict[str, str] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Computed scores for one task."""
    task_id: str
    absolute_coverage: float
    conditional_thoroughness: float | None  # None if denominator is 0
    noise_index: float
    judgments: Judgments
    capability_map: dict[str, int] = Field(default_factory=dict)  # item_id -> capable_i
    dimension_alias: str = ""
    constructs_present: list[str] = Field(default_factory=list)
