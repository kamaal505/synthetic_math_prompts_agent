from unittest.mock import MagicMock, patch

import pytest

from core.orchestration.evaluate_target_model import model_attempts_answer


@patch("core.orchestration.evaluate_target_model._get_openai_client")
def test_model_attempts_answer_openai(mock_get_openai_client):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "x = 2"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20

    mock_client.chat.completions.create.return_value = mock_response
    mock_get_openai_client.return_value = mock_client

    result = model_attempts_answer(
        "x + 1 = 3", {"provider": "openai", "model_name": "gpt-4.1"}
    )

    assert result["output"] == "x = 2"
    assert result["tokens_prompt"] == 10
    assert result["tokens_completion"] == 20


@patch("core.orchestration.evaluate_target_model.genai")
def test_model_attempts_answer_gemini(mock_genai):
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "x = 5"
    mock_genai.GenerativeModel.return_value = mock_model

    result = model_attempts_answer(
        "2x + 1 = 11", {"provider": "gemini", "model_name": "gemini-2.5-pro"}
    )

    assert result["output"] == "x = 5"
    assert result["tokens_prompt"] == 0
    assert result["tokens_completion"] == 0
