"""
Main similarity scoring interface.

This module provides the primary interface for similarity checking,
combining web search and LLM-based similarity evaluation.
"""

import logging
from typing import Any, Dict

from utils.config_manager import get_config_manager

from .similarity_agent import create_similarity_agent
from .tavily_search import query_tavily_search

# Get logger for this module
logger = logging.getLogger(__name__)


def score_similarity(problem_text: str, use_search: bool = None) -> Dict[str, Any]:
    """
    Main interface: retrieves top internet matches and scores similarity.

    Args:
        problem_text: The math problem to check for similarity
        use_search: Whether to use web search. If None, uses config setting

    Returns:
        Dict containing similarity score and match details
    """
    config_manager = get_config_manager()

    # Check if similarity search is enabled
    if use_search is None:
        use_search = config_manager.get("use_search", False)

    if not use_search:
        logger.info("Similarity search disabled, returning zero similarity")
        return {
            "similarity_score": 0.0,
            "top_matches": [],
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "latency": 0.0,
        }

    try:
        # Retrieve documents from web search
        logger.info("Retrieving documents for similarity check")
        retrieved_docs = query_tavily_search(problem_text)

        if not retrieved_docs:
            logger.info("No documents retrieved, returning zero similarity")
            return {
                "similarity_score": 0.0,
                "top_matches": [],
                "tokens_prompt": 0,
                "tokens_completion": 0,
                "latency": 0.0,
            }

        # Create similarity agent and evaluate
        similarity_agent = create_similarity_agent()
        result = similarity_agent.evaluate_similarity(problem_text, retrieved_docs)

        logger.info(
            f"Similarity check completed: score={result.get('similarity_score', 0.0):.3f}"
        )
        return result

    except Exception as e:
        logger.error(f"Similarity check failed: {str(e)}")
        # Return safe defaults on error
        return {
            "similarity_score": 0.0,
            "top_matches": [],
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "latency": 0.0,
            "error": str(e),
        }
