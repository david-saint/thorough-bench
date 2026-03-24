"""Run the MMCE benchmark using an agentic wrapper for a reasoning model."""

import argparse
import sys
from pathlib import Path

from mmce.harness.openrouter import OpenRouterClient
from mmce.kaggle.benchmark import run_benchmark_locally

# The system prompt that guides the base model to perform metacognitive analysis
AGENTIC_SYSTEM_PROMPT = """You are an expert, highly meticulous Senior Staff Engineer. 
Before answering the user's prompt, you must silently analyze the request in a <metacognitive_scratchpad> using the following framework.

<metacognitive_scratchpad>
1. UNCERTAINTY MONITORING (The Fork)
- Is this request materially ambiguous? 
- What specific variables, units, system boundaries, or scopes are missing?
- For each missing variable: Is it a "blocking" ambiguity (I cannot safely proceed) or "non-blocking" (I can safely assume the standard default)?
- *Strict Filter:* Discard theoretical philosophical ambiguities. Only keep variables that would break the system if guessed incorrectly.

2. KNOWLEDGE BOUNDARY DETECTION (The Guardian)
- What hidden risks, prerequisites, or destructive side-effects exist here?
- *Strict Filter:* Discard generic advice ("always write tests", "monitor your app"). Only list risks specific and concrete to THIS exact mutation or action.
</metacognitive_scratchpad>

Once your scratchpad is complete, construct your final response adhering to these strict rules:

1. **Resolve Ambiguity Visibly:** Do not silently guess missing variables. If it is blocking, ask a highly targeted clarifying question. If it is non-blocking, state your explicit assumption (e.g., "Assuming a standard staging rollout..."). You may also use brief branched logic ("If X, do Y; If A, do B").
2. **Surface Risks with Mitigation:** If you identified a critical risk, state it briefly, explain *why* it matters, and provide the mitigation step. 
3. **No Performative Hedging:** Do not apologize. Do not add generic "As an AI" disclaimers. Do not add boilerplate safety warnings. Be direct, technical, and concise.
"""

MODELS = {
    "qwen3.5-27b": "qwen/qwen3.5-27b",
    "mercury-2": "inception/mercury-2",
}

DEFAULT_JUDGE = "qwen/qwen3.5-flash-02-23"

class AgenticOpenRouterClient(OpenRouterClient):
    """Wraps OpenRouterClient to inject the agentic system prompt on every call."""
    
    def prompt(self, text: str, system_prompt: str | None = None) -> str:
        # Override the system prompt with our metacognitive scratchpad prompt
        # We append any existing system prompt if needed, but for MMCE tasks
        # the system prompt is usually not provided or we can just override it.
        combined_system = AGENTIC_SYSTEM_PROMPT
        if system_prompt:
            combined_system += f"\n\n[Original System Prompt]\n{system_prompt}"
            
        return super().prompt(text, system_prompt=combined_system)


def main():
    parser = argparse.ArgumentParser(description="Run Agentic MMCE benchmark")
    parser.add_argument(
        "models",
        nargs="*",
        default=list(MODELS.keys()),
        help=f"Models to test. Shortcuts: {', '.join(MODELS.keys())}. "
             "Or pass a full OpenRouter model ID.",
    )
    parser.add_argument(
        "--judge", default=DEFAULT_JUDGE,
        help=f"Judge model (default: {DEFAULT_JUDGE})",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Don't persist results to disk",
    )
    args = parser.parse_args()

    model_ids = []
    for m in args.models:
        model_ids.append(MODELS.get(m, m))

    judge_id = MODELS.get(args.judge, args.judge)

    print(f"Judge model: {judge_id}")
    print(f"Models to test: {model_ids}")
    print("Using Agentic Metacognitive System Prompt Wrapper")
    print()

    judge_client = OpenRouterClient(model=judge_id)

    for model_id in model_ids:
        print(f"{'=' * 60}")
        print(f"MODEL: {model_id} (Agentic)")
        print(f"{'=' * 60}")

        model_client = AgenticOpenRouterClient(model=model_id)
        base_client = OpenRouterClient(model=model_id)

        run_benchmark_locally(
            prompt_fn=model_client.prompt,
            judge_fn=judge_client.prompt,
            model_name=model_id,
            judge_model=judge_id,
            save_results=not args.no_save,
            control_prompt_fn=base_client.prompt,
            prompt_variant="agentic",
        )
        print()

if __name__ == "__main__":
    main()
