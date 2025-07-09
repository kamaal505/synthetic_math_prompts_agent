"""
Core search module for similarity checking and web search functionality.

This module provides functionality to check if generated math problems are
similar to existing problems on the internet, helping ensure novelty.
"""

from .search_similarity import score_similarity

__all__ = [
    "score_similarity",
]
