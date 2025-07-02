import os

from dotenv import load_dotenv

from core.llm.openai_utils import call_openai_model
from utils.exceptions import ModelError, ValidationError
from utils.json_utils import safe_json_parse
from utils.logging_config import log_info
from utils.system_messages import ENGINEER_MESSAGE

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")


def call_openai(system_prompt, user_prompt, model_name):
    """
    Calls OpenAI model with response-style API and returns parsed output + token usage.
    """
    full_prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"
    response = call_openai_model("engineer", full_prompt, model_name, effort="medium")

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
    Calls Gemini model and returns parsed output + zero token counts (not supported yet).
    """
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_KEY)
    prompt = "\n".join([msg["content"] for msg in messages])
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    parsed = safe_json_parse(response.text)
    parsed.update({
    "tokens_prompt": 0,
    "tokens_completion": 0,
    "raw_output": response.text,
    "raw_prompt": prompt
    })
    return parsed


def generate_full_problem(seed, subject, topic, provider, model_name):
    """
    Generates a math problem with hints and returns full data + token usage.
    """
    user_prompt = (
        f"Generate a math problem in {subject} under the topic '{topic}' with hints."
    )
    if seed:
        user_prompt += f"Use this real-world example as inspiration:\n{seed}"

    system_prompt = ENGINEER_MESSAGE

    if provider == "openai":
        data = call_openai(system_prompt, user_prompt, model_name)
    elif provider == "gemini":
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        data = call_gemini(messages, model_name)
    else:
        raise ModelError(
            f"Unsupported engineer provider: {provider}", provider=provider
        )

    if not isinstance(data.get("hints"), dict) or len(data["hints"]) < 3:
        raise ValidationError("Invalid or too few hints returned.", field="hints")

    log_info(f"✅ Problem generated with {len(data['hints'])} hints.")
    return {
        "subject": data["subject"],
        "topic": data["topic"],
        "problem": data["problem"],
        "answer": data["answer"],
        "hints": data["hints"],
        "tokens_prompt": data.get("tokens_prompt", 0),
        "tokens_completion": data.get("tokens_completion", 0),
        "raw_output": data.get("raw_output", ""),
        "raw_prompt": data.get("raw_prompt", "")
    }

