"""
Centralized LLM client for handling all API interactions.

This module provides a unified interface for calling different LLM providers
(OpenAI, Gemini, etc.) with consistent error handling, retry logic, and logging.
"""

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from openai import OpenAI

from utils.config_manager import get_config_manager
from utils.exceptions import APIError, ModelError

# Load environment variables
load_dotenv()

# Get logger for this module
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Centralized client for all LLM API interactions.

    Handles authentication, request/response logic, retry mechanisms,
    and logging for all supported LLM providers.
    """

    def __init__(self):
        """Initialize the LLM client with API keys and configurations."""
        self.config_manager = get_config_manager()

        # Load API keys from environment
        self.openai_key = os.getenv("OPENAI_KEY")
        self.gemini_key = os.getenv("GEMINI_KEY")
        self.deepseek_key = os.getenv("DEEPSEEK_KEY")

        # Initialize clients
        self.openai_client = None
        if self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)

        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)

    def call_model(
        self,
        provider: str,
        model_name: str,
        prompt: str,
        role: str = "user",
        temperature: float = 1.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Unified method to call any supported LLM model with enhanced concurrent processing support.

        Args:
            provider: The LLM provider ('openai', 'gemini', 'deepseek')
            model_name: The specific model to use
            prompt: The prompt to send to the model
            role: The role for the message (default: 'user')
            temperature: Temperature setting for the model
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict containing:
                - output: The model's response text
                - tokens_prompt: Number of input tokens used
                - tokens_completion: Number of output tokens used
                - latency: Response time in seconds

        Raises:
            ModelError: If the model or provider is unsupported
            APIError: If the API call fails after all retries
        """
        start_time = time.perf_counter()
        thread_id = threading.current_thread().ident

        logger.debug(
            f"🧵 Thread {thread_id}: Calling {provider} model {model_name} "
            f"with {len(prompt)} character prompt"
        )

        last_exception = None

        for attempt in range(max_retries):
            try:
                if provider.lower() == "openai":
                    result = self._call_openai(
                        model_name, prompt, role, temperature, **kwargs
                    )
                elif provider.lower() == "gemini":
                    result = self._call_gemini(
                        model_name, prompt, temperature, **kwargs
                    )
                elif provider.lower() == "deepseek":
                    result = self._call_deepseek(
                        model_name, prompt, role, temperature, **kwargs
                    )
                else:
                    raise ModelError(
                        f"Unsupported provider: {provider}", provider=provider
                    )

                latency = time.perf_counter() - start_time
                result["latency"] = latency
                result["thread_id"] = thread_id
                result["attempt"] = attempt + 1

                logger.debug(
                    f"🧵 Thread {thread_id}: Successfully called {provider} {model_name} "
                    f"(attempt {attempt + 1}, tokens: {result.get('tokens_prompt', 0)}→{result.get('tokens_completion', 0)}, "
                    f"latency: {latency:.3f}s)"
                )

                return result

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"🧵 Thread {thread_id}: Attempt {attempt + 1}/{max_retries} failed for {provider} {model_name}: {str(e)}"
                )

                if attempt < max_retries - 1:
                    base_sleep = retry_delay * (2**attempt)
                    jitter = (
                        base_sleep * 0.1 * (hash(str(thread_id)) % 10) / 10
                    )
                    sleep_time = base_sleep + jitter

                    logger.debug(
                        f"🧵 Thread {thread_id}: Retrying in {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)

        logger.error(
            f"🧵 Thread {thread_id}: All {max_retries} attempts failed for {provider} {model_name}"
        )
        raise APIError(
            f"Failed to call {provider} {model_name} after {max_retries} attempts: {str(last_exception)}",
            api_name=provider,
            model_name=model_name,
        )

    def _call_openai(
        self,
        model_name: str,
        prompt: str,
        role: str,
        temperature: float,
        effort: str = "high",
        **kwargs,
    ) -> Dict[str, Any]:
        """Call OpenAI models (both chat and reasoning models)."""
        if not self.openai_client:
            raise ModelError(
                "OpenAI client not initialized. Check OPENAI_KEY.", provider="openai"
            )

        if model_name.startswith("gpt"):
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": role, "content": prompt}],
                temperature=temperature,
                **kwargs,
            )

            tokens_prompt, tokens_completion = self._extract_openai_tokens(response)
            output_text = response.choices[0].message.content.strip()

            if not output_text:
                raise ModelError(
                    f"OpenAI model '{model_name}' returned empty content.",
                    model_name=model_name,
                )

            return {
                "output": output_text,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
            }

        elif model_name in {"o1", "o3", "o3-mini", "o4", "o4-mini"}:
            response = self.openai_client.responses.create(
                model=model_name,
                reasoning={"effort": effort},
                input=[{"role": role, "content": prompt}],
                **kwargs,
            )

            tokens_prompt, tokens_completion = self._extract_openai_tokens(response)

            if not hasattr(response, "output_text") or not response.output_text.strip():
                logger.debug(
                    f"OpenAI reasoning model '{model_name}' returned no output_text."
                )
                logger.debug("Full response for debugging:")
                logger.debug(response.model_dump_json(indent=2))
                raise ModelError(
                    f"OpenAI model '{model_name}' returned no output.",
                    model_name=model_name,
                )

            return {
                "output": response.output_text.strip(),
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
            }
        else:
            raise ModelError(
                f"Unsupported OpenAI model: '{model_name}'",
                model_name=model_name,
                provider="openai",
            )

    def _call_gemini(
        self, model_name: str, prompt: str, temperature: float, **kwargs
    ) -> Dict[str, Any]:
        """Call Google Gemini models."""
        if not self.gemini_key:
            raise ModelError(
                "Gemini API key not found. Check GEMINI_KEY.", provider="gemini"
            )

        try:
            model = genai.GenerativeModel(model_name=model_name)

            generation_config = genai.types.GenerationConfig(
                temperature=temperature, **kwargs
            )

            response = model.generate_content(
                prompt, generation_config=generation_config
            )

            if not response.text:
                raise ModelError(
                    f"Gemini model '{model_name}' returned empty response.",
                    model_name=model_name,
                )

            return {
                "output": response.text.strip(),
                "tokens_prompt": 0,
                "tokens_completion": 0,
            }

        except Exception as e:
            raise ModelError(
                f"Gemini API call failed: {str(e)}",
                model_name=model_name,
                provider="gemini",
            )

    def _call_deepseek(
        self, model_name: str, prompt: str, role: str, temperature: float, **kwargs
    ) -> Dict[str, Any]:
        """Call DeepSeek models via Fireworks API."""
        if not self.deepseek_key:
            raise ModelError(
                "DeepSeek API key not found. Check DEEPSEEK_KEY.", provider="deepseek"
            )

        url = "https://api.fireworks.ai/inference/v1/chat/completions"

        payload = {
            "model": model_name,
            "max_tokens": kwargs.get("max_tokens", 5120),
            "top_p": kwargs.get("top_p", 1),
            "top_k": kwargs.get("top_k", 40),
            "presence_penalty": kwargs.get("presence_penalty", 0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
            "temperature": temperature,
            "messages": [{"role": role, "content": prompt}],
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_key}",
        }

        response = requests.post(
            url, headers=headers, data=json.dumps(payload), timeout=60
        )

        if response.status_code != 200:
            raise APIError(
                f"DeepSeek API request failed: {response.text}",
                status_code=response.status_code,
                api_name="DeepSeek",
            )

        result = response.json()
        choice = result["choices"][0]["message"]["content"].strip()
        usage = result.get("usage", {})

        return {
            "output": choice,
            "tokens_prompt": usage.get("prompt_tokens", 0),
            "tokens_completion": usage.get("completion_tokens", 0),
        }

    def _extract_openai_tokens(self, response) -> Tuple[int, int]:
        """Extract token usage from OpenAI response objects."""
        usage = getattr(response, "usage", None)

        if not usage and hasattr(response, "response_metadata"):
            usage = getattr(response.response_metadata, "usage", None)

        tokens_prompt = getattr(usage, "prompt_tokens", None)
        tokens_completion = getattr(usage, "completion_tokens", None)

        if tokens_prompt is None and tokens_completion is None:
            tokens_prompt = getattr(usage, "input_tokens", 0)
            tokens_completion = getattr(usage, "output_tokens", 0)

        return tokens_prompt or 0, tokens_completion or 0


# Global instance for easy access
_llm_client = None


def get_llm_client() -> LLMClient:
    """
    Get the global LLMClient instance (singleton pattern).

    Returns:
        The singleton LLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
