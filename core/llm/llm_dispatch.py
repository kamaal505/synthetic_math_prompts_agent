from core.checker.validate_prompt import validate_problem
from core.engineer.generate_prompt import generate_full_problem
from core.orchestration.evaluate_target_model import model_attempts_answer


def call_engineer(subject, topic, seed_prompt, config):
    """
    Wrapper for engineer model call. Returns problem + token usage.
    """
    result = generate_full_problem(
        seed=seed_prompt,
        subject=subject,
        topic=topic,
        provider=config["provider"],
        model_name=config["model_name"],
    )
    return result


def call_checker(core_problem, config, mode="initial"):
    """
    Wrapper for checker model call. Returns validation result + token usage.
    """
    result = validate_problem(
        core_problem,
        mode=mode,
        provider=config["provider"],
        model_name=config["model_name"],
    )
    return result


def call_target_model(problem_text, config):
    """
    Wrapper for target model call. Returns answer + token usage.
    """
    result = model_attempts_answer(problem_text, model_config=config)
    return result
