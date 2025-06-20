import argparse
import yaml
from pathlib import Path
from orchestration.generate_batch import run_generation_pipeline, load_config
from orchestration.save_results import save_prompts

def main():
    parser = argparse.ArgumentParser(description="Synthetic Prompt Generator CLI")
    parser.add_argument("--config", type=str, default="config/settings.yaml", help="Path to config YAML file")
    parser.add_argument("--batch-id", type=str, help="Batch ID for output (e.g., batch_03)")
    parser.add_argument("--num-problems", type=int, help="Override the number of problems to generate")

    parser.add_argument("--engineer-provider", type=str, help="Override engineer model provider (e.g., openai, gemini)")
    parser.add_argument("--engineer-model", type=str, help="Override engineer model name")

    parser.add_argument("--checker-provider", type=str, help="Override checker model provider")
    parser.add_argument("--checker-model", type=str, help="Override checker model name")

    parser.add_argument("--target-provider", type=str, help="Override target model provider")
    parser.add_argument("--target-model", type=str, help="Override target model name")

    args = parser.parse_args()
    config = load_config(Path(args.config))

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
