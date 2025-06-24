import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")

def call_openai_model(role: str, prompt: str, model_name: str, effort: str = "medium") -> str:

    """
    Dispatch OpenAI model calls based on model type.
    Supports o1, o3, o4, and gpt-style models. Deprecated models will raise errors.
    """

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)

    if model_name.startswith("gpt"):
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0
        )
        return response.choices[0].message.content.strip()

    elif model_name in {"o1", "o3", "o3-mini", "o4", "o4-mini"}:
        response = client.responses.create(
            model=model_name,
            reasoning={"effort": effort},
            input=[{"role": "user", "content": prompt}]
        )
        return response.output_text.strip()

    else:
        raise ValueError(f"Unsupported or deprecated OpenAI model: {model_name}")
