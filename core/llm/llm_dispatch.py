from core.engineer.generate_prompt import generate_full_problem
from core.checker.validate_prompt import validate_problem
from core.orchestration.evaluate_target_model import model_attempts_answer


def call_engineer(subject, topic, seed_prompt, config):
    return generate_full_problem(
        seed=seed_prompt,
        subject=subject,
        topic=topic,
        provider=config["provider"],
        model_name=config["model_name"]
    )


def call_checker(core_problem, config, mode="initial"):
    return validate_problem(
        core_problem,
        mode=mode,
        provider=config["provider"],
        model_name=config["model_name"]
    )


def call_target_model(problem_text, config):
    return model_attempts_answer(
        problem_text,
        model_config=config
    )
