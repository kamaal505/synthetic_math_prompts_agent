from core.llm.llm_dispatch import call_engineer, call_checker, call_target_model

def test_dispatch_engineer_openai_runs():
    cfg = {"provider": "openai", "model_name": "o3"}
    result = call_engineer("Algebra", "Linear", None, cfg)
    assert isinstance(result["hints"], dict)
