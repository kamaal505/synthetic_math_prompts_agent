from unittest.mock import patch

from core.search.search_similarity import score_similarity


@patch("core.search.similarity_agent.create_similarity_agent")
@patch("core.search.tavily_search.query_tavily_search")
def test_score_similarity_returns_shape(mock_query, mock_create_agent):
    mock_query.return_value = [{"title": "Mock", "content": "Example question"}]

    # Mock the similarity agent
    mock_agent = mock_create_agent.return_value
    mock_agent.score_similarity.return_value = {
        "similarity_score": 0.92,
        "top_matches": [{"title": "Mock", "content": "Example"}],
        "tokens_prompt": 10,
        "tokens_completion": 20,
        "raw_output": "LLM said it's similar",
    }

    result = score_similarity("What is 2 + 2?")

    assert isinstance(result, dict)
    assert "similarity_score" in result
    assert "top_matches" in result
    assert isinstance(result["top_matches"], list)
