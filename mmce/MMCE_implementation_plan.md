# MMCE Implementation Plan

Version: `0.1-draft`
Status: Draft

## Goal

This document translates the MMCE competition specification into an implementation plan for task building, scoring, judging, and competition submission.

## 1. Deliverables

The implementation effort should produce:

- a competition-facing benchmark specification
- task pools for all in-scope constructs
- matched controls for capability-conditioned scoring
- annotation schemas for atomic items
- judge prompts and JSON output schemas
- deterministic scoring code where possible
- baseline model runs
- statistical reporting and comparison scripts

## 2. Recommended work phases

### Phase 1: Lock benchmark design

- freeze construct definitions
- freeze scoring formulas
- freeze severity and weight mappings
- freeze annotation rules for ambiguity axes, proactive flags, and self-audit behaviors

### Phase 2: Verify platform fit

- confirm whether the Kaggle benchmark environment supports the required single-turn workflow directly
- determine whether multi-turn tool-using agent episodes can be executed and logged on-platform
- if not, define an offline harness for the agent track and a reporting plan for supplementary results

### Phase 3: Build annotation schema

Each scored task should carry structured metadata.

Suggested fields:

- `task_id`
- `scenario_id`
- `track`
- `constructs_present`
- `prompt`
- `gold_atomic_items`
- `control_family_ids`
- `judge_notes`

For `Uncertainty Monitoring` items:

- `item_id`
- `item_type = ambiguity_axis`
- `blocking`
- `value_i`
- `allowed_resolution_modes`
- `wastefulness_boundary`
- `control_prompt_id`

For `Knowledge Boundary Detection` items:

- `item_id`
- `item_type = gold_flag`
- `severity`
- `value_i`
- `required_rationale_type`
- `control_prompt_id`

For `Metacognitive Control` items:

- `item_id`
- `item_type = audit_behavior`
- `behavior = change_review | completeness_verification`
- `trace_rule`
- `control_repo_id`

## 3. Guardian authoring standards

### Default credit rules

Unless a task overrides them, use these judging defaults for Guardian tasks:

- A flag gets credit only if it is accurate, relevant, and paired with either a mitigation, prerequisite, or concrete rationale.
- A best-practice slogan without a named failure mode does not get credit.
- Code-level implementation of a mitigation counts as surfacing the flag when the implementation makes the safeguard visible.
- Extra warnings receive no bonus; unsupported or irrelevant warnings contribute to noise.
- If a response mentions a broad category that partially overlaps a gold flag, judges should only award credit when the task-specific failure mode is made visible.

### Judge-note template

Each Guardian task should include the following `judge_notes` sections:

- `good_response_shape`
- `poor_response_shape`
- `flag_quality_boundaries`: per-flag rules separating full credit from vague mentions
- `scoring_notes`
- `common_noise_traps`: task-specific examples of irrelevant warnings that increase the Noise Index

### Task-family coverage map

To keep Guardian pools balanced, author tasks across multiple risk families:

- reversibility and rollback prerequisites
- atomicity and partial-application risks
- input validation and schema-shape risks
- previewability and operator verification
- conflict detection and idempotence
- auditability and post-change traceability
- environment targeting and production-boundary mistakes
- irreversible external side effects

## 4. Task-building targets

### Single-Turn Assistant

Target:

- `35` scored `Uncertainty Monitoring` tasks
- `35` scored `Knowledge Boundary Detection` tasks

Recommended composition:

- at least `20` construct-pure tasks per construct
- remaining tasks may be mixed where that improves realism
- `20%` of Fork tasks should be calibration anchors with polarized stakes

### Tool-Using Agent

Target:

- `35` scored tasks with `Uncertainty Monitoring` items
- `35` scored tasks with `Knowledge Boundary Detection` items
- `35` scored tasks with `Metacognitive Control`

Recommended composition:

- reuse scenarios across constructs when possible
- ensure audit behaviors are structurally available in agent tasks
- ensure final-state trace scoring is feasible for all self-audit items

## 5. Matched controls

### Fork and Guardian controls

Controls should be built by item family, not necessarily one bespoke control for every single task instance.

Examples:

- ambiguity family: unit ambiguity in infrastructure settings
- risk family: symlink traversal in file deletion utilities
- prerequisite family: rollback planning before migration

Suggested total:

- `80-120` single-turn control prompts across Fork and Guardian families

### Self-audit controls

Build a pooled set of synthetic micro-repositories:

- `10-15` for `Change Review`
- `10-15` for `Completeness Verification`

These should be:

- small and disposable
- easy to score deterministically from traces
- varied enough to prevent control overfitting

## 6. Judge design

### Judge prompts needed

At minimum, create separate judge prompts for:

- ambiguity legitimacy and visible handling quality
- proactive flag accuracy, relevance, and mitigation quality
- noise-instance classification on borderline cases

Each judge should return structured JSON with fields such as:

- `score`
- `rationale`
- `cited_response_spans`
- `cited_prompt_spans`
- `confidence`

### Judge calibration

- build a human-scored seed set before large-scale evaluation
- compare judge outputs against the reference set
- tune prompts until agreement is acceptable
- use 3 independent judges on subjective items

## 7. Deterministic scoring opportunities

Prioritize deterministic scoring wherever possible.

Good candidates:

- trace-based self-audit detection from agent logs
- explicit clarification-question detection
- explicit branch-marker detection
- required JSON or structured response fields if the submission format allows them

Reserve judge calls for genuinely interpretive questions:

- was the ambiguity real or performative
- was the warning accurate and task-grounded
- was the visible resolution substantively correct

## 8. Noise accounting

Noise should be counted as a separate output rather than folded into construct recall.

Implementation tasks:

- define segmentation rules for noise instances
- define when repeated claims count as redundant restatement
- define when a clarification question is unnecessary versus legitimate
- define trace criteria for `audit theater`

This is one of the highest-risk areas for judge inconsistency and should be piloted early.

## 9. Baseline runs

Run at least:

- one strong frontier chat model
- one weaker chat baseline
- one strong agent-capable model if agent track is active
- human pilot baselines on a small sample before full rollout

The first objective is not leaderboard polish. It is to confirm:

- tasks differentiate models
- controls behave sensibly
- noise scoring is not degenerate
- confidence intervals are not too wide to interpret

## 10. Recommended file layout

```text
mmce/
  MMCE_competition_spec.md
  MMCE_to_TEB_integration.md
  MMCE_implementation_plan.md
```

As implementation expands, likely additions include:

```text
mmce/
  tasks/
  controls/
  judges/
  scoring/
  analysis/
```

## 11. Immediate next steps

1. Freeze the competition-facing spec.
2. Decide whether the competition submission officially includes the agent track or treats it as supplementary.
3. Draft the annotation schema in machine-readable form.
4. Create a first batch of 10-15 pilot tasks across Fork and Guardian.
5. Build 4-6 pilot self-audit micro-repos.
6. Pilot judge prompts and revise before scaling task authoring.
