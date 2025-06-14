# 🧠 Synthetic Math Prompt Generation Pipeline

This project builds a high-quality dataset of math problems that are:

- **Mathematically valid**
- **Challenging enough to break a target LLM** (e.g. OpenAI `o1`)

It uses a multi-stage agent framework that ensures **only validated and model-breaking problems** are accepted into the final dataset.

---

## 🧩 Architecture Overview

| Stage        | Agent        | LLM               | Purpose                                    |
|--------------|--------------|-------------------|--------------------------------------------|
| 1. Generate  | Engineer     | Gemini 2.5 Pro     | Create problem and answer                  |
| 2. Hint      | Engineer     | Gemini 2.5 Pro     | Generate step-by-step hints                |
| 3. Validate  | Checker      | OpenAI o3-mini     | Ensure mathematical validity               |
| 4. Challenge | Target Model | OpenAI o1 (default)| Attempt to solve the problem               |
| 5. Judge     | Checker      | OpenAI o3-mini     | Check if the model’s answer is equivalent  |

---

## 🚀 Quickstart

### 🔧 Environment Setup

```bash
git clone https://github.com/your-org/synthetic-prompt-agent
cd synthetic-prompt-agent

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
````

### 🔑 API Keys

Create a `.env` file in the root:

```dotenv
GEMINI_KEY=your_gemini_api_key
OPENAI_KEY=your_openai_api_key
DEEPSEEK_KEY=your_fireworks_api_key  # Optional, for DeepSeek-R1 via Fireworks
```

---

## ▶️ Running the Generator

To generate a batch of validated, model-breaking prompts using default settings:

```bash
python -m cli.interface --batch-id batch_01
```

By default, this will:

* Use the target model from `config/settings.yaml` (typically OpenAI `o1`)
* Generate the number of problems specified in YAML
* Create a new results folder under `results/batch_01`
* Save accepted and rejected prompts as JSON files

---

## 🛠 CLI Override Examples

These examples let you override YAML settings from the command line:

### 1. ✅ Run with all defaults (batch ID, model, number of problems)

```bash
python -m cli.interface --batch-id batch_01
```

### 2. 🗃 Override the batch ID

```bash
python -m cli.interface --batch-id my_custom_batch
```

### 3. 🔢 Override the number of problems

```bash
python -m cli.interface --batch-id test_batch --num-problems 3
```

### 4. 🤖 Use **DeepSeek R1** via Fireworks

```bash
python -m cli.interface \
  --batch-id deepseek_batch \
  --target-provider deepseek \
  --target-model accounts/fireworks/models/deepseek-r1
```

### 5. 🧠 Use an **OpenAI** model other than `o1` (e.g. `gpt-4`)

```bash
python -m cli.interface \
  --batch-id gpt4_batch \
  --target-provider openai \
  --target-model gpt-4
```

### 6. 🔮 Use a **Gemini** model (e.g. `gemini-1.5-pro`)

```bash
python -m cli.interface \
  --batch-id gemini_batch \
  --target-provider gemini \
  --target-model gemini-1.5-pro
```

---

## ⚙️ Configuration

### 📝 YAML Settings (`config/settings.yaml`)

```yaml
num_problems: 10

subjects:
  Linear Algebra:
    - Spectral Theorem
    - Matrix Similarity
  Complex Analysis:
    - Contour Integration
    - Analytic Functions
  Algebra:
    - Galois Theory
    - Polynomial Rings

output_dir: "./results"
default_batch_id: "batch_01"

use_search: false

target_model:
  provider: "openai"
  model_name: "o1"
```

You can edit this file to control:

* Number of problems per batch
* Subject/topic coverage
* Output location
* Default target model/provider (can be overridden via CLI)

---

## 📦 Output Format

Accepted prompts are saved in `valid.json`:

```json
{
  "subject": "Algebra",
  "topic": "Galois Theory",
  "problem": "Let f(x) be a cubic polynomial...",
  "answer": "G = {(σ, τ) ∈ S₃ × S₃ | sgn(σ) = sgn(τ)}",
  "hints": {
    "0": "First, identify the splitting fields for both polynomials.",
    "1": "Next, consider the compositum field and how automorphisms act.",
    "2": "Finally, determine the group structure under the sign condition."
  },
  "target_model_answer": "G = {(σ, τ) in S₃ × S₃ : sgn(σ) = sgn(τ)}"
}
```

Rejected prompts (either invalid or answered correctly by the model) are saved in `discarded.json`.

---

## ✅ Acceptance Criteria

A prompt is accepted **only if:**

* ✅ It is **mathematically valid** (problem, answer, and hints pass validation)
* ❌ And the **target model fails** to produce a semantically equivalent answer

Prompts that are valid but **solved correctly** by the model are discarded.

---

## 📌 To-Do / Future Enhancements

* [ ] **Web Search (via MCP)**
* [ ] **Rejected Prompt Database**
* [ ] **Expanding Taxonomy**
* [ ] **Reviewer UI**
* [ ] **Difficulty Calibration**
* [ ] **Prompt Variants**

---

## 🛠 Debugging Tips

* Gemini sometimes emits invalid JSON. The script will retry until valid output is received.
* Hints are stored as a **dictionary** of index-to-string mappings.
* If your machine sleeps mid-run, the script may freeze. Consider running on a persistent setup.
* To inspect Gemini's responses, uncomment the print statement in `generate_hints()`.

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue to discuss any major changes first.

This project aims to be:

* Modular
* Extensible
* LLM-agnostic
* Research-grade

---

MIT License © 2025 Kamaal