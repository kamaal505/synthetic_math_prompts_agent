from utils.exceptions import ValidationError


def assert_valid_model_config(role: str, config: dict):
    if not isinstance(config, dict):
        raise ValidationError(f"{role.capitalize()} config must be a dictionary.")
    if not config.get("provider"):
        raise ValidationError(
            f"Missing 'provider' in {role} model config.", field="provider"
        )
    if not config.get("model_name"):
        raise ValidationError(
            f"Missing 'model_name' in {role} model config.", field="model_name"
        )
