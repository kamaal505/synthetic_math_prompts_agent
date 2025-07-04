"""
Centralized LLM dispatch using the new agent-based architecture.

This module provides wrapper functions that use the new agent classes
while maintaining backward compatibility with existing code.
"""

import logging
from typing import Any, Dict

from core.agents import create_checker_agent, create_engineer_agent, create_target_agent
from utils.config_manager import get_config_manager

# Get logger for this module
logger = logging.getLogger(__name__)


def call_engineer(
    subject: str,
    topic: str,
    seed_prompt: str,
    config: Dict[str, Any],
    difficulty_level: str = None,
) -> Dict[str, Any]:
    """
    Wrapper for engineer model call using EngineerAgent.

    Args:
        subject: The math subject
        topic: The topic within the subject
        seed_prompt: Optional seed/inspiration for the problem
        config: Model configuration (maintained for compatibility)
        difficulty_level: Optional difficulty level for enhanced prompting

    Returns:
        Problem generation result with token usage
    """
    # Update ConfigManager with the request's engineer model configuration
    config_manager = get_config_manager()
    config_manager.set("engineer_model.provider", config.get("provider", "openai"))
    config_manager.set("engineer_model.model_name", config.get("model_name", "gpt-4"))

    engineer_agent = create_engineer_agent()
    result = engineer_agent.generate(
        subject=subject,
        topic=topic,
        seed_prompt=seed_prompt,
        difficulty_level=difficulty_level,
    )

    return result


def call_checker(
    core_problem: Dict[str, Any], config: Dict[str, Any], mode: str = "initial"
) -> Dict[str, Any]:
    """
    Wrapper for checker model call using CheckerAgent.

    Args:
        core_problem: Problem data to validate
        config: Model configuration (maintained for compatibility)
        mode: Validation mode ('initial' or 'equivalence_check')

    Returns:
        Validation result with token usage
    """
    # Update ConfigManager with the request's checker model configuration
    config_manager = get_config_manager()
    config_manager.set("checker_model.provider", config.get("provider", "openai"))
    config_manager.set("checker_model.model_name", config.get("model_name", "gpt-4"))

    checker_agent = create_checker_agent()
    result = checker_agent.validate(problem_data=core_problem, mode=mode)

    return result


def call_target_model(problem_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper for target model call using TargetAgent.

    Args:
        problem_text: The problem statement to solve
        config: Model configuration (maintained for compatibility)

    Returns:
        Target model answer with token usage
    """
    # Update ConfigManager with the request's target model configuration
    config_manager = get_config_manager()
    config_manager.set("target_model.provider", config.get("provider", "openai"))
    config_manager.set("target_model.model_name", config.get("model_name", "gpt-4"))

    target_agent = create_target_agent()
    result = target_agent.solve(problem_text=problem_text)

    return result
