# 🛠️ Utilities – Synthetic Prompt Agent

The `utils/` module contains all shared functionality needed by the synthetic prompt pipeline, including configuration loading, taxonomy handling, logging, error management, cost tracking, and similarity scoring.

---

## 📁 Directory Structure

```

utils/
├── config\_loader.py         # Loads YAML config files
├── costs.py                 # Tracks tokens and computes cost
├── cost\_estimation.py       # Safe wrapper for logging model costs
├── exceptions.py            # Custom exception classes
├── json\_utils.py            # Robust parsing of LLM output
├── logging\_config.py        # Centralized logging utilities
├── save\_results.py          # Saves prompt and cost outputs
├── similarity\_utils.py      # Embedding-based similarity search tools
├── system\_messages.py       # Standardized prompts for LLM roles
├── taxonomy.py              # Loads taxonomy JSON with validation
├── validation.py            # Sanity checks on model config

````

---

## 🔧 Module Descriptions

### `config_loader.py`

```python
load_config(path: Path) → dict
````

Loads `.yaml` files into dictionaries for use in the pipeline.

---

### `save_results.py`

```python
save_prompts(valid_list, discarded_list, save_path, cost_tracker=None)
```

* Saves `valid.json`, `discarded.json`, and `costs.json` (if available)
* Creates per-run output directories

---

### `costs.py`

Tracks token usage and monetary cost across all LLM providers.

#### `CostTracker`

```python
tracker.log(model_config, tokens_prompt, tokens_completion)
tracker.get_total_cost() → float
tracker.get_breakdown() → dict
tracker.as_dict(run_id) → dict
```

Uses fixed pricing for OpenAI, DeepSeek, and estimated token lengths for Gemini.

---

### `cost_estimation.py`

```python
safe_log_cost(cost_tracker, model_config, tokens_prompt, tokens_completion, raw_output, raw_prompt)
```

* Safely wraps `tracker.log(...)`
* Handles missing token values or logging errors
* Uses fallback estimations and centralized error logging

---

### `exceptions.py`

Defines custom exception classes for cleaner error handling:

* `ConfigError`, `TaxonomyError`, `PipelineError`
* `ModelError`, `ValidationError`
* `JSONParsingError`, `APIError`

Each exception provides contextual information (e.g., file paths, fields, or API names).

---

### `json_utils.py`

```python
safe_json_parse(text: str) → dict
```

* Parses malformed or incomplete JSON-like strings
* Attempts structure recovery or raises `JSONParsingError`

---

### `logging_config.py`

Centralized logging setup for the entire project.

```python
setup_logger(...)
log_error(...)
log_warning(...)
log_info(...)
log_debug(...)
```

* Console and file logging support
* Used across all modules instead of `print()`

---

### `similarity_utils.py`

Embedding-based similarity search and reranking (used for frontend/database filtering).

```python
fetch_embedding(text) → List[float]
cosine_similarity(vec1, vec2) → float
find_similar_problems(problem_text, db_session=None, exclude_ids=[], threshold=...)
```

* Supports OpenAI embeddings
* Used to compare generated problems to existing stored problems (e.g., in SQL DB)
* Can be extended to support other providers

---

### `system_messages.py`

Defines standardized prompts for:

* `ENGINEER_MESSAGE` – LLM generates problem, answer, hints
* `CHECKER_MESSAGE` – Validates and compares

---

### `taxonomy.py`

```python
load_taxonomy_file(taxonomy_path: str | Path) → dict
```

* Loads and validates subject/topic taxonomies from `.json` files
* Raises `TaxonomyError` on missing or malformed input

---

### `validation.py`

```python
assert_valid_model_config(role: str, config: dict)
```

* Validates presence of required model fields (`provider`, `model_name`)
* Raises `ValidationError` if config is incomplete or malformed

---

## ✅ Summary Table

| File                  | Purpose                                     |
| --------------------- | ------------------------------------------- |
| `config_loader.py`    | Load YAML configs                           |
| `costs.py`            | Track token usage and compute cost          |
| `cost_estimation.py`  | Fallback-safe model cost logger             |
| `exceptions.py`       | Structured exception types                  |
| `json_utils.py`       | Parse and recover malformed JSON            |
| `logging_config.py`   | Logging setup with levels and error tracing |
| `save_results.py`     | Save prompts and metadata to disk           |
| `similarity_utils.py` | Embedding-based similarity scoring          |
| `system_messages.py`  | Prompt templates for LLM roles              |
| `taxonomy.py`         | Load and validate subject-topic taxonomy    |
| `validation.py`       | Model config checks for all LLM roles       |

---
