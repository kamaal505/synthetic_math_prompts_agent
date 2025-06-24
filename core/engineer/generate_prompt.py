import os
import re
import json
from dotenv import load_dotenv
from utils.system_messages import ENGINEER_MESSAGE
from utils.json_utils import safe_json_parse
from core.llm.openai_utils import call_openai_model

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")


def call_openai(system_prompt, user_prompt, model_name):
    full_prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"
    return safe_json_parse(call_openai_model("engineer", full_prompt, model_name, effort="medium"))


def call_gemini(messages, model_name):
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)
    prompt = "\n".join([msg["content"] for msg in messages])
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    return safe_json_parse(response.text)


def generate_full_problem(seed, subject, topic, provider, model_name):
    user_prompt = f"Generate a math problem in {subject} under the topic '{topic}' with hints."
    if seed:
        user_prompt += f"\nUse this real-world example as inspiration:\n{seed}"

    system_prompt = ENGINEER_MESSAGE

    if provider == "openai":
        data = call_openai(system_prompt, user_prompt, model_name)
    elif provider == "gemini":
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        data = call_gemini(messages, model_name)
    else:
        raise ValueError(f"Unsupported engineer provider: {provider}")

    if not isinstance(data.get("hints"), dict) or len(data["hints"]) < 3:
        raise ValueError("Invalid or too few hints returned.")

    print(f"✅ Problem generated with {len(data['hints'])} hints.")
    return {
        "subject": data["subject"],
        "topic": data["topic"],
        "problem": data["problem"],
        "answer": data["answer"],
        "hints": data["hints"]
    }
