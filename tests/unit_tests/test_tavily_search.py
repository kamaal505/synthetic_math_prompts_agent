from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError, RequestException

from core.search.tavily_search import query_tavily_search, sanitize_query
from utils.exceptions import APIError


def test_sanitize_query_removes_unicode_and_whitespace():
    raw = "x² + y² = z²\n\nThis is a test.\tExtra space.\n"
    cleaned = sanitize_query(raw)
    assert "²" not in cleaned
    assert "\n" not in cleaned
    assert "\t" not in cleaned
    assert "  " not in cleaned


@patch("core.search.tavily_search.get_config_manager")
@patch("core.search.tavily_search.requests.post")
def test_query_tavily_search_filters_results(mock_post, mock_get_config_manager):
    # Mock config manager
    mock_config_manager = MagicMock()
    mock_config_manager.get_api_key.return_value = "mock-key"
    mock_get_config_manager.return_value = mock_config_manager

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "url": "https://math.stackexchange.com/q1",
                "title": "Q1",
                "content": "mathy",
            },
            {
                "url": "https://reddit.com/r/math/q2",
                "title": "Q2",
                "content": "reddit math",
            },
            {"url": "https://example.com/q3", "title": "Q3", "content": "not allowed"},
        ]
    }
    mock_post.return_value = mock_response

    results = query_tavily_search("x + 2 = 4")

    assert len(results) == 2
    assert all(res["source"] in {"math.stackexchange", "reddit"} for res in results)


@patch("core.search.tavily_search.get_config_manager")
@patch("core.search.tavily_search.time.sleep", return_value=None)
@patch("core.search.tavily_search.requests.post")
def test_query_tavily_search_retries_on_request_exception(
    mock_post, _, mock_get_config_manager
):
    # Mock config manager
    mock_config_manager = MagicMock()
    mock_config_manager.get_api_key.return_value = "mock-key"
    mock_get_config_manager.return_value = mock_config_manager

    # Fail twice, then succeed
    mock_post.side_effect = [
        RequestException("Timeout"),
        RequestException("Timeout again"),
        MagicMock(status_code=200, json=lambda: {"results": []}),
    ]

    results = query_tavily_search("problem?", retries=3)
    assert isinstance(results, list)


@patch("core.search.tavily_search.get_config_manager")
@patch("core.search.tavily_search.time.sleep", return_value=None)
@patch("core.search.tavily_search.requests.post")
def test_query_tavily_search_retries_on_400_http_error(
    mock_post, _, mock_get_config_manager
):
    # Mock config manager
    mock_config_manager = MagicMock()
    mock_config_manager.get_api_key.return_value = "mock-key"
    mock_get_config_manager.return_value = mock_config_manager

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError(
        response=MagicMock(status_code=400)
    )
    mock_post.return_value = mock_response

    with pytest.raises(APIError, match="Tavily request failed after all retries"):
        query_tavily_search("problem?", retries=2)


@patch("core.search.tavily_search.get_config_manager")
@patch("core.search.tavily_search.requests.post")
def test_query_tavily_search_raises_on_invalid_json(mock_post, mock_get_config_manager):
    # Mock config manager
    mock_config_manager = MagicMock()
    mock_config_manager.get_api_key.return_value = "mock-key"
    mock_get_config_manager.return_value = mock_config_manager

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Not JSON")
    mock_post.return_value = mock_response

    with pytest.raises(APIError, match="Invalid JSON returned from Tavily"):
        query_tavily_search("2x + 3 = 5")
