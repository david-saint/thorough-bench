# MMCE Submission Narrative

## Working Title

Metacognitive Monitoring and Control Evaluation (MMCE): Benchmarking Whether AI Systems Know When to Ask, Warn, and Verify

## One-paragraph version

The Metacognitive Monitoring and Control Evaluation (MMCE) is a benchmark for a class of failures that matter in deployment but are poorly captured by standard capability evaluations: failures of uncertainty monitoring, knowledge-boundary detection, and self-verification. Instead of asking only whether a model can produce a correct answer, MMCE asks whether the model notices when a task is underspecified, proactively surfaces missing risks or prerequisites, and, in agent settings, checks its own work before declaring completion. Its central methodological contribution is capability-conditioned scoring, which separates metacognitive failures from failures of base task competence. MMCE is scoped to be implementable for the Kaggle competition now, while also serving as the first reusable module in the broader Thoroughness Evaluation Benchmark (TEB).

## Problem

Many important AI failures are not simple capability failures. Models often know enough to complete the task, but fail because they do not monitor their own uncertainty well.

Common examples include:

- silently picking one interpretation of an ambiguous instruction
- omitting a critical prerequisite because the user did not explicitly ask for it
- making code changes and then declaring success without checking what changed or whether the task is actually complete

These failures are especially costly in production and agentic settings, where plausible-looking output is often not enough.

## Gap in current evaluation

Most benchmarks focus on end-task correctness, factuality, or general reasoning. Those matter, but they do not directly measure whether a model:

- knows when uncertainty should be made visible
- knows when a user's request is missing important context
- turns detected uncertainty into verification or revision

As a result, current evaluations can overestimate the practical reliability of models that are capable but poorly calibrated or weak at self-regulation.

## What MMCE measures

MMCE evaluates three constructs:

- `Uncertainty Monitoring`: does the model detect material ambiguity and resolve it visibly rather than silently?
- `Knowledge Boundary Detection`: does the model proactively surface important risks, prerequisites, or caveats that the user would reasonably want to know?
- `Metacognitive Control`: after taking action, does the agent review and verify its own work before stopping?

Together, these constructs target whether the model knows what it knows, recognizes what it does not know, and acts on that knowledge.

## What is novel

The core methodological innovation is `capability-conditioned scoring`.

MMCE does not treat every omission as a metacognitive failure. Instead, it pairs full tasks with matched controls that test the same atomic item in isolation. A model is only penalized for missing an item in the full task when it appears capable of handling that item on its own. This helps isolate failures of monitoring and control from failures of underlying ability.

MMCE also treats noise as a first-class measurement target. The benchmark separately reports a `Noise Index` for behaviors like unnecessary clarification, performative hedging, hallucinated risks, and unsupported claims of checking. This prevents models from appearing metacognitively strong simply by sounding cautious.

## Why Kaggle is a good venue

The Kaggle competition is a strong fit because MMCE is designed as a benchmark, not just a prompting trick or evaluation anecdote. It has:

- clearly defined constructs
- atomic-item scoring
- matched controls
- a path to both deterministic and judge-based evaluation
- explicit statistical reporting requirements

It is also scoped to allow a realistic first implementation. The primary competition track is single-turn prompt-response evaluation, while the more demanding tool-using agent track can be included if platform support is sufficient or reported as a supplementary offline evaluation.

## Why this matters in practice

In real use, a model that is slightly weaker overall but reliably surfaces ambiguity, flags missing prerequisites, and checks its work may be more useful than a stronger model that fails silently. MMCE aims to measure that difference directly.

This makes the benchmark especially relevant for:

- coding assistants
- operational planning assistants
- safety- or reliability-sensitive copilots
- tool-using agents

## Broader impact

MMCE is intentionally scoped as a standalone benchmark submission, but it also has leverage beyond the competition. It is designed so that the same task templates, controls, and scoring logic can be reused in the broader Thoroughness Evaluation Benchmark (TEB), where metacognition is one major component of overall thoroughness.

That means the competition effort does double duty:

- it produces a useful standalone benchmark for metacognitive evaluation
- it bootstraps reusable infrastructure for a larger benchmark program on AI thoroughness and reliability

## Short closing pitch

MMCE asks a simple but consequential question: not just whether a model can do the work, but whether it knows when it should pause, warn, ask, or check. That is a central part of practical intelligence, and it deserves direct measurement.
