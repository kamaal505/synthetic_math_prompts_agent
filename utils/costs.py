import threading
from collections import defaultdict
from typing import Dict, Optional, Tuple

MODEL_PRICING = {
    # OpenAI Models
    ("openai", "gpt-4o"): (0.0025, 0.01),  # $2.50 / 1M input, $10.00 / 1M output
    ("openai", "gpt-4o-mini"): (0.00015, 0.0006),  # $0.15 / 1M input, $0.60 / 1M output
    ("openai", "gpt-4.1"): (0.002, 0.008),  # $2.00 / 1M input, $8.00 / 1M output
    ("openai", "gpt-4.1-mini"): (0.0004, 0.0016),  # $0.40 / 1M input, $1.60 / 1M output
    ("openai", "gpt-4.1-nano"): (0.0001, 0.0004),  # $0.10 / 1M input, $0.40 / 1M output
    ("openai", "o3"): (0.01, 0.04),  # $10.00 / 1M input, $40.00 / 1M output
    ("openai", "o3-mini"): (0.0011, 0.0044),  # $1.10 / 1M input, $4.40 / 1M output
    ("openai", "o4-mini"): (0.0011, 0.0044),  # $1.10 / 1M input, $4.40 / 1M output
    ("openai", "o1"): (0.0011, 0.0044),  # $1.10 / 1M input, $4.40 / 1M output

    # Gemini Models
    ("gemini", "gemini-2.5-pro-preview-03-25"): (0.0025, 0.015),  # Assumed rates
    ("gemini", "gemini-2.5-pro"): (0.0025, 0.015),  # Just in case both appear

    # DeepSeek Models
    ("deepseek", "deepseek-reasoner"): (0.0015, 0.0025),  # Assumed rates
    ("perplexity", "sonar-pro"): (0.01, 0.03),  # $10 / 1M in, $30 / 1M out
}


class CostTracker:
    """
    Tracks cumulative token usage and cost for each model across a run.
    Thread-safe implementation using threading.Lock.
    """

    def __init__(self):
        self._total_cost = 0.0
        self._model_stats = defaultdict(
            lambda: {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        )
        self._lock = threading.Lock()

    def log(self, model_config: Dict[str, str], input_tokens: int, output_tokens: int):
        provider = model_config["provider"]
        model = model_config["model_name"]
        key = (provider, model)

        input_rate, output_rate = MODEL_PRICING.get(key, (0.0, 0.0))

        # Estimate missing tokens for Gemini
        if provider == "gemini":
            if output_tokens == 0 and isinstance(model_config.get("raw_output"), str):
                output_tokens = len(model_config["raw_output"]) // 4
            if input_tokens == 0 and isinstance(model_config.get("raw_prompt"), str):
                input_tokens = len(model_config["raw_prompt"]) // 4

        input_cost = (input_tokens / 1000) * input_rate
        output_cost = (output_tokens / 1000) * output_rate
        total_cost = input_cost + output_cost

        with self._lock:
            self._total_cost += total_cost
            stats = self._model_stats[key]
            stats["input_tokens"] += input_tokens
            stats["output_tokens"] += output_tokens
            stats["cost"] += total_cost

    def get_total_cost(self) -> float:
        return round(self._total_cost, 6)

    def get_breakdown(self) -> Dict[str, Dict[str, float]]:
        return {
            f"{provider}:{model}": {
                "input_tokens": stats["input_tokens"],
                "output_tokens": stats["output_tokens"],
                "cost_usd": round(stats["cost"], 6),
            }
            for (provider, model), stats in self._model_stats.items()
        }

    def as_dict(self, run_id: Optional[str] = None) -> Dict:
        return {
            **({"run_id": run_id} if run_id else {}),
            "total_cost_usd": self.get_total_cost(),
            "model_breakdown": self.get_breakdown(),
        }

    def reset(self):
        self._total_cost = 0.0
        self._model_stats.clear()
