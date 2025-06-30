import argparse
import json
from pathlib import Path

import yaml

from core.orchestration.generate_batch import run_generation_pipeline
from core.orchestration.save_results import save_prompts
from utils.config_loader import load_config


def main():
    parser = argparse.ArgumentParser(description="Synthetic Prompt Generator CLI")
    parser.add_argument(
        "--config",
        type=str,
        default="config/settings.yaml",
        help="Path to config YAML file",
    )
    parser.add_argument(
        "--batch-id", type=str, help="Batch ID for output (e.g., batch_03)"
    )
    parser.add_argument(
        "--num-problems", type=int, help="Override the number of problems to generate"
    )

    parser.add_argument(
        "--engineer-provider",
        type=str,
        help="Override engineer model provider (e.g., openai, gemini)",
    )
    parser.add_argument(
        "--engineer-model", type=str, help="Override engineer model name"
    )

    parser.add_argument(
        "--checker-provider", type=str, help="Override checker model provider"
    )
    parser.add_argument("--checker-model", type=str, help="Override checker model name")

    parser.add_argument(
        "--target-provider", type=str, help="Override target model provider"
    )
    parser.add_argument("--target-model", type=str, help="Override target model name")

    parser.add_argument(
        "--taxonomy-path", type=str, help="Override taxonomy file path (JSON file)"
    )

    args = parser.parse_args()
    config = load_config(Path(args.config))

    # Handle taxonomy override from command line
    if args.taxonomy_path:
        taxonomy_path = Path(args.taxonomy_path)
        try:
            if not taxonomy_path.exists():
                raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")

            with open(taxonomy_path, "r", encoding="utf-8") as f:
                config["taxonomy"] = json.load(f)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in taxonomy file {taxonomy_path}: {e}")
            return

    if args.num_problems:
        config["num_problems"] = args.num_problems
    if args.batch_id:
        config["default_batch_id"] = args.batch_id

    if args.engineer_provider:
        config.setdefault("engineer_model", {})["provider"] = args.engineer_provider
    if args.engineer_model:
        config.setdefault("engineer_model", {})["model_name"] = args.engineer_model

    if args.checker_provider:
        config.setdefault("checker_model", {})["provider"] = args.checker_provider
    if args.checker_model:
        config.setdefault("checker_model", {})["model_name"] = args.checker_model

    if args.target_provider:
        config.setdefault("target_model", {})["provider"] = args.target_provider
    if args.target_model:
        config.setdefault("target_model", {})["model_name"] = args.target_model

    batch_id = config.get("default_batch_id", "batch_01")
    save_path = Path(config["output_dir"]) / batch_id
    config["save_path"] = str(save_path)

    valid, rejected = run_generation_pipeline(config)
    save_prompts(valid, rejected, save_path)

    print(f"\n✅ {len(valid)} accepted | ❌ {len(rejected)} discarded")


if __name__ == "__main__":
    main()
