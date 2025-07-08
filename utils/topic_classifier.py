from utils.json_utils import safe_json_parse
from core.llm.openai_utils import call_openai_model
from utils.exceptions import ModelError
from utils.costs import CostTracker
from utils.cost_estimation import safe_log_cost

def classify_subject_topic(
    problem_text: str,
    model_name: str = "gpt-4.1",
    cost_tracker: CostTracker = None
) -> tuple[str, str]:
    """
    Classifies a math problem into (subject, topic) using a lightweight LLM.
    """

    prompt = f"""
You are a math taxonomy expert.

Classify the following math problem into the most appropriate subject and topic.

Problem:
\"\"\"
{problem_text.strip()}
\"\"\"

Respond in this JSON format:
{{
  "subject": "...",
  "topic": "..."
}}
"""

    response = call_openai_model(
        role="classifier",
        prompt=prompt,
        model_name=model_name,
        effort="medium"
    )

    if cost_tracker:
        safe_log_cost(
            cost_tracker,
            {"provider": "openai", "model_name": model_name},
            response.get("tokens_prompt", 0),
            response.get("tokens_completion", 0),
            raw_prompt=prompt,
            raw_output=response.get("output", "")
        )

    if not response or "output" not in response:
        raise ModelError("Classifier LLM returned no usable output", model_name=model_name, provider="openai")

    parsed = safe_json_parse(response["output"])
    return parsed.get("subject", "Unknown"), parsed.get("topic", "Unknown")
