"""
Agent-based architecture for the synthetic math prompts system.

This module defines the base Agent class and specialized agent classes for
different roles in the problem generation pipeline: EngineerAgent, CheckerAgent,
and TargetAgent.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.llm.llm_client import get_llm_client
from utils.config_manager import get_config_manager
from utils.exceptions import ModelError, ValidationError
from utils.json_utils import safe_json_parse
from utils.system_messages import CHECKER_MESSAGE, ENGINEER_MESSAGE
from utils.taxonomy import get_topic_info
from utils.prompt_examples import build_enhanced_prompt_context
from core.checker.cas_validator import verify_with_cas

# Get logger for this module
logger = logging.getLogger(__name__)


class Agent(ABC):
    """
    Base class for all agents in the system.

    Each agent encapsulates specific logic for interacting with LLM models
    and maintains its own configuration and system prompts.
    """

    def __init__(self, agent_type: str, config_key: str):
        """
        Initialize the base agent.

        Args:
            agent_type: Type of agent (e.g., 'engineer', 'checker', 'target')
            config_key: Configuration key for this agent's model settings
        """
        self.agent_type = agent_type
        self.config_key = config_key
        self.config_manager = get_config_manager()
        self.llm_client = get_llm_client()
        self.logger = logging.getLogger(f"{__name__}.{agent_type}")

        # Load model configuration
        self.model_config = self.config_manager.get(config_key, {})
        self.provider = self.model_config.get("provider", "openai")
        self.model_name = self.model_config.get("model_name", "gpt-4")

        self.logger.info(
            f"Initialized {agent_type} agent with {self.provider} {self.model_name}"
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    def call_model(
        self, prompt: str, temperature: float = 1.0, **kwargs
    ) -> Dict[str, Any]:
        """
        Call the LLM model for this agent.

        Args:
            prompt: The prompt to send to the model
            temperature: Temperature setting for the model
            **kwargs: Additional model parameters

        Returns:
            Dict containing model response and metadata
        """
        try:
            result = self.llm_client.call_model(
                provider=self.provider,
                model_name=self.model_name,
                prompt=prompt,
                temperature=temperature,
                **kwargs,
            )

            self.logger.debug(
                f"{self.agent_type} model call completed "
                f"(tokens: {result.get('tokens_prompt', 0)}→{result.get('tokens_completion', 0)})"
            )

            return result

        except Exception as e:
            self.logger.error(f"{self.agent_type} model call failed: {str(e)}")
            raise


class EngineerAgent(Agent):
    """
    Agent responsible for generating math problems.

    The EngineerAgent creates problems with hints based on subject/topic
    specifications and ensures they meet quality criteria.
    """

    def __init__(self):
        """Initialize the EngineerAgent."""
        super().__init__("engineer", "engineer_model")

    def get_system_prompt(self, difficulty_level: Optional[str] = None) -> str:
        """Get the enhanced system prompt for problem generation."""
        base_prompt = ENGINEER_MESSAGE
        
        # Add difficulty-specific instructions
        if difficulty_level:
            difficulty_instructions = {
                "High School": "Focus on problems that require multi-step reasoning and conceptual understanding beyond basic computation.",
                "Undergraduate": "Create problems that combine multiple mathematical concepts and require theoretical insight.",
                "Graduate": "Generate problems that test deep theoretical understanding and advanced mathematical techniques.",
                "Research": "Develop problems that push the boundaries of standard methods and require novel approaches."
            }
            
            if difficulty_level in difficulty_instructions:
                base_prompt += f"\n\nDifficulty Level: {difficulty_level}\n{difficulty_instructions[difficulty_level]}"
        
        return base_prompt

    def generate(
        self,
        subject: str,
        topic: str,
        seed_prompt: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a math problem with hints using enhanced prompt engineering.

        Args:
            subject: The math subject (e.g., 'Algebra', 'Calculus')
            topic: The specific topic within the subject
            seed_prompt: Optional seed/inspiration for the problem
            difficulty_level: Optional difficulty level specification
            **kwargs: Additional generation parameters

        Returns:
            Dict containing:
                - subject: The math subject
                - topic: The topic
                - problem: The problem statement
                - answer: The correct answer
                - hints: Dictionary of step-by-step hints
                - difficulty_level: The difficulty level used
                - topic_description: Description of the topic
                - tokens_prompt: Input tokens used
                - tokens_completion: Output tokens used
                - raw_output: Raw model output
                - raw_prompt: Raw prompt sent to model

        Raises:
            ValidationError: If the generated problem is invalid
            ModelError: If the model call fails
        """
        self.logger.info(f"Generating problem for {subject} - {topic} (level: {difficulty_level})")

        # Get topic information from enhanced taxonomy
        taxonomy_data = self.config_manager.get("taxonomy", {})
        topic_info = get_topic_info(taxonomy_data, subject, topic)
        
        # Use topic info to determine difficulty level if not provided
        if not difficulty_level and topic_info:
            difficulty_level = topic_info.get("level")
            
        topic_description = topic_info.get("description")

        # Build enhanced context using few-shot examples and adversarial techniques
        enhanced_context = build_enhanced_prompt_context(
            subject=subject,
            topic=topic,
            difficulty_level=difficulty_level,
            topic_description=topic_description
        )

        # Build user prompt with enhanced context
        user_prompt_parts = [
            f"Generate a math problem in {subject} under the topic '{topic}' with hints."
        ]
        
        if difficulty_level:
            user_prompt_parts.append(f"The problem should be at {difficulty_level} level.")
            
        if topic_description:
            user_prompt_parts.append(f"Topic context: {topic_description}")

        if seed_prompt:
            user_prompt_parts.append(f"Use this real-world example as inspiration:\n{seed_prompt}")
            
        # Add enhanced context
        if enhanced_context:
            user_prompt_parts.append(f"\n{enhanced_context}")

        user_prompt = "\n".join(user_prompt_parts)

        # Combine system and user prompts
        system_prompt = self.get_system_prompt(difficulty_level)
        full_prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"

        # Call the model
        response = self.call_model(full_prompt, **kwargs)

        # Parse the JSON response
        try:
            parsed_data = safe_json_parse(response["output"])
        except Exception as e:
            self.logger.error(f"Failed to parse engineer response as JSON: {str(e)}")
            raise ValidationError(
                f"Invalid JSON response from engineer: {str(e)}", field="response"
            )

        # Validate the response structure
        required_fields = ["subject", "topic", "problem", "answer", "hints"]
        for field in required_fields:
            if field not in parsed_data:
                raise ValidationError(f"Missing required field: {field}", field=field)

        # Validate hints
        hints = parsed_data.get("hints", {})
        if not isinstance(hints, dict) or len(hints) < 3:
            raise ValidationError("Invalid or too few hints returned.", field="hints")

        self.logger.info(f"Successfully generated {difficulty_level or 'standard'} level problem with {len(hints)} hints")

        # Return complete result
        return {
            "subject": parsed_data["subject"],
            "topic": parsed_data["topic"],
            "problem": parsed_data["problem"],
            "answer": parsed_data["answer"],
            "hints": hints,
            "difficulty_level": difficulty_level,
            "topic_description": topic_description,
            "tokens_prompt": response.get("tokens_prompt", 0),
            "tokens_completion": response.get("tokens_completion", 0),
            "raw_output": response.get("output", ""),
            "raw_prompt": full_prompt,
        }


