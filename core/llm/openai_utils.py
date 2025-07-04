import os

from dotenv import load_dotenv
from openai import OpenAI

from utils.exceptions import ModelError
from utils.logging_config import get_logger

# Get logger instance
logger = get_logger(__name__)

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")


def extract_tokens_from_response(response) -> tuple[int, int]:
    """
    Safely extracts input/output token counts from OpenAI responses.
    Handles both chat (prompt/completion) and responses (input/output) APIs.
    """
    usage = getattr(response, "usage", None)

    # Fallback for response-style models
    if not usage and hasattr(response, "response_metadata"):
        usage = getattr(response.response_metadata, "usage", None)

    # Chat format
    tokens_prompt = getattr(usage, "prompt_tokens", None)
    tokens_completion = getattr(usage, "completion_tokens", None)

    # Responses format
    if tokens_prompt is None and tokens_completion is None:
        tokens_prompt = getattr(usage, "input_tokens", 0)
        tokens_completion = getattr(usage, "output_tokens", 0)

    return tokens_prompt or 0, tokens_completion or 0


def call_openai_model(
    role: str, prompt: str, model_name: str, effort: str = "high"
) -> dict:
    """
    Calls OpenAI model and returns output + token usage metadata.
    Supports both chat and responses APIs. Returns None if output is missing.
    """
    client = OpenAI(api_key=OPENAI_KEY)

    if model_name.startswith("gpt"):
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
        )

        tokens_prompt, tokens_completion = extract_tokens_from_response(response)
        output_text = response.choices[0].message.content.strip()

        if not output_text:
            logger.debug(f"[❗] Chat model '{model_name}' returned empty content.")
            return None

        return {
            "output": output_text,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
        }

    elif model_name in {"o1", "o3", "o3-mini", "o4", "o4-mini"}:
        response = client.responses.create(
            model=model_name,
            reasoning={"effort": effort},
            input=[{"role": "user", "content": prompt}],
        )

        tokens_prompt, tokens_completion = extract_tokens_from_response(response)

        if not hasattr(response, "output_text") or not response.output_text.strip():
            logger.debug(f"[❗] Responses model '{model_name}' returned no output_text.")
            logger.debug("🔍 Full response for debugging:")
            logger.debug(response.model_dump_json(indent=2))
            return None

        return {
            "output": response.output_text.strip(),
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
        }

    else:
        raise ModelError(
            f"Unsupported or deprecated OpenAI model: '{model_name}'",
            model_name=model_name,
            provider="openai",
        )
