# 🧠 Core Logic – Synthetic Prompt Generation Engine

This module implements the **core logic** of a multi-stage agent pipeline that produces **mathematically valid**, **LLM-breaking** math problems. It uses three LLM roles:

* **Engineer**: Generates problems, answers, and hints
* **Checker**: Validates correctness and evaluates model answers
* **Target Model**: Simulates an LLM being challenged by the prompt

Only problems that are both **valid** and **not solved by the target model** are accepted.

---

## 📁 Directory Structure

```
core/
├── checker/
│   └── validate_prompt.py         # Validates problem and target model answer
├── engineer/
│   └── generate_prompt.py         # Generates problems, answers, and hints
├── llm/
│   ├── llm_dispatch.py            # Role-based dispatcher for engineer, checker, target
│   └── openai_utils.py            # Token-aware OpenAI wrapper (chat & responses APIs)
├── orchestration/
│   ├── generate_batch.py          # Main generation loop with cost tracking
│   └── evaluate_target_model.py   # Sends problems to the target model
├── cli/
│   ├── interface.py               # CLI for config-driven batch generation
│   └── run_interactive.py         # Interactive CLI for experimentation
├── runner.py                      # Entrypoint for backend or service integration
```

Dependencies:

```
utils/
├── config_loader.py               # Loads YAML config files
├── save_results.py                # Saves valid/discarded prompts and cost logs
├── system_messages.py             # Defines standardized system prompts
├── costs.py                       # Tracks tokens + computes cost by model
├── json_utils.py                  # Parses loosely structured JSON outputs
├── validation.py                  # Validates model config structure
```

---

## 📐 1. Engineering

The **Engineer** LLM generates:

* A math **problem**
* Its correct **answer**
* A dictionary of **hints**

### 🔧 `engineer/generate_prompt.py`

```python
generate_full_problem(seed, subject, topic, provider, model_name) → dict
```

* Constructs prompts using `ENGINEER_MESSAGE`
* Supports OpenAI and Gemini
* Parses LLM output using `safe_json_parse`
* Returns:

  * `problem`, `answer`, `hints`
  * `tokens_prompt`, `tokens_completion`

Raises error if:

* Hints are not a dictionary
* Fewer than 3 hints are returned

---

## ✅ 2. Validation

The **Checker** validates correctness and optionally compares the model's answer.

### 🔧 `checker/validate_prompt.py`

```python
validate_problem(problem_data, mode, provider, model_name) → dict
```

Modes:

* `"initial"`: Validates generated problem/answer/hints
* `"equivalence_check"`: Compares model answer with correct answer

Returns:

```json
{
  "valid": true,
  "reason": "...",
  "corrected_hints": { "0": "...", ... },
  "tokens_prompt": 123,
  "tokens_completion": 456
}
```

---

## 🤖 3. Evaluation

The **Target Model** attempts to solve the problem. If it fails, the problem is accepted.

### 🔧 `orchestration/evaluate_target_model.py`

```python
model_attempts_answer(problem: str, model_config: dict) → dict
```

* Uses a strict "final answer only" prompt
* Supports OpenAI, Gemini, and DeepSeek
* Returns:

  * `output`: model's answer
  * `tokens_prompt`, `tokens_completion`

---

## 🔌 3.5 Role Dispatcher

This module centralizes how each model role is routed to the appropriate logic.

### 🔧 `llm/llm_dispatch.py`

```python
call_engineer(subject, topic, seed_prompt, config) → dict
call_checker(core_problem, config, mode="initial") → dict
call_target_model(problem_text, config) → dict
```

Each function delegates to:

* Engineer → `generate_full_problem(...)`
* Checker → `validate_problem(...)`
* Target → `model_attempts_answer(...)`

Each call returns both output **and token usage**.

This dispatcher:

* Keeps `generate_batch.py` clean and role-agnostic
* Ensures consistent interface and logging across all roles

---

## 📦 4. Batch Generation

Loops through the entire prompt generation pipeline until enough valid, model-breaking prompts are accepted.

### 🔧 `orchestration/generate_batch.py`

```python
run_generation_pipeline(config: dict) → (accepted, discarded, cost_tracker)
```

Process:

1. Sample subject/topic from taxonomy (or override)
2. Optionally use a seed prompt (if web search is enabled)
3. Engineer generates a problem
4. Checker validates it
5. Target model attempts to solve it
6. Checker performs equivalence check

Tracks:

* Accepted prompts
* Discarded prompts
* Per-model token usage and cost

---

## 🧮 Cost Tracking

Token metadata is extracted and aggregated:

* ✅ OpenAI chat and responses APIs
* ✅ Compatible with cost tracking for Gemini and DeepSeek
* ✅ CostTracker stores token and price data

Saved as `costs.json` in the batch output directory.

---

## 🧪 CLI Support

CLI entry points live in the `cli/` folder.

* `interface.py`: accepts config or override args
* `run_interactive.py`: prompts user for config values

All results are saved in `output_dir/batch_id/`.

---

## ✅ Acceptance Criteria

A problem is accepted **only if**:

* ✅ It passes the initial validation (well-formed + pedagogically sound)
* ❌ It breaks the target model (i.e., model's answer is incorrect)

---

## 📂 Output Files

Saved to `results/<batch_id>/`:

```
results/
└── batch_01/
    ├── valid.json         # Accepted, validated, and LLM-breaking
    ├── discarded.json     # Invalid or solved
    └── costs.json         # Token and cost breakdown
```

---

## 🔐 API Keys

Add a `.env` file in the root:

```env
OPENAI_KEY=...
GEMINI_KEY=...
DEEPSEEK_KEY=...
```

These are accessed automatically by the relevant provider wrappers.

---