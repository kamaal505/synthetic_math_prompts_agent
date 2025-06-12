import argparse
import yaml
from pathlib import Path
from orchestration.generate_batch import run_generation_pipeline
from orchestration.save_results import save_prompts

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Synthetic Prompt Generator CLI")
    parser.add_argument("--config", type=str, default="config/settings.yaml",
                        help="Path to config YAML file")
    parser.add_argument("--batch-id", type=str, default=None,
                        help="Batch ID for output (e.g., batch_03)")
    parser.add_argument("--num-problems", type=int,
                        help="Override the number of problems to generate")

    args = parser.parse_args()

    # Load settings
    config = load_config(args.config)
    batch_id = args.batch_id or config.get("default_batch_id", "batch_01")

    # CLI override
    if args.num_problems:
        config["num_problems"] = args.num_problems

    save_path = Path(config["output_dir"]) / batch_id
    config["save_path"] = str(save_path)

    # Run pipeline
    valid, rejected = run_generation_pipeline(config)
    save_prompts(valid, rejected, save_path)

if __name__ == "__main__":
    main()
