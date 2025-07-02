import pytest
from utils.validation import assert_valid_model_config
from utils.exceptions import ValidationError

def test_invalid_model_config_raises():
    with pytest.raises(ValidationError) as exc:
        assert_valid_model_config("engineer", {"provider": "openai"})
    assert "model_name" in str(exc.value)