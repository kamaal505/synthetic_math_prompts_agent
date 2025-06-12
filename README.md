# 🧠 Synthetic Math Prompt Generation Pipeline

This project builds a high-quality dataset of math problems that are:

- **Mathematically valid**
- **Challenging enough to break a target LLM** (e.g. OpenAI `o1`)

It uses a multi-stage agent framework that ensures **only validated and model-breaking problems** are accepted into the final dataset.

---

## 🧩 Architecture Overview

| Stage        | Agent        | LLM             | Purpose                                    |
|--------------|--------------|------------------|--------------------------------------------|
| 1. Generate  | Engineer     | Gemini 2.5 Pro    | Create problem and answer                  |
| 2. Hint      | Engineer     | Gemini 2.5 Pro    | Generate step-by-step hints                |
| 3. Validate  | Checker      | OpenAI o3-mini    | Ensure mathematical validity               |
| 4. Challenge | Target Model | OpenAI o1         | Attempt to solve the problem               |
| 5. Judge     | Checker      | OpenAI o3-mini    | Check if the model’s answer is equivalent  |

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
```

---

## ▶️ Running the Generator

To generate a batch of validated, model-breaking prompts:

```bash
python -m cli.interface --batch-id batch_test
```

To override the number of prompts (e.g. generate 1 instead of the default 10):

```bash
python -m cli.interface --batch-id test_batch --num-problems 1
```

This will:

* Load settings from `config/settings.yaml`
* Create a new folder under `results/test_batch`
* Save accepted and rejected prompts as JSON files

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

use_search: false  # (Planned) Enable web search augmentation
```

You can edit this file to control:

* Number of problems per batch
* Subject/topic coverage
* Output directory

---

## 📦 Output Format

Accepted prompts are saved in `valid.json`:

```json
{
  "subject": "Algebra",
  "topic": "Galois Theory",
  "problem": "Let f(x) be a cubic polynomial...",
  "answer": "G = {(σ, τ) ∈ S₃ × S₃ | sgn(σ) = sgn(τ)}",
  "hints": [
    "First, identify the splitting fields for both polynomials.",
    "Next, consider the compositum field and how automorphisms act.",
    "Finally, determine the group structure under the sign condition."
  ],
  "target_model_answer": "G = {(σ, τ) in S₃ × S₃ : sgn(σ) = sgn(τ)}"
}
```

Rejected prompts (either invalid or answered correctly by the model) are saved in `discarded.json`.

---

## ✅ Acceptance Criteria

A prompt is accepted **only if:**

* ✅ It is **mathematically valid** (problem, answer, hints pass the checker)
* ❌ And the **target model fails** to produce a semantically equivalent answer

Prompts that are valid but **solved correctly** by the model are **discarded**.

---

## 📌 To-Do / Future Enhancements

* [ ] **Web Search (via MCP)**
  Incorporate external knowledge to create more realistic prompts.

* [ ] **Rejected Prompt Database**
  Track model-passed problems for regression and fine-tuning.

* [ ] **Expanding Taxonomy**
  Add capability for greater taxonomy of math domains.

* [ ] **Reviewer UI**
  Build a dashboard to browse, rate, or audit prompts manually.

* [ ] **Difficulty Calibration**
  Use token curves or semantic metrics to score complexity.

* [ ] **Prompt Variants**
  Generate multiple mutations of each validated prompt.

---

## 🛠 Debugging Tips

* Gemini sometimes emits invalid JSON. The script will retry until it receives clean output.
* Hints are now stored as a **list of strings**, not a dictionary.
* If your laptop sleeps, the script may freeze mid-run. Disable sleep or run on a persistent machine.
* To debug what Gemini is returning, uncomment the print statement in `generate_hints()`.

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