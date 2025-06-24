import os
import json
import re
from typing import List, Dict
from dotenv import load_dotenv
from utils.system_messages import CHECKER_MESSAGE
from utils.json_utils import safe_json_parse
from core.llm.openai_utils import call_openai_model

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")


def call_openai(messages: List[Dict[str, str]], model_name: str) -> dict:
    # Flatten all messages into a single prompt for response-style models
    prompt = "\n".join([m["content"].strip() for m in messages])
    return safe_json_parse(call_openai_model("checker", prompt, model_name, effort="low"))


def call_gemini(messages, model_name):
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)
    prompt = "\n".join([msg["content"] for msg in messages])
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    return safe_json_parse(response.text)


def validate_problem(problem_data: dict, mode, provider, model_name):
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
