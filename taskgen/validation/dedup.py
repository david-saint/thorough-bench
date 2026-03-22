"""LLM-based semantic deduplication."""

from __future__ import annotations

from taskgen.llm.client import TaskGenLLMClient


DEDUP_SYSTEM = """\
You are a similarity judge. Given two task descriptions, score their semantic \
similarity from 0.0 (completely different) to 1.0 (testing the same thing).

Consider:
- Same domain + same risks/ambiguities = high similarity
- Same domain + different risks = moderate similarity
- Different domain + same abstract pattern = low-moderate similarity
- Different domain + different risks = low similarity

Return ONLY a JSON object: {"similarity": 0.XX, "rationale": "brief reason"}"""


def check_similarity(
    client: TaskGenLLMClient,
    task_a_summary: str,
    task_b_summary: str,
    model_override: str | None = None,
) -> float:
    """Check semantic similarity between two task summaries. Returns 0.0-1.0."""
    user_prompt = f"""\
Task A: {task_a_summary}

Task B: {task_b_summary}

Score their similarity from 0.0 to 1.0."""

    result = client.generate_json(user_prompt, DEDUP_SYSTEM, model_override)
    return float(result.get("similarity", 0.0))


def check_task_against_existing(
    client: TaskGenLLMClient,
    new_task_summary: str,
    existing_summaries: list[str],
    threshold: float = 0.85,
    model_override: str | None = None,
) -> tuple[bool, str | None]:
    """Check if a new task is too similar to any existing task.

    Returns (is_duplicate, most_similar_summary).
    """
    if not existing_summaries:
        return False, None

    # Batch check: ask the model to compare against all existing at once
    # for efficiency (avoids N separate LLM calls)
    existing_list = "\n".join(
        f"  {i+1}. {s}" for i, s in enumerate(existing_summaries)
    )

    user_prompt = f"""\
New task: {new_task_summary}

Existing tasks:
{existing_list}

For each existing task, score similarity to the new task (0.0-1.0).
Return JSON: {{"scores": [{{"index": 1, "similarity": 0.XX}}], "max_similarity": 0.XX, "most_similar_index": N}}"""

    result = client.generate_json(user_prompt, DEDUP_SYSTEM, model_override)

    max_sim = float(result.get("max_similarity", 0.0))
    most_similar_idx = int(result.get("most_similar_index", 0)) - 1

    if max_sim >= threshold and 0 <= most_similar_idx < len(existing_summaries):
        return True, existing_summaries[most_similar_idx]

    return False, None
