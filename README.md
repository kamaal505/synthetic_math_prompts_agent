# 🧠 Synthetic Prompt Agent

A multi-stage LLM framework for generating **mathematically valid**, **LLM-breaking** problems. This system automates the creation, validation, and evaluation of STEM prompts, and exposes both CLI and REST API interfaces. Each problem is checked for correctness, pedagogical quality, and ability to fool a target LLM.

---

## 🚧 Motivation

High-quality automated prompt generation is hard. This agent focuses on:

- 🔍 Engineering math problems with structured hints
- ✅ Validating them for correctness and clarity
- 🧪 Testing whether LLMs like O3, Gemini, or DeepSeek can solve them
- 💥 Accepting only those problems that *break* the target model

Optionally, it also performs **search-based similarity scoring** to avoid duplicates.

---

## 🧱 Architecture Overview

```

project-root/
├── core/             # Core orchestration + generation logic
├── utils/            # Shared utilities (costs, prompts, taxonomy, etc.)
├── app/              # FastAPI backend for serving pipeline
├── tests/            # Unit tests
├── results/          # Output from each generation run
├── .env              # API keys + config
└── requirements.txt  # Python dependencies

````

---

## ⚙️ Components

### 🧠 `core/`

Implements the three-agent loop:

| Role       | Purpose                                   |
|------------|-------------------------------------------|
| Engineer   | Generates math problem, answer, and hints |
| Checker    | Validates content and final answer        |
| Target     | Attempts to solve the problem             |

Also includes:

- Batch orchestration
- CLI interface
- Token + cost tracking
- Search augmentation (`Tavily + GPT reranker`)

📄 See: [`core/README.md`](core/README.md)

---

### 🛠️ `utils/`

Shared support logic:

- ✅ Config + taxonomy loading
- 💰 Token accounting and cost estimation
- 🧼 Robust JSON parsing from LLMs
- 🚨 Centralized logging and error handling
- 📎 Embedding + cosine similarity tools

📄 See: [`utils/README.md`](utils/README.md)

---

### 🚀 `app/` (FastAPI Backend)

Exposes a REST API for:

- Starting a new generation batch
- Tracking batch status and cost
- Querying generated problems
- Managing metadata (target model, similarity, etc.)

Database-backed via SQLAlchemy.

📄 See: [`app/README.md`](app/README.md)

---

### 🧪 `tests/`

Unit tests for:

- Generation logic
- Prompt validation
- Cost tracking
- API endpoints

📄 See: [`tests/README.md`](tests/README.md)

---

## 🔐 API Keys

Create a `.env` file in the root directory:

```env
OPENAI_KEY=your-openai-key
GEMINI_KEY=your-gemini-key
DEEPSEEK_KEY=your-fireworks-key
TAVILY_API_KEY=your-tavily-key
DATABASE_URL=sqlite:///./database/math_agent.db
````

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Run CLI (Core Pipeline)

Run interactively:

```bash
python core/cli/run_interactive.py
```

Or use a YAML config:

```bash
python core/cli/interface.py --config configs/sample_config.yaml
```

Results saved to:

```
results/
└── run_2025_07_03_14_15_00/
    ├── valid.json
    ├── discarded.json
    └── costs.json
```

---

### 3. Run FastAPI Backend

```bash
uvicorn app.main:app --reload
```

Now visit: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

You can:

* POST to `/api/generation/` to start batch generation
* GET `/api/generation/status/{batch_id}` to track progress
* Query prompts via `/api/problems/` or `/api/batches/`

---

## 📦 Example: Start a Batch via API

```bash
curl -X POST http://localhost:8000/api/generation \
  -H "Content-Type: application/json" \
  -d '{
    "num_problems": 5,
    "engineer_model": {"provider": "gemini", "model_name": "gemini-2.5-pro"},
    "checker_model": {"provider": "openai", "model_name": "o3"},
    "target_model": {"provider": "openai", "model_name": "o3"},
    "taxonomy": { "Algebra": ["Quadratics"] },
    "use_search": true
  }'
```

---

## 📈 Output Structure

Each accepted prompt includes:

* ✅ Validated `problem`, `answer`, `hints`
* 💥 Target model output
* 📎 Similar problems (via Tavily + GPT)
* 💰 Cost + token usage
* 🧠 Embedding vector (for deduplication)

---

## 🧠 Acceptance Criteria

A problem is accepted if:

* It passes all validation checks
* The target model fails to solve it
* (Optional) Similarity is below threshold to known problems

---

## 💬 Status Endpoints

* `/api/` → Welcome message
* `/api/health` → Health check
* `/api/generation/status/{batch_id}` → Generation progress
* `/api/problems/` → Query prompts with filters
* `/api/batches/` → View batch summary + statistics

---

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 📄 License

MIT License

---

## 🙌 Credits

Mirza Kamaal
Tom Mathews
Mintesnote Bankisra

```