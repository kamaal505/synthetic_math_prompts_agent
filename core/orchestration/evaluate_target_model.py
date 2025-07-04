import json
import logging
from typing import Dict

import google.generativeai as genai
import requests
from openai import OpenAI

from utils.config_manager import get_config_manager
from utils.exceptions import APIError, ModelError

# Get logger for this module
logger = logging.getLogger(__name__)

# Initialize clients lazily
_openai_client = None
_gemini_configured = False


def _get_openai_client():
    """Get OpenAI client with lazy initialization."""
    global _openai_client
    if _openai_client is None:
        config_manager = get_config_manager()
        openai_key = config_manager.get_api_key("openai")
        if openai_key:
            _openai_client = OpenAI(api_key=openai_key)
    return _openai_client


def _configure_gemini():
    """Configure Gemini with lazy initialization."""
    global _gemini_configured
    if not _gemini_configured:
        config_manager = get_config_manager()
        gemini_key = config_manager.get_api_key("gemini")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            _gemini_configured = True


def model_attempts_answer(problem: str, model_config: Dict) -> Dict:
    """
    Calls the target model with a math problem and returns its answer along with token usage metadata.

    Args:
        problem (str): The math problem to solve.
        model_config (dict): Contains provider and model_name keys.

    Returns:
        dict:
            {
                "output": str (model's final answer),
                "tokens_prompt": int,
                "tokens_completion": int
            }

    Raises:
        ValueError: If provider is unsupported.
        EnvironmentError: If API key is missing.
        RuntimeError: If request fails.
    """
    provider = model_config.get("provider", "openai").lower()
    model_name = model_config.get("model_name", "o1")

    system_msg = "You are a math student trying to solve the following problem. Only provide the final answer. No explanation."
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": problem},
    ]

    config_manager = get_config_manager()

    if provider == "openai":
        openai_client = _get_openai_client()
        if not openai_client:
            raise ModelError("Missing OPENAI_KEY", provider="openai")

        logger.info(f"Calling OpenAI {model_name}...")
        response = openai_client.chat.completions.create(
            model=model_name, messages=messages, temperature=1.0
        )
        choice = response.choices[0]
        usage = response.usage
        logger.info(f"OpenAI {model_name} responded successfully")
        return {
            "output": choice.message.content.strip(),
            "tokens_prompt": usage.prompt_tokens,
            "tokens_completion": usage.completion_tokens,
        }

    elif provider == "deepseek":
        deepseek_key = config_manager.get_api_key("deepseek")
        if not deepseek_key:
            raise ModelError(
                "Missing DEEPSEEK_KEY for Fireworks API", provider="deepseek"
            )

        logger.info(f"Calling DeepSeek {model_name}...")
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
        payload = {
            "model": model_name,
            "max_tokens": 5120,
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": 0.6,
            "messages": messages,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {deepseek_key}",
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise APIError(
                f"Fireworks API request failed: {response.text}",
                status_code=response.status_code,
                api_name="Fireworks",
            )

        result = response.json()
        choice = result["choices"][0]["message"]["content"].strip()
        usage = result.get("usage", {})
        logger.info(f"DeepSeek {model_name} responded successfully")
        return {
            "output": choice,
            "tokens_prompt": usage.get("prompt_tokens", 0),
            "tokens_completion": usage.get("completion_tokens", 0),
        }

    elif provider == "gemini":
        _configure_gemini()
        gemini_key = config_manager.get_api_key("gemini")
        if not gemini_key:
            raise ModelError("Missing GEMINI_KEY", provider="gemini")

        logger.info(f"Calling Gemini {model_name}...")
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(problem)
        # Gemini doesn't expose usage reliably in current SDK
        logger.info(f"Gemini {model_name} responded successfully")
        return {
            "output": response.text.strip(),
            "tokens_prompt": 0,
            "tokens_completion": 0,
        }

    else:
        raise ModelError(f"Unknown model provider: {provider}", provider=provider)
