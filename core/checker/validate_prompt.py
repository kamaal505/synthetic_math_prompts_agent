import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from utils.system_messages import CHECKER_MESSAGE
from utils.json_utils import safe_json_parse
from core.llm.openai_utils import call_openai_model

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")


def call_openai(messages: List[Dict[str, str]], model_name: str) -> dict:
    """
    Calls OpenAI checker and returns parsed response with token usage.
    """
    prompt = "\n".join([m["content"].strip() for m in messages])
    response = call_openai_model("checker", prompt, model_name, effort="low")

    if not response or "output" not in response:
        raise ValueError(f"OpenAI model '{model_name}' returned no usable output.")

    parsed = safe_json_parse(response["output"])
    parsed.update({
        "tokens_prompt": response.get("tokens_prompt", 0),
        "tokens_completion": response.get("tokens_completion", 0)
    })
    return parsed


def call_gemini(messages, model_name):
    """
    Calls Gemini checker and returns parsed response with zero token metadata.
    """
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)
    prompt = "\n".join([msg["content"] for msg in messages])
    model = genai.GenerativeModel(model_name=model_name)
    
    print(f"🔍 Checker (Gemini {model_name}) called...")
    response = model.generate_content(prompt)
    parsed = safe_json_parse(response.text)
    parsed.update({
        "tokens_prompt": 0,
        "tokens_completion": 0
    })
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
            "hints": problem_data["hints"]
        }
    elif mode == "equivalence_check":
        user_prompt = {
            "problem": problem_data["problem"],
            "true_answer": problem_data["answer"],
            "model_answer": problem_data["target_model_answer"]
        }
    else:
        raise ValueError("Unknown mode")

    messages = [
        {"role": "system", "content": CHECKER_MESSAGE},
        {"role": "user", "content": json.dumps(user_prompt)}
    ]

    if provider == "openai":
        return call_openai(messages, model_name)
    elif provider == "gemini":
        return call_gemini(messages, model_name)
    else:
        raise ValueError(f"Unsupported checker provider: {provider}")
