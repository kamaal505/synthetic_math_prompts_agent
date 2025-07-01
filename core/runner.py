from core.orchestration.generate_batch import run_generation_pipeline
from utils.exceptions import PipelineError
from utils.logging_config import log_error


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
        log_error("🚨 Pipeline execution failed", exception=e)
        raise PipelineError(f"Pipeline crashed: {e}", stage="execution")
