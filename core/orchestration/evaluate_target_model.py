import json
import os
from typing import Dict

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from openai import OpenAI

from utils.exceptions import APIError, ModelError

load_dotenv()

# Load API keys
OPENAI_KEY = os.getenv("OPENAI_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")

# OpenAI client (for o1, o3, o4, etc.)
openai_client = OpenAI(api_key=OPENAI_KEY)

# Gemini config
genai.configure(api_key=GEMINI_KEY)


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

    if provider == "openai":
        if not OPENAI_KEY:
            raise ModelError("Missing OPENAI_KEY", provider="openai")

        print(f"   📞 Calling OpenAI {model_name}...")
        response = openai_client.chat.completions.create(
            model=model_name, messages=messages, temperature=1.0
        )
        choice = response.choices[0]
        usage = response.usage
        print(f"   ✅ OpenAI {model_name} responded successfully")
        return {
            "output": choice.message.content.strip(),
            "tokens_prompt": usage.prompt_tokens,
            "tokens_completion": usage.completion_tokens,
        }

    elif provider == "deepseek":
        if not DEEPSEEK_KEY:
            raise ModelError(
                "Missing DEEPSEEK_KEY for Fireworks API", provider="deepseek"
            )

        print(f"   📞 Calling DeepSeek {model_name}...")
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
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
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
        print(f"   ✅ DeepSeek {model_name} responded successfully")
        return {
            "output": choice,
            "tokens_prompt": usage.get("prompt_tokens", 0),
            "tokens_completion": usage.get("completion_tokens", 0),
        }

    elif provider == "gemini":
        if not GEMINI_KEY:
            raise ModelError("Missing GEMINI_KEY", provider="gemini")

        print(f"   📞 Calling Gemini {model_name}...")
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(problem)
        # Gemini doesn't expose usage reliably in current SDK
        print(f"   ✅ Gemini {model_name} responded successfully")
        return {
            "output": response.text.strip(),
            "tokens_prompt": 0,
            "tokens_completion": 0,
        }

    else:
        raise ModelError(f"Unknown model provider: {provider}", provider=provider)
