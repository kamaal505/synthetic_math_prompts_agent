from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)


def safe_log_cost(
    cost_tracker,
    model_config,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    raw_output: str = "",
    raw_prompt: str = "",
):
    """
    Safely log model cost with fallback values and exception handling.

    Args:
        cost_tracker: CostTracker instance
        model_config: Dict containing at least "provider" and "model_name"
        tokens_prompt: Number of tokens in the prompt (estimated or actual)
        tokens_completion: Number of tokens in the model output (estimated or actual)
        raw_output: Raw output string from model
        raw_prompt: Raw prompt string sent to model
    """
    try:
        cost_tracker.log(
            {
                **model_config,
                "raw_output": raw_output,
                "raw_prompt": raw_prompt,
            },
            tokens_prompt or 0,
            tokens_completion or 0,
        )
    except Exception as e:
        logger.error("⚠️ Failed to log model cost: %s", str(e), exc_info=True)
