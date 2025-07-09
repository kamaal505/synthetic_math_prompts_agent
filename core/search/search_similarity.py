from typing import Dict, Any
from core.search.perplexity_similarity import query_similarity_via_perplexity

def score_similarity(problem_text: str, use_search: bool = None, **kwargs) -> Dict[str, Any]:
    return query_similarity_via_perplexity(problem_text, **kwargs)
