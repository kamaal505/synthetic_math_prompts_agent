import logging

from core.llm.openai_utils import call_openai_model
from utils.config_manager import get_config_manager
from utils.exceptions import ModelError, ValidationError
from utils.json_utils import safe_json_parse
from utils.system_messages import ENGINEER_MESSAGE, ENGINEER_MESSAGE_SEED

# Get logger for this module
logger = logging.getLogger(__name__)


def call_openai(system_prompt, user_prompt, model_name):
    """
    Calls OpenAI model with response-style API and returns parsed output + token usage.
    """
    full_prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"
    response = call_openai_model("engineer", full_prompt, model_name, effort="high")

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

    config_manager = get_config_manager()
    gemini_key = config_manager.get_api_key("gemini")

    if not gemini_key:
        raise ModelError("Missing GEMINI_KEY", provider="gemini")

    genai.configure(api_key=gemini_key)
    prompt = "\n".join([msg["content"] for msg in messages])
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    parsed = safe_json_parse(response.text)
    parsed.update(
        {
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "raw_output": response.text,
            "raw_prompt": prompt,
        }
    )
    return parsed


def generate_full_problem(seed, subject, topic, provider, model_name):
    """
    Generates a math problem with hints and returns full data + token usage.
    Uses a seed-mode system prompt if 'seed' is provided.
    """

    # Choose correct system message and user prompt
    if seed:
        system_prompt = ENGINEER_MESSAGE_SEED
        user_prompt = f"""Use the following math problem as a base and modify it to make it more difficult while keeping the topic and final answer format consistent:

        Original problem:
        \"\"\"
        {seed}
        \"\"\"
        """
    else:
        system_prompt = ENGINEER_MESSAGE
        user_prompt = f"Generate a math problem in {subject} under the topic '{topic}' with hints."

    # Call model
    if provider == "openai":
        data = call_openai(system_prompt, user_prompt, model_name)
    elif provider == "gemini":
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        data = call_gemini(messages, model_name)
    else:
        raise ModelError(f"Unsupported engineer provider: {provider}", provider=provider)

    if not isinstance(data.get("hints"), dict) or len(data["hints"]) < 3:
        raise ValidationError("Invalid or too few hints returned.", field="hints")

    logger.info(f"✅ Problem generated with {len(data['hints'])} hints.")

    return {
        "subject": data.get("subject", subject),
        "topic": data.get("topic", topic),
        "problem": data["problem"],
        "answer": data["answer"],
        "hints": data["hints"],
        "tokens_prompt": data.get("tokens_prompt", 0),
        "tokens_completion": data.get("tokens_completion", 0),
        "raw_output": data.get("raw_output", ""),
        "raw_prompt": data.get("raw_prompt", ""),
    }
