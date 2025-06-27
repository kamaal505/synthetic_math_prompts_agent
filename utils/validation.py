def assert_valid_model_config(role: str, config: dict):
    if not isinstance(config, dict):
        raise ValueError(f"{role.capitalize()} config must be a dictionary.")
    if not config.get("provider"):
        raise ValueError(f"Missing 'provider' in {role} model config.")
    if not config.get("model_name"):
        raise ValueError(f"Missing 'model_name' in {role} model config.")
