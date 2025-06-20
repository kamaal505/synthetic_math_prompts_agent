import os
import json
import re
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")

from system_messages import CHECKER_MESSAGE

def safe_json_parse(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = re.sub(r'(?<!\\)\\(?![\\nt"\\/bfr])', r'\\\\', raw_text)
    return json.loads(raw_text)

def call_openai(messages: List[Dict[str, str]], model_name="o3-mini") -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=1.0
    )
    return safe_json_parse(response.choices[0].message.content.strip())

def call_gemini(messages, model_name):
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)
    prompt = "\n".join([msg["content"] for msg in messages])
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    return safe_json_parse(response.text)

def validate_problem(problem_data: dict, mode="initial", provider="openai", model_name="o3-mini") -> dict:
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
