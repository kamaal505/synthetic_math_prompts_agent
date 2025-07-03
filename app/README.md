# 🚀 FastAPI Backend – Synthetic Prompt Agent

This module exposes a REST API to orchestrate, track, and manage synthetic math prompt generation. It supports:

- Launching LLM-based generation runs
- Tracking batch progress
- Querying all generated prompts (valid, discarded, solved)
- Updating batch metadata and target model
- Storing metadata like cost, similarity, embeddings

---

## 📁 Directory Structure

```

app/
├── api/
│   ├── routes.py              # Main API router
│   ├── batches.py             # /batches – batch management endpoints
│   ├── generation.py          # /generation – start/track generation jobs
│   └── problems.py            # /problems – prompt-level access
├── config.py                  # App settings and validation
├── main.py                    # FastAPI app entrypoint
├── models/
│   ├── database.py            # SQLAlchemy engine + session
│   ├── models.py              # ORM models: Batch, Problem
│   └── schemas.py             # Pydantic schemas
├── services/
│   ├── batch\_service.py       # Batch-related DB logic
│   ├── problem\_service.py     # Problem-related DB logic
│   └── pipeline\_service.py    # Launches and tracks core pipeline

````

---

## 🔌 Key Features

### ✅ Generation (via POST `/api/generation/`)

Starts a generation run with background execution:

```json
{
  "num_problems": 10,
  "engineer_model": {"provider": "gemini", "model_name": "gemini-2.5-pro"},
  "checker_model": {"provider": "openai", "model_name": "o3"},
  "target_model": {"provider": "openai", "model_name": "o3"},
  "taxonomy": { "Algebra": ["Quadratics"] },
  "use_search": true
}
````

* Launches `core.runner.run_pipeline_from_config()` as a background task
* Persists each valid/discarded prompt to the DB
* Saves embeddings, similarity matches, and batch cost

---

### 📦 Batches API – `/api/batches`

Manage generation batches and metadata.

* `GET /batches/` – List all batches with prompt stats
* `GET /batches/{batch_id}` – Fetch a specific batch + stats
* `PATCH /batches/{batch_id}/target-model` – Update target model
* `DELETE /batches/{batch_id}` – Delete a batch
* `GET /batches/problems/count` – Get total prompt count or per-batch

---

### 🧠 Problems API – `/api/problems`

Access and filter problems across all batches.

* `GET /problems/` – Paginated query with filters (`batch_id`, `status`)
* `GET /problems/problem/{id}` – Fetch single problem
* `GET /problems/batch/{batch_id}/problems` – All problems for a batch
* `GET /problems/all` – All problems (unlimited; use with caution)

Each problem includes:

* Rejection reason
* Target model answer
* Embedding vector
* Similarity matches
* Cost and status (`valid`, `discarded`, etc.)

---

### 📊 Generation Status – `/api/generation/status/{batch_id}`

Returns live progress of a running or completed batch:

```json
{
  "batch_id": 12,
  "total_needed": 10,
  "valid_generated": 8,
  "total_generated": 14,
  "progress_percentage": 80.0,
  "stats": {
    "valid": 8,
    "discarded": 6
  },
  "batch_cost": 0.0952,
  "status": "in_progress"
}
```

---

## 🧾 Schemas

Located in `app/models/schemas.py`. Includes:

* `GenerationRequest` / `GenerationResponse`
* `Batch`, `BatchWithStats`
* `Problem`, `ProblemResponse`
* `PipelineConfig`, `ModelConfig`
* `GenerationStatus`

---

## 🧱 Database Models

### `Batch`

* Taxonomy JSON
* Pipeline config (engineer, checker, target)
* Number of problems
* Batch-level cost
* Created/updated timestamps

### `Problem`

* Subject, topic, problem, answer, hints
* Rejection reason
* Status: `valid`, `discarded`, or `solved`
* Embeddings
* Similar problems
* Token-level cost
* Target model output

---

## ⚙️ Configuration – `config.py`

Reads `.env` file and exposes global `settings` object:

```dotenv
OPENAI_KEY=...
GEMINI_KEY=...
DEEPSEEK_KEY=...
DATABASE_URL=sqlite:///./database/math_agent.db
```

Also sets:

* `SIMILARITY_THRESHOLD = 0.82`
* `EMBEDDING_MODEL = "text-embedding-3-small"`

---

## 🩺 Health Check

```
GET / → { "message": "Synthetic Math Prompts API" }
GET /health → { "status": "healthy" }
```

---

## 🚀 Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` file with API keys

3. Run the server:

```bash
uvicorn app.main:app --reload
```

The API will be available at: [http://localhost:8000/api](http://localhost:8000/api)

---

## 🧪 Example Query: List all valid problems from a batch

```http
GET /api/problems?batch_id=12&status=valid
```

---

## 🧪 Example: Start a new batch

```bash
curl -X POST http://localhost:8000/api/generation \
  -H "Content-Type: application/json" \
  -d '{
    "num_problems": 5,
    "engineer_model": { "provider": "gemini", "model_name": "gemini-2.5-pro" },
    "checker_model": { "provider": "openai", "model_name": "o3" },
    "target_model": { "provider": "openai", "model_name": "o3" },
    "taxonomy": { "Algebra": ["Quadratics"] },
    "use_search": true
  }'
```

---