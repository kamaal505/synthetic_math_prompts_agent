import json
import os
import time
from pathlib import Path

from core.orchestration.generate_batch import run_generation_pipeline
from utils.config_manager import get_config_manager
from utils.exceptions import TaxonomyError
from utils.helpers import format_duration, get_input
from utils.logging_config import log_error, log_info
from utils.save_results import save_prompts

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"


def main():
    log_info("🧠 Synthetic Prompt Generator (Interactive Mode)")

    # Use ConfigManager for centralized configuration management
    config_manager = get_config_manager()
    config_path = Path("config/settings.yaml")
    config_manager.load_config(config_path)

    # Calculate default max_workers (90% of CPU cores)
    default_max_workers = max(1, int(os.cpu_count() * 0.9))

    # Prompt the user
    log_info("(Leave all fields blank to use defaults from config/settings.yaml)\n")
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
        "Checker model name",
        config_manager.get("checker_model.model_name", "o3-mini"),
    )
    target_provider = get_input(
        "Target model provider",
        config_manager.get("target_model.provider", "openai"),
    )
    target_model = get_input(
        "Target model name", config_manager.get("target_model.model_name", "gpt-4.1")
    )
    # Get the original taxonomy path from config before it gets loaded as JSON
    default_taxonomy_path = "taxonomy/sample_math_taxonomy.json"
    taxonomy_config = config_manager.get("taxonomy")
    if isinstance(taxonomy_config, str):
        default_taxonomy_path = taxonomy_config

    taxonomy_path = get_input("Taxonomy file path", default_taxonomy_path)

    # Determine if all values were left blank (i.e., use config only)
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
        log_info("📝 No overrides provided. Using YAML defaults only.")
        batch_id = config_manager.get("default_batch_id", "batch_01")
        save_path = Path(config_manager.get("output_dir")) / batch_id

        # Load default taxonomy from config using ConfigManager's caching
        default_taxonomy_path = config_manager.get(
            "taxonomy", "taxonomy/sample_math_taxonomy.json"
        )
        if isinstance(default_taxonomy_path, str):
            try:
                taxonomy_data = config_manager.load_taxonomy_file_cached(
                    default_taxonomy_path
                )
                config_manager.set("taxonomy", taxonomy_data)
            except (FileNotFoundError, TaxonomyError) as e:
                log_error(f"❌ Error: {e}")
                return
            except json.JSONDecodeError as e:
                log_error(
                    f"❌ Error: Invalid JSON in default taxonomy file {default_taxonomy_path}: {e}"
                )
                return
    else:
        log_info("🛠 Applying overrides...")

        if batch_id:
            config_manager.set("default_batch_id", batch_id)
        if num_problems:
            config_manager.set("num_problems", int(num_problems))
        if max_workers:
            config_manager.set("max_workers", int(max_workers))

        # Update model configurations using ConfigManager's dot notation
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

        # Handle taxonomy path (either override or default)
        final_taxonomy_path = taxonomy_path or config_manager.get(
            "taxonomy", "taxonomy/sample_math_taxonomy.json"
        )
        if isinstance(final_taxonomy_path, str):
            try:
                taxonomy_data = config_manager.load_taxonomy_file_cached(
                    final_taxonomy_path
                )
                config_manager.set("taxonomy", taxonomy_data)
                if taxonomy_path:
                    log_info(f"✅ Loaded custom taxonomy from: {final_taxonomy_path}")
            except FileNotFoundError as e:
                log_error(f"Error: {e}")
                return
            except json.JSONDecodeError as e:
                log_error(
                    f"Error: Invalid JSON in taxonomy file {final_taxonomy_path}: {e}"
                )
                return

        save_path = Path(config_manager.get("output_dir")) / config_manager.get(
            "default_batch_id", "batch_01"
        )

    config_manager.set("save_path", str(save_path))

    log_info("🚀 Running generation pipeline...\n")

    # Start timing
    start_time = time.monotonic()

    # Get the complete configuration for the pipeline
    config = config_manager.get_all()
    valid, rejected, cost_tracker = run_generation_pipeline(config)

    # Stop timing and calculate duration
    end_time = time.monotonic()
    total_duration = end_time - start_time

    save_prompts(valid, rejected, save_path, cost_tracker)

    # Calculate and display timing information
    num_problems = config_manager.get("num_problems", 10)
    avg_time_per_problem = total_duration / num_problems if num_problems > 0 else 0

    log_info(f"⏱️  Execution completed in {format_duration(total_duration)}")
    log_info(f"📊 Average time per problem: {format_duration(avg_time_per_problem)}")
    log_info("🎉 Done.")


if __name__ == "__main__":
    main()
