import argparse
import json
import os
from pathlib import Path

from core.orchestration.generate_batch import run_generation_pipeline
from utils.config_manager import get_config_manager
from utils.exceptions import TaxonomyError
from utils.logging_config import log_error, log_info
from utils.save_results import save_prompts

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"


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

    # Use ConfigManager for centralized configuration management
    config_manager = get_config_manager()
    config_manager.load_config(Path(args.config))

    # Handle taxonomy override from command line
    if args.taxonomy_path:
        try:
            taxonomy_data = config_manager.load_taxonomy_file_cached(args.taxonomy_path)
            config_manager.set("taxonomy", taxonomy_data)
        except (FileNotFoundError, TaxonomyError) as e:
            log_error(f"❌ Error: {e}")
            return
        except json.JSONDecodeError as e:
            log_error(
                f"❌ Error: Invalid JSON in taxonomy file {args.taxonomy_path}: {e}"
            )
            return

    # Apply command line overrides using ConfigManager
    if args.num_problems:
        config_manager.set("num_problems", args.num_problems)
    if args.batch_id:
        config_manager.set("default_batch_id", args.batch_id)

    if args.engineer_provider:
        config_manager.set("engineer_model.provider", args.engineer_provider)
    if args.engineer_model:
        config_manager.set("engineer_model.model_name", args.engineer_model)

    if args.checker_provider:
        config_manager.set("checker_model.provider", args.checker_provider)
    if args.checker_model:
        config_manager.set("checker_model.model_name", args.checker_model)

    if args.target_provider:
        config_manager.set("target_model.provider", args.target_provider)
    if args.target_model:
        config_manager.set("target_model.model_name", args.target_model)

    batch_id = config_manager.get("default_batch_id", "batch_01")
    save_path = Path(config_manager.get("output_dir")) / batch_id
    config_manager.set("save_path", str(save_path))

    # Get the complete configuration for the pipeline
    config = config_manager.get_all()
    valid, rejected = run_generation_pipeline(config)
    save_prompts(valid, rejected, save_path)

    log_info(f"✅ {len(valid)} accepted | ❌ {len(rejected)} discarded")


if __name__ == "__main__":
    main()
