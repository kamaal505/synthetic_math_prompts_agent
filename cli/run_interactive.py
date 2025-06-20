import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from pathlib import Path
from orchestration.generate_batch import run_generation_pipeline, load_config
from orchestration.save_results import save_prompts

def get_input(prompt, default=None):
    val = input(f"{prompt} [{default}]: ") if default else input(f"{prompt}: ")
    return val.strip() or None

def main():
    print("\n🧠 Synthetic Prompt Generator (Interactive Mode)")

    # Load default config first
    config_path = Path("config/settings.yaml")
    config = load_config(config_path)

    # Prompt the user
    print("\n(Leave all fields blank to use defaults from config/settings.yaml)\n")
    batch_id = get_input("Enter batch ID", config.get("default_batch_id", "batch_01"))
    num_problems = get_input("Number of problems", str(config.get("num_problems", 10)))
    engineer_provider = get_input("Engineer provider", config.get("engineer_model", {}).get("provider", "gemini"))
    engineer_model = get_input("Engineer model name", config.get("engineer_model", {}).get("model_name", "gemini-2.5-pro"))
    checker_provider = get_input("Checker/validator provider", config.get("checker_model", {}).get("provider", "openai"))
    checker_model = get_input("Checker model name", config.get("checker_model", {}).get("model_name", "o3-mini"))
    target_provider = get_input("Target model provider", config.get("target_model", {}).get("provider", "openai"))
    target_model = get_input("Target model name", config.get("target_model", {}).get("model_name", "gpt-4.1"))

    # Determine if all values were left blank (i.e., use config only)
    all_inputs = [batch_id, num_problems, engineer_provider, engineer_model,
                  checker_provider, checker_model, target_provider, target_model]
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

        config["engineer_model"] = {
            "provider": engineer_provider or config.get("engineer_model", {}).get("provider", "gemini"),
            "model_name": engineer_model or config.get("engineer_model", {}).get("model_name", "gemini-2.5-pro")
        }

        config["checker_model"] = {
            "provider": checker_provider or config.get("checker_model", {}).get("provider", "openai"),
            "model_name": checker_model or config.get("checker_model", {}).get("model_name", "o3-mini")
        }

        config["target_model"] = {
            "provider": target_provider or config.get("target_model", {}).get("provider", "openai"),
            "model_name": target_model or config.get("target_model", {}).get("model_name", "gpt-4.1")
        }

        save_path = Path(config["output_dir"]) / config.get("default_batch_id", "batch_01")

    config["save_path"] = str(save_path)

    print("\n🚀 Running generation pipeline...\n")
    valid, rejected = run_generation_pipeline(config)

    save_prompts(valid, rejected, save_path)
    print("\n🎉 Done.")

if __name__ == "__main__":
    main()
