from unittest.mock import MagicMock, patch

from core.llm.llm_dispatch import call_checker, call_engineer, call_target_model


@patch("core.agents.get_llm_client")
def test_dispatch_engineer_openai_runs(mock_get_llm_client):
    # Mock the LLM client
    mock_client = MagicMock()
    mock_client.call_model.return_value = {
        "output": '{"subject": "Algebra", "topic": "Linear", "problem": "Test problem", "answer": "Test answer", "hints": {"hint1": "Test hint 1", "hint2": "Test hint 2", "hint3": "Test hint 3"}}',
        "tokens_prompt": 10,
        "tokens_completion": 20,
    }
    mock_get_llm_client.return_value = mock_client

    cfg = {"provider": "openai", "model_name": "o3"}
    result = call_engineer("Algebra", "Linear", None, cfg)
    assert isinstance(result["hints"], dict)
