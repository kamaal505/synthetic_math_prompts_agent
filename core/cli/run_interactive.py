import json
import os
import time
from pathlib import Path

from core.orchestration.generate_batch import run_generation_pipeline
from utils.config_loader import load_config
from utils.helpers import get_input, format_duration
from utils.save_results import save_prompts


def main():
    print("\n🧠 Synthetic Prompt Generator (Interactive Mode)")

    # Load default config first
    config_path = Path("config/settings.yaml")
    config = load_config(config_path)

    # Calculate default max_workers (90% of CPU cores)
    default_max_workers = max(1, int(os.cpu_count() * 0.9))

    # Prompt the user
    print("\n(Leave all fields blank to use defaults from config/settings.yaml)\n")
    batch_id = get_input("Enter batch ID", config.get("default_batch_id", "batch_01"))
    num_problems = get_input("Number of problems", str(config.get("num_problems", 10)))
    max_workers = get_input("Number of max workers", str(config.get("max_workers", default_max_workers)))
    engineer_provider = get_input(
        "Engineer provider", config.get("engineer_model", {}).get("provider", "gemini")
    )
    engineer_model = get_input(
        "Engineer model name",
        config.get("engineer_model", {}).get("model_name", "gemini-2.5-pro"),
    )
    checker_provider = get_input(
        "Checker/Validator provider",
        config.get("checker_model", {}).get("provider", "openai"),
    )
    checker_model = get_input(
        "Checker model name",
        config.get("checker_model", {}).get("model_name", "o3-mini"),
    )
    target_provider = get_input(
        "Target model provider",
        config.get("target_model", {}).get("provider", "openai"),
    )
    target_model = get_input(
        "Target model name", config.get("target_model", {}).get("model_name", "gpt-4.1")
    )

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
    ]
    if all(val is None for val in all_inputs):
        print("\n📝 No overrides provided. Using YAML defaults only.")
        batch_id = config.get("default_batch_id", "batch_01")
        save_path = Path(config["output_dir"]) / batch_id
    else:
        print("\n🛠 Applying overrides...")

        if batch_id:
            config["default_batch_id"] = batch_id
        if num_problems:
            config["num_problems"] = int(num_problems)
        if max_workers:
            config["max_workers"] = int(max_workers)

        config["engineer_model"] = {
            "provider": engineer_provider
            or config.get("engineer_model", {}).get("provider", "gemini"),
            "model_name": engineer_model
            or config.get("engineer_model", {}).get("model_name", "gemini-2.5-pro"),
        }

        config["checker_model"] = {
            "provider": checker_provider
            or config.get("checker_model", {}).get("provider", "openai"),
            "model_name": checker_model
            or config.get("checker_model", {}).get("model_name", "o3-mini"),
        }

        config["target_model"] = {
            "provider": target_provider
            or config.get("target_model", {}).get("provider", "openai"),
            "model_name": target_model
            or config.get("target_model", {}).get("model_name", "gpt-4.1"),
        }

        save_path = Path(config["output_dir"]) / config.get(
            "default_batch_id", "batch_01"
        )

    config["save_path"] = str(save_path)

    print("\n🚀 Running generation pipeline...\n")
    
    # Start timing
    start_time = time.monotonic()
    
    valid, rejected, cost_tracker = run_generation_pipeline(config)
    
    # Stop timing and calculate duration
    end_time = time.monotonic()
    total_duration = end_time - start_time
    
    save_prompts(valid, rejected, save_path, cost_tracker)
    
    # Calculate and display timing information
    num_problems = config.get("num_problems", 10)
    avg_time_per_problem = total_duration / num_problems if num_problems > 0 else 0
    
    print(f"\n⏱️  Execution completed in {format_duration(total_duration)}")
    print(f"📊 Average time per problem: {format_duration(avg_time_per_problem)}")
    print("\n🎉 Done.")


if __name__ == "__main__":
    main()
