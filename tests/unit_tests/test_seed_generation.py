import pytest
from unittest.mock import patch, MagicMock
from core.orchestration.generate_batch import _generate_and_validate_prompt
from utils.costs import CostTracker

# Sample seed config
@pytest.fixture
def seed_config():
    return {
        "use_seed_data": True,
        "benchmark_name": "AIME",
        "engineer_model": {
            "provider": "openai",
            "model_name": "gpt-4"
        },
        "checker_model": {
            "provider": "openai",
            "model_name": "gpt-4"
        },
        "target_model": {
            "provider": "openai",
            "model_name": "gpt-4"
        }
    }


@patch("core.orchestration.generate_batch.load_benchmark")
@patch("core.orchestration.generate_batch.classify_subject_topic")
@patch("core.orchestration.generate_batch.call_engineer")
@patch("core.orchestration.generate_batch.call_checker")
@patch("core.orchestration.generate_batch.call_target_model")
def test_seed_prompt_accepted(
    mock_target,
    mock_checker,
    mock_engineer,
    mock_classify,
    mock_load,
    seed_config
):
    # Mock seed problem from benchmark
    mock_load.return_value = [{"problem": "Mock seed problem", "answer": "42", "source_id": "2022-A3"}]
    mock_classify.return_value = ("Algebra", "Inequalities")

    # Engineer returns valid generated data
    mock_engineer.return_value = {
        "problem": "Generated problem",
        "answer": "42",
        "hints": {"1": "hint one", "2": "hint two", "3": "hint three"},
        "tokens_prompt": 20,
        "tokens_completion": 50,
        "raw_prompt": "prompt",
        "raw_output": "output"
    }

    # Checker: initial validation = pass, final check = target model failed
    mock_checker.side_effect = [
        {"valid": True, "corrected_hints": None, "tokens_prompt": 10, "tokens_completion": 5},
        {"valid": False, "tokens_prompt": 10, "tokens_completion": 5}
    ]

    # Target model returns incorrect output
    mock_target.return_value = {"output": "Wrong answer", "tokens_prompt": 15, "tokens_completion": 25}

    result_type, data = _generate_and_validate_prompt(seed_config, CostTracker())

    assert result_type == "accepted"
    assert data["problem"] == "Generated problem"
    assert data["reference"] == "AIME:2022-A3"
    assert data["subject"] == "Algebra"
    assert data["topic"] == "Inequalities"
    assert "hints" in data and isinstance(data["hints"], dict)
