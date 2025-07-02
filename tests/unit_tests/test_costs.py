from utils.costs import CostTracker
from utils.cost_estimation import safe_log_cost

def test_openai_cost_logging():
    tracker = CostTracker()
    cfg = {"provider": "openai", "model_name": "gpt-4o"}
    tracker.log(cfg, 1000, 500)

    stats = tracker.get_breakdown()["openai:gpt-4o"]
    assert stats["input_tokens"] == 1000
    assert stats["output_tokens"] == 500

def test_gemini_cost_estimation():
    tracker = CostTracker()
    cfg = {
        "provider": "gemini",
        "model_name": "gemini-2.5-pro",
        "raw_prompt": "a" * 400,
        "raw_output": "b" * 800,
    }
    tracker.log(cfg, 0, 0)
    stats = tracker.get_breakdown()["gemini:gemini-2.5-pro"]

    assert stats["input_tokens"] == 100
    assert stats["output_tokens"] == 200

def test_safe_log_cost_wraps_successfully():
    tracker = CostTracker()
    cfg = {"provider": "openai", "model_name": "gpt-4.1"}
    safe_log_cost(tracker, cfg, 50, 100, raw_prompt="q", raw_output="a")
    assert "openai:gpt-4.1" in tracker.get_breakdown()
