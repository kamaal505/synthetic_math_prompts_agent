import os
import json
import re
from dotenv import load_dotenv

from utils.system_messages import ENGINEER_MESSAGE

# Load API keys
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# --- Utility ---

def safe_json_parse(raw_text):
    
    raw_text = raw_text.strip()

    # Strip Markdown ```json or ``` markers
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    # Trim to { ... } block if there's garbage around
    json_start = raw_text.find('{')
    json_end = raw_text.rfind('}') + 1
    if json_start == -1 or json_end == -1:
        raise ValueError("No JSON block detected.")
    raw_text = raw_text[json_start:json_end]

    # Fix invalid quote escaping (e.g., \" inside a value)
    raw_text = raw_text.replace('\\"', '"')

    # Escape LaTeX-style backslashes if not already escaped
    raw_text = re.sub(r'(?<!\\)\\(?![\\nt"\\/bfr])', r'\\\\', raw_text)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("⚠️ JSON decode error at char", e.pos)
        print("🔍 Offending context:\n", raw_text[e.pos-40:e.pos+40])
        raise ValueError(f"Output is not valid JSON: {e}")
    
# --- LLM call wrappers ---

def call_openai(system_prompt, user_prompt, model_name):
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
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

# --- Main entrypoint ---

def generate_full_problem(seed=None, subject=None, topic=None, provider="gemini", model_name="gemini-2.5-pro"):
    user_prompt = f"Generate a math problem in {subject} under the topic '{topic}' with hints." if subject and topic else "Generate a new math problem with hints."
    if seed:
        user_prompt += f"\nUse this real-world example as inspiration:\n{seed}"

    if provider == "openai":
        data = call_openai(ENGINEER_MESSAGE, user_prompt, model_name)
    elif provider == "gemini":
        messages = [
            {"role": "system", "content": ENGINEER_MESSAGE},
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
