# 🛠️ Utilities – Synthetic Prompt Agent

The `utils/` module supports configuration loading, result saving, cost tracking, validation, and prompt formatting.

---

## 📁 Directory Structure

```
utils/
├── config_loader.py     # Loads YAML config files
├── save_results.py      # Saves prompts + costs
├── system_messages.py   # Shared prompt templates
├── costs.py             # Token accounting + price calculation
├── json_utils.py        # Safe parsing of LLM JSON-ish output
├── validation.py        # Validates model config schema
```

---

## 🔧 1. `config_loader.py`

```python
load_config(path: Path) → dict
```

Loads and parses a `.yaml` config into a Python dictionary.

---

## 💾 2. `save_results.py`

```python
save_prompts(valid_list, discarded_list, save_path, cost_tracker=None)
```

* Saves:

  * `valid.json`
  * `discarded.json`
  * `costs.json` (if `cost_tracker` is provided)
* Pretty-prints JSON with full fidelity

---

## 💰 3. `costs.py`

### ➤ `CostTracker` class

Tracks token usage and cost per model (OpenAI, Gemini, DeepSeek):

```python
tracker.log(model_config, tokens_prompt, tokens_completion)
tracker.get_total_cost() → float
tracker.get_breakdown() → dict
tracker.as_dict(run_id) → full JSON-ready cost summary
```

Pricing is model-specific (e.g., GPT-4o vs o3-mini) and defined via:

```python
MODEL_PRICING: Dict[(provider, model_name), (input_cost, output_cost)]
```

---

## 🧠 4. `system_messages.py`

Defines reusable LLM system prompts:

* `ENGINEER_MESSAGE`: guides generation of problem + answer + hints
* `CHECKER_MESSAGE`: validates problem and assesses model answers

Each prompt is tuned for strict formatting, no markdown/LaTeX, and JSON compliance.

---

## 🧼 5. `json_utils.py`

```python
safe_json_parse(text: str) → dict
```

* Parses malformed JSON-like strings (e.g. from LLMs)
* Falls back to correction strategies
* Raises a `ValueError` if unfixable

---

## 🔍 6. `validation.py`

```python
assert_valid_model_config(role: str, config: dict)
```

Raises helpful errors if:

* Config is missing
* Keys like `"provider"` or `"model_name"` are not found

Used at the start of the pipeline to prevent silent misconfigurations.

---

## ✅ Summary

| File                 | Purpose                              |
| -------------------- | ------------------------------------ |
| `config_loader.py`   | Load config settings                 |
| `save_results.py`    | Save prompts + cost tracking to disk |
| `costs.py`           | Track tokens used and compute cost   |
| `json_utils.py`      | Parse messy JSON returned by LLMs    |
| `system_messages.py` | Standardized LLM role prompts        |
| `validation.py`      | Sanity-check model config fields     |

---