class CheckerAgent(Agent):
    """
    Agent responsible for validating math problems and checking answer equivalence.

    The CheckerAgent ensures problems meet quality standards and can verify
    if different answer formats are mathematically equivalent.
    """

    def __init__(self):
        """Initialize the CheckerAgent."""
        super().__init__("checker", "checker_model")

    def get_system_prompt(self) -> str:
        """Get the system prompt for problem validation."""
        return CHECKER_MESSAGE

    def validate(
        self, problem_data: Dict[str, Any], mode: str = "initial", **kwargs
    ) -> Dict[str, Any]:
        """
        Validate a problem or perform enhanced answer equivalence check.

        Args:
            problem_data: Dictionary containing problem information
            mode: Validation mode ('initial' or 'equivalence_check')
            **kwargs: Additional validation parameters

        Returns:
            Dict containing:
                - valid: Boolean indicating if problem is valid
                - reason: Explanation of validation result
                - corrected_hints: Optional corrected hints if needed
                - equivalence_confidence: Confidence score for equivalence (0-1)
                - tokens_prompt: Input tokens used
                - tokens_completion: Output tokens used
                - raw_output: Raw model output
                - raw_prompt: Raw prompt sent to model

        Raises:
            ValidationError: If mode is invalid
            ModelError: If the model call fails
        """
        self.logger.info(f"Validating problem in {mode} mode")

        # Prepare user prompt based on mode
        if mode == "initial":
            user_prompt = {
                "problem": problem_data["problem"],
                "answer": problem_data["answer"],
                "hints": problem_data["hints"],
                "validation_type": "initial"
            }
        elif mode == "equivalence_check":
            user_prompt = {
                "problem": problem_data["problem"],
                "true_answer": problem_data["answer"],
                "model_answer": problem_data["target_model_answer"],
                "validation_type": "equivalence_check"
            }
            
            # Add enhanced equivalence checking instructions
            user_prompt["equivalence_instructions"] = [
                "Check for mathematical equivalence, not just textual similarity",
                "Consider different valid representations (fractions, decimals, expressions)",
                "Account for rounding differences and approximations",
                "Verify algebraic equivalence for expressions",
                "Check if answers represent the same mathematical concept",
                "Provide a confidence score (0-1) for the equivalence assessment"
            ]
        else:
            raise ValidationError(f"Unknown validation mode: {mode}", field="mode")

        # Build enhanced system prompt for equivalence checking
        if mode == "equivalence_check":
            enhanced_system_prompt = self.get_system_prompt() + """

ENHANCED EQUIVALENCE CHECKING:
When checking answer equivalence, consider these scenarios:
1. Algebraic equivalence: 2x + 4 ≡ 2(x + 2)
2. Numerical equivalence: 0.5 ≡ 1/2 ≡ 50%
3. Trigonometric equivalence: sin²(x) + cos²(x) ≡ 1
4. Set equivalence: {1,2,3} ≡ {3,1,2}
5. Approximation tolerance: π ≈ 3.14159 (within reasonable precision)
6. Multiple valid forms: x = 2 ≡ x - 2 = 0

Provide a confidence score from 0 to 1:
- 1.0: Definitely equivalent
- 0.8-0.9: Very likely equivalent (minor formatting differences)
- 0.6-0.7: Probably equivalent (requires verification)
- 0.3-0.5: Possibly equivalent (significant differences)
- 0.0-0.2: Not equivalent

Include "equivalence_confidence" in your JSON response.
"""
            system_prompt = enhanced_system_prompt
        else:
            system_prompt = self.get_system_prompt()

        # Build full prompt
        full_prompt = f"{system_prompt.strip()}\n\n{json.dumps(user_prompt, indent=2)}"

        # Call the model with lower temperature for more consistent validation
        response = self.call_model(full_prompt, temperature=0.2, **kwargs)

        # Parse the JSON response
        try:
            parsed_result = safe_json_parse(response["output"])
        except Exception as e:
            self.logger.error(f"Failed to parse checker response as JSON: {str(e)}")
            raise ValidationError(
                f"Invalid JSON response from checker: {str(e)}", field="response"
            )

        # Validate response structure
        if "valid" not in parsed_result:
            raise ValidationError(
                "Checker response missing 'valid' field", field="valid"
            )

        is_valid = parsed_result.get("valid", False)
        reason = parsed_result.get("reason", "No reason provided")
        equivalence_confidence = parsed_result.get("equivalence_confidence", 0.0)

        # Perform optional CAS verification for equivalence checks
        cas_result = None
        if mode == "equivalence_check":
            try:
                cas_result = verify_with_cas(
                    problem=problem_data["problem"],
                    given_answer=problem_data["answer"],
                    computed_answer=problem_data["target_model_answer"]
                )
                
                # If CAS verification is available and confident, use it to enhance the result
                if cas_result.get("verified") and cas_result.get("confidence", 0) > 0.8:
                    if not is_valid:  # LLM said invalid, but CAS says valid
                        self.logger.info(f"CAS verification overrides LLM: answers are equivalent")
                        is_valid = True
                        reason = f"CAS verification: {cas_result['reason']} (LLM disagreed)"
                        equivalence_confidence = max(equivalence_confidence, cas_result.get("confidence", 0.9))
                elif cas_result.get("verified") == False and cas_result.get("confidence", 0) > 0.8:
                    if is_valid:  # LLM said valid, but CAS says invalid
                        self.logger.info(f"CAS verification overrides LLM: answers are not equivalent")
                        is_valid = False
                        reason = f"CAS verification: {cas_result['reason']} (LLM disagreed)"
                        equivalence_confidence = min(equivalence_confidence, 1.0 - cas_result.get("confidence", 0.9))
                        
            except Exception as e:
                self.logger.debug(f"CAS verification failed: {str(e)}")

        # Log detailed validation result
        if mode == "equivalence_check":
            cas_info = f" [CAS: {cas_result.get('method', 'N/A')}]" if cas_result else ""
            self.logger.info(
                f"Equivalence check: {'VALID' if is_valid else 'INVALID'} "
                f"(confidence: {equivalence_confidence:.2f}) - {reason}{cas_info}"
            )
        else:
            self.logger.info(
                f"Validation result: {'VALID' if is_valid else 'INVALID'} - {reason}"
            )

        result = {
            "valid": is_valid,
            "reason": reason,
            "corrected_hints": parsed_result.get("corrected_hints", {}),
            "equivalence_confidence": equivalence_confidence,
            "tokens_prompt": response.get("tokens_prompt", 0),
            "tokens_completion": response.get("tokens_completion", 0),
            "raw_output": response.get("output", ""),
            "raw_prompt": full_prompt,
        }
        
        # Add CAS verification results if available
        if cas_result:
            result["cas_verification"] = cas_result
            
        return result


