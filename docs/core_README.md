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
│   └── validate_prompt.py           # Validates problem and target model answer
├── engineer/
│   └── generate_prompt.py           # Generates problems, answers, and hints
├── orchestration/
│   ├── generate_batch.py            # Main generation loop
│   └── evaluate_target_model.py     # Sends problems to target model
├── cli/
│   ├── interface.py                 # CLI interface with override support
│   └── run_interactive.py           # Interactive CLI for manual runs
├── runner.py                        # Entry point for backend / service use
```

Dependencies:

```
utils/
├── config_loader.py                 # Loads YAML config
├── save_results.py                  # Saves valid and discarded problems
├── system_messages.py               # Holds prompt templates
```

---

## 📐 1. Engineering

### Purpose

The **Engineer** agent is responsible for generating:

* A math **problem**
* Its correct **answer**
* A set of **step-by-step hints** (dictionary of strings)

### Key Module: `engineer/generate_prompt.py`

#### ➤ `generate_full_problem(seed=None, subject=None, topic=None, ...)`

Creates a complete synthetic math prompt package.

* Pulls optional `seed` if real-world prompt data is available
* Builds user/system prompts using the `ENGINEER_MESSAGE`
* Calls:

  * `call_gemini()` or `call_openai()` depending on config
* Parses model output using `safe_json_parse()`

**Validation Criteria**:

* `hints` must be a `dict` with at least 3 entries
* Raises an error if invalid or underspecified

---

## ✅ 2. Validation

### Purpose

The **Checker** agent ensures the problem is:

* Mathematically sound
* Answer and hints are logically consistent
* Target model response is evaluated for correctness

### Key Module: `checker/validate_prompt.py`

#### ➤ `validate_problem(problem_data: dict, mode: str, provider: str, model_name: str)`

Modes:

* `"initial"`: Validates the generated problem/answer/hints
* `"equivalence_check"`: Compares the target model's answer to the ground truth

Internally uses:

* `call_openai()` or `call_gemini()`
* `safe_json_parse()` to sanitize JSON-like LLM output

**Returns**:

```python
{
  "valid": bool,
  "reason": "optional string if rejected",
  "corrected_hints": dict | None
}
```

---

## 🤖 3. Evaluation

### Purpose

The **Target Model** (e.g. OpenAI o1, GPT-4o, DeepSeek R1) attempts to solve the generated problem. If it fails to match the correct answer (semantically), the problem is considered a **break case**.

### Key Module: `orchestration/evaluate_target_model.py`

#### ➤ `model_attempts_answer(problem: str, model_config: dict)`

* Sends only the problem with a strict prompt:

  > “Only provide the final answer. No explanation.”
* Supports providers:

  * `openai` (via OpenAI SDK)
  * `deepseek` (via Fireworks API)
  * `gemini` (via `google.generativeai`)

**Returns**: final answer string (stripped)

---

## 📦 4. Batch Generation

### Purpose

Runs the full generation pipeline in a loop until the target number of **validated + model-breaking** problems is reached.

### Key Module: `orchestration/generate_batch.py`

#### ➤ `run_generation_pipeline(config)`

**Main steps per attempt**:

1. Sample a `subject` and `topic` (from config or `taxonomy`)
2. Optionally pull `seed_prompt` (e.g. from search)
3. **Engineer** generates problem, answer, hints
4. **Checker** validates (initial phase)
5. If valid, the **Target Model** attempts to solve
6. **Checker** judges the model’s answer
7. Accepted if:

   * Problem is valid ✅
   * Target model failed ❌

**Returns**:

* `accepted`: list of valid, model-breaking prompts
* `discarded`: list of invalid or solved prompts

---

## 🧰 CLI Interfaces

### 📄 `cli/interface.py`

This command-line entry point allows users to run the pipeline non-interactively with full YAML override support.

---

#### 🛠 CLI Override Examples

**1. ✅ Run with all defaults (batch ID, model, number of problems)**

```bash
python -m cli.interface --batch-id batch_01
```

**2. 🗃 Override the batch ID**

```bash
python -m cli.interface --batch-id my_custom_batch
```

**3. 🔢 Override the number of problems**

```bash
python -m cli.interface --batch-id test_batch --num-problems 3
```

**4. 🤖 Use DeepSeek R1 via Fireworks**

```bash
python -m cli.interface \
  --batch-id deepseek_batch \
  --target-provider deepseek \
  --target-model accounts/fireworks/models/deepseek-r1
```

**5. 🧠 Use an OpenAI model other than `o1` (e.g. `gpt-4`)**

```bash
python -m cli.interface \
  --batch-id gpt4_batch \
  --target-provider openai \
  --target-model gpt-4o
```

**6. 🔮 Use a Gemini model (e.g. `gemini-1.5-pro`)**

```bash
python -m cli.interface \
  --batch-id gemini_batch \
  --target-provider gemini \
  --target-model gemini-1.5-pro
```

---

### 🖥️ `cli/run_interactive.py`

This script is a fully interactive CLI for real-time config selection and override. It's ideal for debugging, experimentation, or one-off generations.

---

#### 🧰 Features

* Loads the default config from `config/settings.yaml`
* Prompts the user for:

  * Batch ID
  * Number of problems
  * Engineer, Checker, and Target model (provider + model name)
* Skipped entries fall back to default config values
* Displays which values were overridden
* Runs the full pipeline and prints live status
* Saves results to the batch output folder

---

#### 🔁 User Flow

1. Print a banner and load config
2. Prompt user for input values (with prefilled defaults)
3. Build config dynamically
4. Run pipeline
5. Save and print summary

---

#### 🧪 Example Interaction

```bash
python cli/run_interactive.py
```

```text
🧠 Synthetic Prompt Generator (Interactive Mode)

Enter batch ID [batch_01]:
Number of problems [10]: 3
Engineer provider [gemini]: openai
Engineer model name [gpt-4]: gpt-4
...

🚀 Running generation pipeline...

✅ Problem generated with 3 hints.
🧠 Target model failed — Accepted!

✅ 1 accepted | ❌ 2 discarded
🎉 Done.
```

---

## 🔁 Runner

### 📄 `runner.py`

A lightweight wrapper used by the FastAPI backend or other Python services.

#### ➤ `run_pipeline_from_config(config: dict) → dict`

Returns a dictionary of results:

```python
{
  "valid_prompts": [...],
  "discarded_prompts": [...],
  "metadata": {
    "total_attempted": int,
    "total_accepted": int
  }
}
```

---

## 📂 Output Structure

After running the pipeline, files are saved to `config["output_dir"]/batch_id/`:

```
results/
└── batch_01/
    ├── valid.json        # Accepted prompts
    └── discarded.json    # Rejected prompts (invalid or solved)
```

Each entry contains:

* `subject`, `topic`, `problem`, `answer`
* `hints` (dict)
* `target_model_answer`
* `rejection_reason` (if applicable)

---

## ✅ Acceptance Criteria

A problem is accepted into the dataset only if:

* ✅ It passes **initial validation** by the Checker
* ❌ The **Target model fails** to solve it correctly (semantic mismatch)

---

## 🔐 API Keys Required

Store your keys in a `.env` file at the root:

```env
OPENAI_KEY=your-openai-api-key
GEMINI_KEY=your-gemini-api-key
DEEPSEEK_KEY=your-fireworks-api-key
```

---