import pytest

@pytest.fixture
def dummy_config():
    return {
        "taxonomy": {"Algebra": ["Linear Equations"]},
        "engineer_model": {"provider": "openai", "model_name": "o3"},
        "checker_model": {"provider": "openai", "model_name": "o3"},
        "target_model": {"provider": "openai", "model_name": "o3"},
        "use_search": False
    }
