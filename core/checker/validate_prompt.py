import json
import os
from typing import Dict, List

from dotenv import load_dotenv

from core.llm.openai_utils import call_openai_model
from utils.exceptions import ModelError, ValidationError
from utils.json_utils import safe_json_parse
from utils.system_messages import CHECKER_MESSAGE

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")


def call_openai(messages: List[Dict[str, str]], model_name: str) -> dict:
    """
    Calls OpenAI checker and returns parsed response with token usage.
    """
    prompt = "\n".join([m["content"].strip() for m in messages])
    response = call_openai_model("checker", prompt, model_name, effort="low")

    if not response or "output" not in response:
        raise ModelError(
            f"OpenAI model '{model_name}' returned no usable output.",
            model_name=model_name,
            provider="openai",
        )

    parsed = safe_json_parse(response["output"])
    parsed.update(
        {
            "tokens_prompt": response.get("tokens_prompt", 0),
            "tokens_completion": response.get("tokens_completion", 0),
        }
    )
    return parsed


def call_gemini(messages, model_name):
    """
    Calls Gemini checker and returns parsed response with zero token metadata.
    """
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_KEY)
    prompt = "\n".join([msg["content"] for msg in messages])
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    parsed = safe_json_parse(response.text)
    parsed.update({"tokens_prompt": 0, "tokens_completion": 0})
    return parsed


def validate_problem(problem_data: dict, mode, provider, model_name):
    """
    Validates a problem or performs answer equivalence check.
    Returns checker result + token usage.
    """
    if mode == "initial":
        user_prompt = {
            "problem": problem_data["problem"],
            "answer": problem_data["answer"],
            "hints": problem_data["hints"],
        }
    elif mode == "equivalence_check":
        user_prompt = {
            "problem": problem_data["problem"],
            "true_answer": problem_data["answer"],
            "model_answer": problem_data["target_model_answer"],
        }
    else:
        raise ValidationError("Unknown mode", field="mode")

    messages = [
        {"role": "system", "content": CHECKER_MESSAGE},
        {"role": "user", "content": json.dumps(user_prompt)},
    ]

    if provider == "openai":
        return call_openai(messages, model_name)
    elif provider == "gemini":
        return call_gemini(messages, model_name)
    else:
        raise ModelError(f"Unsupported checker provider: {provider}", provider=provider)