class TargetAgent(Agent):
    """
    Agent that attempts to solve math problems to test their difficulty.

    The TargetAgent represents the model being tested and should fail
    on appropriately challenging problems.
    """

    def __init__(self):
        """Initialize the TargetAgent."""
        super().__init__("target", "target_model")

    def get_system_prompt(self) -> str:
        """Get the system prompt for problem solving."""
        return "You are a math student trying to solve the following problem. Only provide the final answer. No explanation."

    def solve(self, problem_text: str, **kwargs) -> Dict[str, Any]:
        """
        Attempt to solve a math problem.

        Args:
            problem_text: The problem statement to solve
            **kwargs: Additional solving parameters

        Returns:
            Dict containing:
                - output: The model's answer attempt
                - tokens_prompt: Input tokens used
                - tokens_completion: Output tokens used
                - latency: Response time in seconds

        Raises:
            ModelError: If the model call fails
        """
        self.logger.info("Attempting to solve problem")

        # Build full prompt
        full_prompt = f"{self.get_system_prompt().strip()}\n\n{problem_text.strip()}"

        # Call model with deterministic settings (temperature=0) for consistent results
        response = self.call_model(full_prompt, temperature=0.0, **kwargs)

        answer = response.get("output", "").strip()
        self.logger.info(f"Target model provided answer: {answer[:100]}...")

        return {
            "output": answer,
            "tokens_prompt": response.get("tokens_prompt", 0),
            "tokens_completion": response.get("tokens_completion", 0),
            "latency": response.get("latency", 0.0),
        }


# Factory functions for easy agent creation
def create_engineer_agent() -> EngineerAgent:
    """Create and return an EngineerAgent instance."""
    return EngineerAgent()


def create_checker_agent() -> CheckerAgent:
    """Create and return a CheckerAgent instance."""
    return CheckerAgent()


def create_target_agent() -> TargetAgent:
    """Create and return a TargetAgent instance."""
    return TargetAgent()
