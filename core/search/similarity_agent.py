"""
Similarity agent for evaluating math problem similarity using LLM.

This module provides an agent-based approach to similarity checking,
integrating with the centralized LLM client and configuration system.
"""

import json
import logging
from typing import Any, Dict, List

from core.llm.llm_client import get_llm_client
from utils.config_manager import get_config_manager
from utils.exceptions import ModelError
from utils.json_utils import safe_json_parse

# Get logger for this module
logger = logging.getLogger(__name__)


class SimilarityAgent:
    """
    Agent responsible for evaluating similarity between math problems.

    Uses LLM to compare synthetic problems against real-world math questions
    and provide similarity scores and analysis.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        """
        Initialize the SimilarityAgent.

        Args:
            model_name: The model to use for similarity evaluation
        """
        self.model_name = model_name
        self.provider = "openai"  # Default to OpenAI for similarity checking
        self.config_manager = get_config_manager()
        self.llm_client = get_llm_client()
        self.logger = logging.getLogger(f"{__name__}.similarity")

        self.logger.info(
            f"Initialized similarity agent with {self.provider} {self.model_name}"
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for similarity evaluation."""
        return """You are a math question similarity evaluator.

Given a synthetic math problem and a list of real math forum questions (including their full question content), compare them and return a cosine-style similarity score from 0.0 (completely different) to 1.0 (identical in content or approach).

For each internet question, consider both the title and the content. Focus on whether the type of math object, structure of reasoning, and problem goal are similar.

Provide individual scores for each match and an overall aggregated score.

Respond with JSON in this format:
{
  "similarity_score": float,
  "matches": [
    {"title": str, "url": str, "similarity": float, "source": str}
  ]
}"""

    def evaluate_similarity(
        self, problem_text: str, retrieved_docs: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate similarity between a problem and retrieved documents.

        Args:
            problem_text: The synthetic math problem to evaluate
            retrieved_docs: List of retrieved documents from web search
            **kwargs: Additional evaluation parameters

        Returns:
            Dict containing:
                - similarity_score: Overall similarity score (0.0-1.0)
                - top_matches: List of top matching documents with scores
                - tokens_prompt: Input tokens used
                - tokens_completion: Output tokens used
                - latency: Response time in seconds

        Raises:
            ModelError: If the model call fails
        """
        self.logger.info(
            f"Evaluating similarity for problem against {len(retrieved_docs)} documents"
        )

        # Prepare the payload
        payload = {"problem": problem_text, "related": retrieved_docs}

        # Build the full prompt
        system_prompt = self.get_system_prompt()
        user_input = f"User Input:\n{json.dumps(payload, indent=2, ensure_ascii=False)}"
        full_prompt = f"{system_prompt}\n\n{user_input}"

        try:
            # Call the model with low effort for cost efficiency
            response = self.llm_client.call_model(
                provider=self.provider,
                model_name=self.model_name,
                prompt=full_prompt,
                temperature=0.3,  # Lower temperature for more consistent evaluation
                effort="low" if self.provider == "openai" else None,
                **kwargs,
            )

            # Parse the JSON response
            try:
                parsed_result = safe_json_parse(response["output"])
            except Exception as e:
                self.logger.error(
                    f"Failed to parse similarity response as JSON: {str(e)}"
                )
                # Return default values if parsing fails
                return {
                    "similarity_score": 0.0,
                    "top_matches": [],
                    "tokens_prompt": response.get("tokens_prompt", 0),
                    "tokens_completion": response.get("tokens_completion", 0),
                    "latency": response.get("latency", 0.0),
                }

            similarity_score = parsed_result.get("similarity_score", 0.0)
            matches = parsed_result.get("matches", [])

            self.logger.info(
                f"Similarity evaluation completed: score={similarity_score:.3f}, "
                f"matches={len(matches)}"
            )

            return {
                "similarity_score": similarity_score,
                "top_matches": matches,
                "tokens_prompt": response.get("tokens_prompt", 0),
                "tokens_completion": response.get("tokens_completion", 0),
                "latency": response.get("latency", 0.0),
            }

        except Exception as e:
            self.logger.error(f"Similarity evaluation failed: {str(e)}")
            raise ModelError(
                f"Failed to evaluate similarity: {str(e)}",
                model_name=self.model_name,
                provider=self.provider,
            )


def create_similarity_agent(model_name: str = "gpt-4o") -> SimilarityAgent:
    """
    Create and return a SimilarityAgent instance.

    Args:
        model_name: The model to use for similarity evaluation

    Returns:
        Configured SimilarityAgent instance
    """
    return SimilarityAgent(model_name=model_name)
