# 🧠 Core Logic – Synthetic Prompt Generation Engine

This module implements the core logic of a multi-stage agent pipeline that produces **mathematically valid**, **LLM-breaking** math problems. It features three distinct LLM roles:

- **Engineer**: Generates math problems, answers, and hints
- **Checker**: Validates problem structure and evaluates model answers
- **Target Model**: Attempts to solve the problem

Only problems that are both **valid** and **unsolved by the target model** are accepted. If enabled, the system also augments accepted problems with **similarity metadata** using web search and GPT reranking.

---

## 📁 Directory Structure

```

core/
├── checker/
│   └── validate\_prompt.py            # Validates problem and target model answer
├── engineer/
│   └── generate\_prompt.py            # Generates problems, answers, and hints
├── llm/
│   ├── llm\_dispatch.py               # Role-based dispatcher
│   └── openai\_utils.py               # Token-aware OpenAI wrapper
├── orchestration/
│   ├── generate\_batch.py             # Batch generation loop
│   └── evaluate\_target\_model.py      # Target model solver
├── search/
│   ├── agent.py                      # GPT reranker over Tavily results
│   ├── tavily\_search.py              # Tavily API search interface
│   ├── search\_similarity.py          # Similarity scoring orchestrator
│   └── **init**.py                   # Exports score\_similarity()
├── cli/
│   ├── interface.py                  # Batch mode CLI
│   └── run\_interactive.py            # Interactive experimentation
├── runner.py                         # Entrypoint for backend or service integration

````

---

## 🧠 Engineering: `engineer/generate_prompt.py`

```python
generate_full_problem(seed, subject, topic, provider, model_name) → dict
````

* Generates `problem`, `answer`, `hints` (as a list of strings)
* Uses structured prompts (from `system_messages.py`)
* Validates output format
* Returns:

  * `problem`, `answer`, `hints`
  * `tokens_prompt`, `tokens_completion`, `raw_output`, `raw_prompt`

---

## ✅ Validation: `checker/validate_prompt.py`

```python
validate_problem(problem_data, mode, provider, model_name) → dict
```

Modes:

* `"initial"`: checks formatting, structure, and hint validity
* `"equivalence_check"`: compares target model output to correct answer

Returns:

```json
{
  "valid": true,
  "reason": "...",
  "corrected_hints": [...],
  "tokens_prompt": 123,
  "tokens_completion": 456
}
```

---

## 🤖 Evaluation: `orchestration/evaluate_target_model.py`

```python
model_attempts_answer(problem: str, model_config: dict) → dict
```

* Sends the problem to a target LLM
* Returns:

  * `output` (target model answer)
  * `tokens_prompt`, `tokens_completion`

---

## 🔀 Role Dispatcher: `llm/llm_dispatch.py`

Centralizes model-specific logic and routes all LLM calls.

```python
call_engineer(...)
call_checker(..., mode)
call_target_model(...)
```

All calls return output + token usage.

---

## 🌀 Batch Loop: `orchestration/generate_batch.py`

```python
run_generation_pipeline(config: dict) → (valid, discarded, cost_tracker)
```

Pipeline:

1. Sample subject/topic from taxonomy (or override)
2. (Optional) Run web search for seed prompt
3. Engineer generates a problem
4. Checker validates it
5. Target model attempts it
6. Checker compares answers
7. If accepted and `use_search=True`, similarity metadata is added

Tracks:

* Accepted vs discarded prompts
* Per-model token usage
* Cost per provider
* Search metadata

---

## 🔍 Search Similarity (Optional)

Located in `core/search/`. Adds relevance metadata to accepted prompts by comparing them to real math forum questions.

### 🔧 Key Components

* `tavily_search.py`: Sends queries to Tavily with `include_answer=True`
* `agent.py`: Uses GPT to score similarity between generated problems and Tavily results
* `search_similarity.py`: Orchestrates search + reranking
* `__init__.py`: Exports `score_similarity()`

### ➕ Output Fields (if enabled)

Each valid prompt includes:

```json
{
  "similarity_score": 0.82,
  "top_matches": [
    {"title": "...", "content": "..."},
    ...
  ]
}
```

---

## 💰 Cost Tracking

Handled via `utils/costs.py`, with full token and price tracking:

* ✅ OpenAI (chat + responses)
* ✅ Gemini (estimated from char count)
* ✅ DeepSeek

Stored in `.costs.json` per run.

---

## 🧪 CLI Entry Points

* `interface.py`: Run from YAML config
* `run_interactive.py`: Manual entry for experimentation

All results saved to:

```
results/<run_id>/
```

---

## ✅ Acceptance Criteria

A prompt is **accepted** only if:

* It passes checker validation
* The target model answers incorrectly (i.e., is "broken")
* \[Optional] Search metadata can be added afterward

---

## 📂 Output Files

```
results/
└── run_2025_07_03_14_15_00/
    ├── valid.json         # Accepted + validated + model-breaking
    ├── discarded.json     # Invalid or target-model-solved
    └── costs.json         # Token usage + pricing metadata
```

---

## 🔐 Environment Variables

Use `.env` at the project root:

```dotenv
OPENAI_KEY=...
GEMINI_KEY=...
DEEPSEEK_KEY=...
TAVILY_API_KEY=...
```

```