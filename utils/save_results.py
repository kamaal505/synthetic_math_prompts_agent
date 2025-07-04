import json
import os
from pathlib import Path

from utils.costs import CostTracker
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)


def save_prompts(
    valid_list, discarded_list, save_path, cost_tracker: CostTracker = None
):
    save_dir = Path(save_path)
    os.makedirs(save_dir, exist_ok=True)

    # ✅ Save full JSON with full fidelity
    with open(save_dir / "valid.json", "w", encoding="utf-8") as f:
        json.dump(valid_list, f, indent=2, ensure_ascii=False)

    with open(save_dir / "discarded.json", "w", encoding="utf-8") as f:
        json.dump(discarded_list, f, indent=2, ensure_ascii=False)

    # ✅ Save costs.json if provided
    if cost_tracker:
        run_id = save_dir.name  # Assume save_path = "outputs/<run_id>"
        with open(save_dir / "costs.json", "w", encoding="utf-8") as f:
            json.dump(cost_tracker.as_dict(run_id=run_id), f, indent=2)

    logger.info(f"📁 Results saved to: {save_dir}")
    logger.info(f"✅ valid.json ({len(valid_list)} entries)")
    logger.info(f"❌ discarded.json ({len(discarded_list)} entries)")
    if cost_tracker:
        logger.info(
            f"💰 costs.json saved (Total: ${cost_tracker.get_total_cost():.6f})"
        )
        logger.info(
            f"💰 costs.json saved (Total: ${cost_tracker.get_total_cost():.6f})"
        )
