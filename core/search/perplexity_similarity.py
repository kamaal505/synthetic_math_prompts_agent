import requests
import logging
import json
from typing import Dict, Any
from utils.config_manager import get_config_manager
from utils.exceptions import APIError
from utils.json_utils import safe_json_parse
from utils.cost_estimation import safe_log_cost

logger = logging.getLogger(__name__)

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

SYSTEM_PROMPT = """
You are a math question similarity evaluator.

Given a synthetic math problem and a list of real math forum questions (including their full question content), compare them and return a cosine-style similarity score from 0.0 (completely different) to 1.0 (identical in content or approach).

For each internet question, consider both the title and the content. Focus on whether the type of math object, structure of reasoning, and problem goal are similar.

Provide individual scores for each match and an overall aggregated score.

Respond with JSON in this format:
{
  "similarity_score": float,
  "matches": [
    {"title": str, "url": str, "similarity": float, "source": str}
  ]
}
"""

def query_similarity_via_perplexity(problem_text: str, **kwargs) -> Dict[str, Any]:
    config = get_config_manager()
    api_key = config.get_api_key("perplexity")

    if not api_key:
        raise APIError("Missing PERPLEXITY_API_KEY", api_name="Perplexity")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Just pass the problem; Perplexity does search internally
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": problem_text}
        ],
        "stream": False
    }

    try:
        response = requests.post(PERPLEXITY_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"Perplexity API request failed: {str(e)}")
        raise APIError("Perplexity API request failed", api_name="Perplexity")

    try:
        response_text = data.get("choices", [])[0]["message"]["content"]
        logger.debug(f"Raw Perplexity response:\n{response_text}")
        parsed = safe_json_parse(response_text)
        # Estimate token usage (Perplexity does not return this)
        estimated_prompt_tokens = len(problem_text) // 4
        estimated_output_tokens = len(response_text) // 4

        # Log cost using safe_log_cost (if a CostTracker is passed via kwargs)
        if "cost_tracker" in kwargs:
            safe_log_cost(
                kwargs["cost_tracker"],
                model_config={"provider": "perplexity", "model_name": "sonar-pro"},
                tokens_prompt=estimated_prompt_tokens,
                tokens_completion=estimated_output_tokens,
                raw_prompt=problem_text,
                raw_output=response_text,
            )

        return {
            "similarity_score": parsed.get("similarity_score", 0.0),
            "top_matches": parsed.get("matches", []),
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "latency": 0.0
        }
    except Exception as e:
        logger.error(f"Failed to parse Perplexity similarity response: {str(e)}")
        return {
            "similarity_score": 0.0,
            "top_matches": [],
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "latency": 0.0,
            "error": "Parsing failed"
        }
