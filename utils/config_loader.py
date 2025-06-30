import json
from pathlib import Path

import yaml


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Check if taxonomy is a JSON file path
    if isinstance(config.get("taxonomy"), str) and config["taxonomy"].endswith(".json"):
        taxonomy_path = Path(config["taxonomy"])
        if not taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")

        with open(taxonomy_path, "r", encoding="utf-8") as f:
            config["taxonomy"] = json.load(f)

    return config
