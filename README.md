Here is a comprehensive README for your **Synthetic Prompt Agent** project. It captures the full pipeline, modular architecture, API usage, and key developer notes:

---

# 🧠 Synthetic Prompt Agent

A modular framework for generating, validating, and filtering high-quality synthetic math prompts to stress-test LLMs. This system orchestrates multiple LLMs (e.g., OpenAI, Gemini, DeepSeek) to produce mastery-level questions with hints, verify their correctness, and assess whether a target model fails to solve them correctly.

---

## 🚀 Key Features

* **Multi-LLM Orchestration**: Separate roles for *engineer*, *checker*, and *target* models.
* **Strict Output Validation**: Ensures correctness and format adherence via semantic and structural checks.
* **Model Breaking Logic**: Accepts only those valid problems that the target model answers incorrectly.
* **Hint Generation and Repair**: Automatically retries if hint generation fails.
* **Cost Tracking**: Tracks and logs token usage per model.
* **FastAPI Backend**: Production-ready API with strict Pydantic schemas.
* **CLI Support**: Interactive testing and batch generation via terminal.
* **Modular Architecture**: Clean separation of LLM logic, pipeline orchestration, and utilities.

---

## 🗂 Project Structure

```
synthetic_prompt_agent/
├── core/                  # Core logic for prompt generation, validation, evaluation
│   ├── generate_prompt.py
│   ├── validate_prompt.py
│   ├── evaluate_target_model.py
│   ├── llm/               # Model-specific dispatchers and cost trackers
│   │   ├── llm_dispatch.py
│   │   ├── openai_utils.py
│   │   └── ...
├── utils/                 # Utility functions
│   ├── taxonomy.py
│   ├── cost_tracker.py
│   ├── validation.py
│   └── ...
├── app/                   # FastAPI backend
│   ├── main.py
│   ├── routes.py
│   ├── schemas.py
│   └── pipeline_service.py
├── cli/                   # CLI interface
│   ├── run_interactive.py
│   └── ...
├── save_results.py        # Handles saving valid, discarded, and cost logs
├── generate_batch.py      # Main entrypoint for generating a batch of prompts
├── requirements.txt
├── README.md              # ← You're here
└── ...
```

---

## ⚙️ How It Works

1. **Input**: A configuration specifying:

   * Desired number of prompts
   * Model configurations for engineer, checker, and target
   * Optional `taxonomy` (subject/topic) for sampling

2. **Engineer Role**:

   * Generates problem, answer, and list of hints
   * Retries if hints are empty

3. **Validation Stage**:

   * Checks format, correctness, and mathematical validity
   * Ensures `hints` is a non-empty `List[str]`

4. **Target Model Evaluation**:

   * Model attempts the problem
   * Answer is compared semantically with ground truth

5. **Final Filtering**:

   * Only prompts that are **valid** and **break the target model** are saved as `valid.json`
   * Others go to `discarded.json`

6. **Cost Logging**:

   * Token usage is logged per model and saved to `costs.json`

---

## 🧪 Run a Batch from CLI

```bash
python generate_batch.py \
    --num_prompts 10 \
    --engineer_model '{"provider": "gemini", "model": "gemini-2.5-pro-preview-03-25"}' \
    --checker_model '{"provider": "deepseek", "model": "deepseek-reasoner"}' \
    --target_model '{"provider": "openai", "model": "o3"}' \
    --taxonomy taxonomy/math_taxonomy.json
```

---

## 🌐 API Usage (FastAPI)

### 🔗 POST `/generate`

Generate a batch of prompts using your configuration.

#### Request

```json
{
  "num_prompts": 5,
  "engineer_model": {
    "provider": "gemini",
    "model": "gemini-2.5-pro-preview-03-25"
  },
  "checker_model": {
    "provider": "deepseek",
    "model": "deepseek-reasoner"
  },
  "target_model": {
    "provider": "openai",
    "model": "o3"
  },
  "taxonomy": {
    "Algebra": ["Polynomials", "Inequalities"]
  }
}
```

#### Response

```json
{
  "run_id": "20250626_183721",
  "num_accepted": 4,
  "num_attempted": 5,
  "valid_problems": [ ... ],
  "discarded_problems": [ ... ]
}
```

---

## 🧾 Output Files

Each run produces:

* `valid.json`: Fully validated, target-broken prompts
* `discarded.json`: Invalid or solved by target
* `costs.json`: Token usage and cost data (not exposed via API)

Files are saved to `./output/<run_id>/`.

---

## 🧠 Model Configuration

Each model is passed explicitly as:

```json
{
  "provider": "openai" | "gemini" | "deepseek",
  "model": "o3" | "gemini-2.5-pro-preview-03-25" | ...
}
```

This design enforces transparency and allows local testing before deployment.

---

## 🧰 Developer Notes

* Add new models by updating `llm_dispatch.py` and respective utility modules.
* All token tracking is centralized via `CostTracker`.
* Run-level logic should go through `generate_batch.py` or `pipeline_service.py`.

---

## ✅ TODO / Roadmap

* [ ] Database logging & search
* [ ] `/progress/{run_id}` endpoint
* [ ] Frontend dashboard (Django or React)
* [ ] Test suite for all core modules
* [ ] Web search & Google proof augmentation

---

##  Contributors

* Project Lead: **You**
* Architected with: OpenAI, Gemini, DeepSeek APIs

---