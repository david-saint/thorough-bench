"""Run the MMCE benchmark against one or more models via OpenRouter."""

from __future__ import annotations

import argparse
import sys

from mmce.harness.openrouter import OpenRouterClient
from mmce.kaggle.benchmark import run_benchmark_locally

# Cheap models suitable for testing
MODELS = {
    "gpt-5.4-nano": "openai/gpt-5.4-nano",
    "gpt-5.4-mini": "openai/gpt-5.4-mini",
    "gemini-3-flash": "google/gemini-3-flash-preview",
    "gemini-3.1-flash-lite": "google/gemini-3.1-flash-lite-preview",
}

DEFAULT_JUDGE = "qwen/qwen3.5-flash-02-23"


def main():
    parser = argparse.ArgumentParser(description="Run MMCE benchmark via OpenRouter")
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

    # Resolve model shortcuts
    model_ids = []
    for m in args.models:
        model_ids.append(MODELS.get(m, m))

    judge_id = MODELS.get(args.judge, args.judge)

    print(f"Judge model: {judge_id}")
    print(f"Models to test: {model_ids}")
    print()

    judge_client = OpenRouterClient(model=judge_id)

    for model_id in model_ids:
        print(f"{'=' * 60}")
        print(f"MODEL: {model_id}")
        print(f"{'=' * 60}")

        model_client = OpenRouterClient(model=model_id)

        run_benchmark_locally(
            prompt_fn=model_client.prompt,
            judge_fn=judge_client.prompt,
            model_name=model_id,
            judge_model=judge_id,
            save_results=not args.no_save,
        )
        print()


if __name__ == "__main__":
    main()
