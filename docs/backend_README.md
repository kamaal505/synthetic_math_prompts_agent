# 🚀 FastAPI Backend – Synthetic Prompt Agent

This module exposes a FastAPI interface for generating math prompts via the core synthetic prompt pipeline. It enables external systems (like frontends, dashboards, or other services) to interact with the generator through a simple HTTP API.

---

## 📁 Directory Structure

```
app/
├── api/
│   └── routes.py              # Defines API endpoints
├── models/
│   └── schemas.py             # Pydantic schemas for request/response
├── services/
│   └── pipeline_service.py    # Converts request into core config + runs pipeline
└── main.py                    # FastAPI app entrypoint
```

---

## 🔧 How It Works

The FastAPI app exposes a single POST endpoint at `/generate`, which:

1. Accepts a `GenerationRequest` payload (includes number of problems, models, and topic/taxonomy)
2. Converts that payload into the internal config format
3. Calls the core runner (`run_pipeline_from_config`)
4. Returns:

   * All accepted prompts (model-breaking and validated)
   * All rejected prompts
   * Summary metadata

---

## 🔁 Endpoint Summary

### `POST /generate`

Generates a batch of synthetic prompts and returns both accepted and discarded examples.

* **Input**: JSON body matching `GenerationRequest`
* **Output**: JSON response as `GenerationResponse`

---

## 🧾 Request Schema: `GenerationRequest`

```json
{
  "num_problems": 1,
  "engineer_model": {
    "provider": "gemini",
    "model_name": "gemini-2.5-pro"
  },
  "checker_model": {
    "provider": "openai",
    "model_name": "o3-mini"
  },
  "target_model": {
    "provider": "openai",
    "model_name": "o1"
  },
  "taxonomy": {
    "Algebra (High School)": [
      "Linear Equations and Inequalities",
      "Quadratic Equations and Functions"
    ],
    "Complex Analysis": [
      "Contour Integration",
      "Analytic Continuation"
    ]
  }
}
```

### 🧠 Field Descriptions

| Field            | Type                     | Required | Description                                      |
| ---------------- | ------------------------ | -------- | ------------------------------------------------ |
| `num_problems`   | int                      | ✅        | How many prompts to generate                     |
| `engineer_model` | `{provider, model_name}` | ✅        | LLM to generate problems                         |
| `checker_model`  | `{provider, model_name}` | ✅        | LLM to validate outputs and answers              |
| `target_model`   | `{provider, model_name}` | ✅        | LLM to challenge with the generated problem      |
| `subject`        | str                      | ❌        | Specific subject (used if `taxonomy` is omitted) |
| `topic`          | str                      | ❌        | Specific topic (same as above)                   |
| `taxonomy`       | dict\[str, list\[str]]   | ❌        | Mapping of subjects to topic lists               |

---

## 📤 Response Schema: `GenerationResponse`

```json
{
  "valid_prompts": [
    {
      "subject": "Algebra",
      "topic": "Galois Theory",
      "problem": "...",
      "answer": "...",
      "hints": {
        "0": "...",
        "1": "...",
        "2": "..."
      },
      "hints_were_corrected": false,
      "target_model_answer": "..."
    }
  ],
  "discarded_prompts": [
    {
      "rejection_reason": "Model solved correctly",
      ...
    }
  ],
  "metadata": {
    "total_attempted": 5,
    "total_accepted": 2
  }
}
```

---

## ⚙️ How to Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Make sure your project also includes the `core/` logic and `utils/`, since this backend depends on them.

### 2. Set environment variables

Create a `.env` file with your API keys:

```dotenv
OPENAI_KEY=your-openai-key
GEMINI_KEY=your-gemini-key
DEEPSEEK_KEY=your-fireworks-api-key
```

### 3. Start the FastAPI app

```bash
uvicorn app.main:app --reload
```

This will start the API server at:

```
http://127.0.0.1:8000
```

---

## 🔬 Example: Test with `curl`

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "num_problems": 1,
    "engineer_model": {
      "provider": "gemini",
      "model_name": "gemini-2.5-pro"
    },
    "checker_model": {
      "provider": "openai",
      "model_name": "o3-mini"
    },
    "target_model": {
      "provider": "openai",
      "model_name": "o1"
    },
    "taxonomy": {
      "Linear Algebra": ["Spectral Theorem"]
    }
  }'
```

---

## 🧼 Notes

* The backend is stateless — no database is used (yet).
* You can swap out `model_name` and `provider` to test other LLMs.
* Logs and runtime behavior will reflect the output from the core pipeline (e.g. approvals, discards, model failures).

---