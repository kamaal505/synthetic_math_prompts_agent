from .tavily_search import query_tavily_search
from .agent import score_with_llm

def score_similarity(problem_text: str) -> dict:
    """
    Main interface: retrieves top internet matches and scores similarity.
    """
    retrieved = query_tavily_search(problem_text)
    return score_with_llm(problem_text, retrieved)
