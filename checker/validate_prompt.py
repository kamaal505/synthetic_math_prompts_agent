import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

try:
    from system_messages import CHECKER_MESSAGE
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from system_messages import CHECKER_MESSAGE

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=OPENAI_KEY)

def call_openai(messages: List[Dict[str, str]]) -> dict:
    response = client.chat.completions.create(
        model="o3-mini",
        messages=messages,
        temperature=1.0
    )
    content = response.choices[0].message.content.strip()
    return json.loads(content)

def validate_problem(problem_data: dict, mode="initial") -> dict:
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
    return call_openai(messages)
