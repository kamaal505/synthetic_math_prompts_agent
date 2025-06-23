# 🛠️ Utilities – Synthetic Prompt Agent

The `utils/` module provides essential supporting functions for the synthetic prompt generation system. These utilities help with configuration loading, result saving, and standardized system prompts for LLM calls.

---

## 📁 Directory Structure

```
utils/
├── config_loader.py      # Loads YAML config files
├── save_results.py       # Saves accepted/rejected prompts as JSON
└── system_messages.py    # Holds system prompts for LLMs
```

---

## 🔧 1. `config_loader.py`

### ➤ `load_config(config_path: Path) → dict`

Reads a `.yaml` configuration file and returns a dictionary.

**Usage Example:**

```python
from utils.config_loader import load_config
from pathlib import Path

config = load_config(Path("config/settings.yaml"))
print(config["num_problems"])
```

This is used by both CLI and interactive scripts to initialize pipeline parameters.

---

## 💾 2. `save_results.py`

### ➤ `save_prompts(valid_list, discarded_list, save_path)`

Writes accepted and rejected problems to a batch-specific folder as JSON files.

* Creates the output directory if it doesn't exist.
* Preserves full fidelity and formatting (`ensure_ascii=False`).
* Logs the save location and prompt counts.

**Files written:**

* `valid.json` – contains prompts that were validated and broke the target model
* `discarded.json` – contains invalid prompts or ones solved by the model

**Example Usage:**

```python
from utils.save_results import save_prompts

save_prompts(valid, discarded, "results/batch_01")
```

---

## 🧠 3. `system_messages.py`

Contains standardized system messages used to prime the LLMs in different roles. These ensure consistent behavior across providers (OpenAI, Gemini, etc.).

---

### ➤ `ENGINEER_MESSAGE`

Sets expectations for the LLM tasked with generating synthetic math problems.

**Highlights:**

* Problems must be self-contained, precise, and difficult
* Must return a valid answer and a dictionary of hints
* No markdown or LaTeX wrappers allowed
* Strong emphasis on correctness and JSON format

Example usage:

```python
from utils.system_messages import ENGINEER_MESSAGE
```

---

### ➤ `CHECKER_MESSAGE`

Used in validation and equivalence checking modes. It instructs the LLM on how to:

* Validate a math problem's answer and hints
* Provide corrections if needed
* Determine if a model's answer is mathematically equivalent

**Highlights:**

* Validates both logic and final answers
* Requires JSON output with:

  ```json
  {
    "valid": true,
    "reason": "...",
    "corrected_hints": { "0": "...", "1": "..." }
  }
  ```
* Must avoid markdown, LaTeX, or unnecessary formatting

---

## 💡 Summary

| File                 | Purpose                                       |
| -------------------- | --------------------------------------------- |
| `config_loader.py`   | Load structured config for the pipeline       |
| `save_results.py`    | Save accepted and rejected prompts to disk    |
| `system_messages.py` | Provide reusable system prompts for LLM roles |

---