import re
import json

def safe_json_parse(raw_text):
    raw_text = raw_text.strip()

    # Strip Markdown-style fencing
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

    # Escape LaTeX-style backslashes
    raw_text = re.sub(r'(?<!\\)\\(?![\\nt"\\/bfr])', r'\\\\', raw_text)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("⚠️ JSON decode error at char", e.pos)
        print("🔍 Offending context:\n", raw_text[e.pos-40:e.pos+40])
        raise ValueError(f"Output is not valid JSON: {e}")
