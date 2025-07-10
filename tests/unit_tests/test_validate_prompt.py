from unittest.mock import patch
from core.checker.validate_prompt import validate_problem


@patch("core.checker.validate_prompt.call_openai")
def test_validate_problem_initial_mode(mock_call_openai):
    mock_call_openai.return_value = {
        "valid": True,
        "corrected_hints": None,
        "tokens_prompt": 5,
        "tokens_completion": 10,
        "raw_output": "OK",
        "raw_prompt": "PROMPT"
    }

    problem_data = {
        "problem": "x + 1 = 2",
        "answer": "x = 1",
        "hints": {"1": "Subtract 1", "2": "Solve"}
    }

    result = validate_problem(problem_data, mode="initial", provider="openai", model_name="o3")

    assert result["valid"] is True
    assert "raw_output" in result
    assert "tokens_prompt" in result

@patch("core.checker.validate_prompt.call_openai")
def test_validate_problem_with_corrections(mock_call_openai):
    mock_call_openai.return_value = {
        "valid": True,
        "corrected_hints": {"1": "Subtract 1 from both sides"},
        "tokens_prompt": 5,
        "tokens_completion": 10,
        "raw_output": "OK",
        "raw_prompt": "PROMPT"
    }

    problem_data = {
        "problem": "x + 1 = 2",
        "answer": "x = 1",
        "hints": {"1": "Subtract 1", "2": "Solve"}
    }

    result = validate_problem(problem_data, mode="initial", provider="openai", model_name="o3")

    assert result["valid"] is True
    assert result["corrected_hints"]["1"] == "Subtract 1 from both sides"

