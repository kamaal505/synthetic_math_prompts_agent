from unittest.mock import patch
from core.engineer.generate_prompt import generate_full_problem


@patch("core.engineer.generate_prompt.call_openai")
def test_generate_full_problem_returns_expected_structure(mock_call_openai):
    mock_call_openai.return_value = {
        "subject": "Algebra",
        "topic": "Linear Equations",
        "problem": "Solve x + 2 = 4",
        "answer": "x = 2",
        "hints": {"step1": "Subtract 2", "step2": "Simplify", "step3": "Solve"},
        "tokens_prompt": 10,
        "tokens_completion": 20,
        "raw_output": "some output",
        "raw_prompt": "some prompt"
    }

    result = generate_full_problem(
        seed=None,
        subject="Algebra",
        topic="Linear Equations",
        provider="openai",
        model_name="o3"
    )

    assert isinstance(result, dict)
    assert "problem" in result and "answer" in result and "hints" in result
    assert isinstance(result["hints"], dict)
