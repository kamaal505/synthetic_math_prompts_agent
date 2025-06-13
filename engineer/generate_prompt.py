import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

try:
    from system_messages import ENGINEER_MESSAGE, HINT_ONLY_MESSAGE
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from system_messages import ENGINEER_MESSAGE, HINT_ONLY_MESSAGE

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-pro-preview-06-05")

def safe_json_parse(raw_text):
    raw_text = raw_text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    # Fix LaTeX-style escapes
    raw_text = re.sub(r'(?<!\\)\\(?![\\nt"\\/bfr])', r'\\\\', raw_text)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("⚠️ Gemini JSON decode error at char", e.pos)
        print("Offending text:\n", raw_text[e.pos-50:e.pos+50])
        raise ValueError(f"Gemini output is not valid JSON: {e}")

def call_gemini(messages):
    prompt = "\n".join([msg["content"] for msg in messages])
    response = model.generate_content(prompt)
    return safe_json_parse(response.text)

def generate_problem_shell(seed=None, subject=None, topic=None):
    user_prompt = "Generate a new problem as instructed."
    if subject and topic:
        user_prompt = f"Generate a math problem in {subject} under the topic '{topic}'."
    if seed:
        user_prompt += f"\nUse this real-world example as inspiration:\n{seed}"

    messages = [
        {"role": "system", "content": ENGINEER_MESSAGE},
        {"role": "user", "content": user_prompt}
    ]
    data = call_gemini(messages)
    return {
        "subject": data["subject"],
        "topic": data["topic"],
        "problem": data["problem"],
        "answer": data["answer"]
    }

def dictify_hints(hints):
    if isinstance(hints, list):
        return {str(i): h for i, h in enumerate(hints)}
    return hints

def generate_hints(problem, answer):
    retries = 0
    while True:
        retries += 1
        messages = [
            {"role": "system", "content": HINT_ONLY_MESSAGE},
            {"role": "user", "content": json.dumps({"problem": problem, "answer": answer})}
        ]
        try:
            result = call_gemini(messages)
            hints = result.get("hints", {})

            if isinstance(hints, list):  # sanitize if needed
                hints = dictify_hints(hints)

            print(f"\n🧾 Gemini response (attempt {retries}):", hints)
            if isinstance(hints, dict) and any(h.strip() for h in hints.values()):
                print(f"✅ Non-empty hint dict received on attempt {retries}")
                return hints
            else:
                print(f"❌ Empty or malformed hints on attempt {retries}. Retrying...")
        except Exception as e:
            print(f"⚠️ Hint parsing failed (attempt {retries}): {e}")
