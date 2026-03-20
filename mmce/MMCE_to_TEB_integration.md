# MMCE to TEB Integration

Version: `0.1-draft`
Status: Draft

## Purpose

This note explains how the Metacognitive Monitoring and Control Evaluation (MMCE) relates to the broader Thoroughness Evaluation Benchmark (TEB).

MMCE is intended to function in two roles at once:

- as a standalone benchmark submission for the Kaggle "Measuring AGI" competition
- as the first canonical module in the larger TEB program

The design goal is that work invested in MMCE should transfer directly into TEB rather than requiring a second benchmark-design cycle after the competition.

## Why MMCE is a natural TEB module

TEB measures whether models finish the whole job once they are capable of the underlying work. Within that broader frame, MMCE captures the metacognitive subset of thoroughness:

- recognizing ambiguity instead of silently assuming
- surfacing hidden risks and prerequisites instead of answering narrowly
- checking completed work instead of stopping at first-pass plausibility

These behaviors are already present inside TEB, but spread across two core dimensions and one agent diagnostic. MMCE groups them into a coherent metacognition-focused benchmark unit.

## Canonical mapping

| MMCE Construct | TEB Component | TEB Track Coverage |
|---|---|---|
| `Uncertainty Monitoring` | `Disambiguation ("The Fork")` | `Single-Turn`, `Long-Context`, `Tool-Using Agent` |
| `Knowledge Boundary Detection` | `Proactive Flagging ("The Guardian")` | `Single-Turn`, `Long-Context`, `Tool-Using Agent` |
| `Metacognitive Control` | `Self-Audit Quality` diagnostic | `Tool-Using Agent` only |

## Important integration choice

Within TEB, `Self-Audit Quality` is an agent-process diagnostic reported alongside the main dimensions. Within MMCE, the same behavior is promoted into a scored construct because metacognitive control is one of the benchmark's central targets.

This is a deliberate reframing rather than a contradiction:

- in TEB, self-audit helps explain agent thoroughness failures
- in MMCE, self-audit is itself part of the construct being benchmarked

The underlying task materials, trace logic, and scoring logic can still be reused directly.

## Reuse rule

The intended reuse contract is:

- every MMCE task should be authored so it can also live inside TEB
- every MMCE control task should be reusable as a TEB matched control where relevant
- every MMCE scoring rule should either inherit from TEB directly or define a compatible specialization

This means MMCE should not introduce benchmark mechanics that are incompatible with TEB's atomic-item, capability-conditioned framework.

## What transfers directly

The following should transfer into TEB with no redesign:

- task templates for Fork-style ambiguity-axis prompts
- task templates for Guardian-style proactive-flagging prompts
- matched controls for those constructs
- agent self-audit trace parsers
- judge prompts for ambiguity legitimacy, relevance, and correctness
- noise taxonomy for metacognitive overproduction

## What remains outside MMCE

MMCE does not cover the full scope of TEB. The following TEB dimensions remain outside the module:

- `Constraint Recall`
- `Unprompted Depth`
- `Edge-Case Exhaustiveness`
- `Generation Endurance`
- `Exhaustive Synthesis`

The following agent diagnostics also remain outside MMCE:

- `Inspection Breadth`
- `Verification Actions`
- `Premature Closure Rate`

## Strategic value

Using MMCE as the competition submission creates a practical path for funding and validating the broader TEB effort:

- MMCE is narrower and easier to communicate than the full TEB
- MMCE still exercises TEB's central design philosophy: capability-conditioned thoroughness evaluation
- successful implementation of MMCE yields reusable tasks, controls, scoring tools, and judge infrastructure for the parent benchmark

In short, MMCE should be treated as a focused, competition-ready benchmark that simultaneously bootstraps the broader TEB program.
