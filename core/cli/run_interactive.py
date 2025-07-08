import json
import logging
import os
import time
from pathlib import Path

from core.orchestration.generate_batch import run_generation_pipeline
from utils.config_manager import get_config_manager
from utils.exceptions import TaxonomyError
from utils.helpers import format_duration, get_input
from utils.logging_config import get_logger, setup_logger
from utils.save_results import save_prompts

# Initialize logging system with console output
setup_logger(console_output=True, level="INFO")

# Get logger for this module
logger = get_logger(__name__)

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"


def main():
    logger.info("🧠 Synthetic Prompt Generator (Interactive Mode)")

    config_manager = get_config_manager()
    config_path = Path("config/settings.yaml")
    config_manager.load_config(config_path)

    default_max_workers = max(1, int(os.cpu_count() * 0.9))

    logger.info("(Leave all fields blank to use defaults from config/settings.yaml)\n")
    batch_id = get_input(
        "Enter batch ID", config_manager.get("default_batch_id", "batch_01")
    )
    num_problems = get_input(
        "Number of problems", str(config_manager.get("num_problems", 10))
    )
    max_workers = get_input(
        "Number of max workers",
        str(config_manager.get("max_workers", default_max_workers)),
    )
    engineer_provider = get_input(
        "Engineer provider", config_manager.get("engineer_model.provider", "gemini")
    )
    engineer_model = get_input(
        "Engineer model name",
        config_manager.get("engineer_model.model_name", "gemini-2.5-pro"),
    )
    checker_provider = get_input(
        "Checker/Validator provider",
        config_manager.get("checker_model.provider", "openai"),
    )
    checker_model = get_input(
        "Checker model name", config_manager.get("checker_model.model_name", "o3-mini")
    )
    target_provider = get_input(
        "Target model provider", config_manager.get("target_model.provider", "openai")
    )
    target_model = get_input(
        "Target model name", config_manager.get("target_model.model_name", "gpt-4.1")
    )
    # Use enhanced taxonomy by default
    default_taxonomy_path = "taxonomy/enhanced_math_taxonomy.json"

    taxonomy_path = None  # <-- Ensure this is defined even in seed mode

    use_seed = get_input("Use benchmark seed data? (y/n)", "n").strip().lower() == "y"
    config_manager.set("use_seed_data", use_seed)

    if use_seed:
        benchmark_name = get_input("Which benchmark? (e.g., AIME, HMMT, MATH500)", "AIME").strip()
        if not benchmark_name:
            benchmark_name = "AIME"
        config_manager.set("benchmark_name", benchmark_name)
    else:
        taxonomy_path = get_input("Taxonomy file path", default_taxonomy_path)

    use_search = get_input("Enable search-based similarity scoring? (y/n)", "n")
    config_manager.set("use_search", (use_search or "n").strip().lower() == "y")

    all_inputs = [
        batch_id,
        num_problems,
        max_workers,
        engineer_provider,
        engineer_model,
        checker_provider,
        checker_model,
        target_provider,
        target_model,
        taxonomy_path,
    ]
    if all(val is None for val in all_inputs):
        logger.info("📝 No overrides provided. Using YAML defaults only.")
        batch_id = config_manager.get("default_batch_id", "batch_01")
        save_path = Path(config_manager.get("output_dir")) / batch_id

        default_taxonomy_path = config_manager.get(
            "taxonomy", "taxonomy/enhanced_math_taxonomy.json"
        )
        if isinstance(default_taxonomy_path, str):
            try:
                taxonomy_data = config_manager.load_taxonomy_file_cached(
                    default_taxonomy_path
                )
                config_manager.set("taxonomy", taxonomy_data)
            except (FileNotFoundError, TaxonomyError, json.JSONDecodeError) as e:
                logger.error(f"❌ Error: {e}")
                return
    else:
        logger.info("🛠 Applying overrides...")
        if batch_id:
            config_manager.set("default_batch_id", batch_id)
        if num_problems:
            config_manager.set("num_problems", int(num_problems))
        if max_workers:
            config_manager.set("max_workers", int(max_workers))
        if engineer_provider:
            config_manager.set("engineer_model.provider", engineer_provider)
        if engineer_model:
            config_manager.set("engineer_model.model_name", engineer_model)
        if checker_provider:
            config_manager.set("checker_model.provider", checker_provider)
        if checker_model:
            config_manager.set("checker_model.model_name", checker_model)
        if target_provider:
            config_manager.set("target_model.provider", target_provider)
        if target_model:
            config_manager.set("target_model.model_name", target_model)

        final_taxonomy_path = taxonomy_path or config_manager.get(
            "taxonomy", "taxonomy/enhanced_math_taxonomy.json"
        )
        if isinstance(final_taxonomy_path, str):
            try:
                taxonomy_data = config_manager.load_taxonomy_file_cached(
                    final_taxonomy_path
                )
                config_manager.set("taxonomy", taxonomy_data)
                if taxonomy_path:
                    logger.info(
                        f"✅ Loaded custom taxonomy from: {final_taxonomy_path}"
                    )
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error: {e}")
                return

        save_path = Path(config_manager.get("output_dir")) / config_manager.get(
            "default_batch_id", "batch_01"
        )

    config_manager.set("save_path", str(save_path))

    if config_manager.get("use_search", False):
        logger.info("🔍 Search similarity scoring is ENABLED.\n")
    else:
        logger.info("🚫 Search similarity scoring is DISABLED.\n")

    logger.info("🚀 Running generation pipeline...\n")
    start_time = time.monotonic()

    config = config_manager.get_all()
    valid, rejected, cost_tracker = run_generation_pipeline(config)

    end_time = time.monotonic()
    total_duration = end_time - start_time

    save_prompts(valid, rejected, save_path, cost_tracker)

    num_problems = config_manager.get("num_problems", 10)
    avg_time_per_problem = total_duration / num_problems if num_problems > 0 else 0

    logger.info(f"⏱️  Execution completed in {format_duration(total_duration)}")
    logger.info(f"📊 Average time per problem: {format_duration(avg_time_per_problem)}")
    logger.info("🎉 Done.")


if __name__ == "__main__":
    main()
