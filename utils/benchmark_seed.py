import json
import os

# Map benchmark names to local file paths
BENCHMARK_PATHS = {
    "AIME": "taxonomy/benchmarks/AIME.json",
    "HMMT": "taxonomy/benchmarks/HMMT.json",
    "GPQA_DIAMOND": "taxonomy/benchmarks/GPQA_DIAMOND.json",
}

def load_benchmark(name: str):
    if name not in BENCHMARK_PATHS:
        raise ValueError(f"Unknown benchmark: {name}")

    filepath = os.path.join(os.path.dirname(__file__), "..", BENCHMARK_PATHS[name])
    filepath = os.path.normpath(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Quick validation
    if not isinstance(data, list):
        raise ValueError(f"{name} benchmark must be a list of problems")
    if not all("problem" in item and "answer" in item for item in data):
        raise ValueError(f"{name} benchmark data is not normalized")

    return data
