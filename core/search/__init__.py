"""
Core search module for similarity checking and web search functionality.

This module provides functionality to check if generated math problems are
similar to existing problems on the internet, helping ensure novelty.
"""

from .search_similarity import score_similarity
from .similarity_agent import SimilarityAgent
from .tavily_search import query_tavily_search

__all__ = [
    "score_similarity",
    "SimilarityAgent",
    "query_tavily_search",
]
