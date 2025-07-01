import json
from core.llm.openai_utils import call_openai_model
from utils.json_utils import safe_json_parse

MCP_SIMILARITY_PROMPT = """You are a math question similarity evaluator.

Given a synthetic math problem and a list of real math forum questions (including their full question content), compare them and return a cosine-style similarity score from 0.0 (completely different) to 1.0 (identical in content or approach).

For each internet question, consider both the title and the content. Focus on whether the type of math object, structure of reasoning, and problem goal are similar.

Provide individual scores for each match and an overall aggregated score.

Respond with JSON in this format:
{
  "similarity_score": float,
  "matches": [
    {"title": str, "url": str, "similarity": float, "source": str}
  ]
}
"""


def score_with_llm(problem_text, retrieved_docs, model="gpt-4-1106-preview"):
    """
    Calls an LLM to evaluate how similar a synthetic math problem is
    to a list of real-world math questions (title + content).
    """
    payload = {
        "problem": problem_text,
        "related": retrieved_docs
    }

    prompt = f"{MCP_SIMILARITY_PROMPT}\n\nUser Input:\n{json.dumps(payload, indent=2, ensure_ascii=False)}"
    response = call_openai_model("search", prompt, model, effort="low")

    parsed = safe_json_parse(response["output"])
    return {
        "similarity_score": parsed.get("similarity_score", 0.0),
        "top_matches": parsed.get("matches", [])
    }
