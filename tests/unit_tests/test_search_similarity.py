from unittest.mock import patch
from core.search.search_similarity import score_similarity

@patch("core.search.agent.score_with_llm")
@patch("core.search.tavily_search.query_tavily_search")
def test_score_similarity_returns_shape(mock_query, mock_score):
    mock_query.return_value = [{"title": "Mock", "content": "Example question"}]
    mock_score.return_value = {
        "similarity_score": 0.92,
        "top_matches": [{"title": "Mock", "content": "Example"}],
        "tokens_prompt": 10,
        "tokens_completion": 20,
        "raw_output": "LLM said it's similar"
    }

    result = score_similarity("What is 2 + 2?")
    
    assert isinstance(result, dict)
    assert "similarity_score" in result
    assert "top_matches" in result
    assert isinstance(result["top_matches"], list)
