from core.orchestration.generate_batch import run_generation_pipeline
from utils.exceptions import PipelineError
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)


def run_pipeline_from_config(config: dict) -> dict:
    try:
        valid, discarded, cost_tracker = run_generation_pipeline(config)
        return {
            "valid_prompts": valid,
            "discarded_prompts": discarded,
            "total_cost": cost_tracker.get_total_cost(),
            "metadata": {
                "total_attempted": len(valid) + len(discarded),
                "total_accepted": len(valid),
            },
        }
    except Exception as e:
        logger.error("🚨 Pipeline execution failed: %s", str(e), exc_info=True)
        raise PipelineError(f"Pipeline crashed: {e}", stage="execution")
