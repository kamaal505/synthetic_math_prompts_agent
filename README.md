# 🧠 Synthetic Math Prompts Agent

A sophisticated multi-stage LLM framework for generating **mathematically valid**, **LLM-breaking** problems. This system automates the creation, validation, and evaluation of STEM prompts using an agent-based architecture, with both CLI and REST API interfaces. Each problem is rigorously checked for correctness, pedagogical quality, and ability to challenge target LLMs.

---

## 🚧 Motivation

High-quality automated prompt generation is challenging. This agent focuses on:

- 🔍 **Engineering** math problems with structured hints and adversarial techniques
- ✅ **Validating** them for correctness, clarity, and pedagogical value
- 🧪 **Testing** whether advanced LLMs like O3, Gemini, or DeepSeek can solve them
- 💥 **Accepting** only those problems that successfully challenge the target model
- 🎯 **Curriculum-based** generation with intelligent topic and difficulty selection
- 🔄 **Performance optimization** with caching, concurrent processing, and adaptive threading

Optionally performs **search-based similarity scoring** to avoid duplicates and **CAS verification** for mathematical accuracy.

---

## 🏗️ Enhanced Architecture

The system uses a modern **agent-based architecture** with centralized configuration management and performance monitoring:

```
project-root/
├── core/                    # Agent-based generation pipeline
│   ├── agents.py           # EngineerAgent, CheckerAgent, TargetAgent
│   ├── llm/                # Centralized LLM client with caching
│   ├── orchestration/      # Concurrent processing & batch generation
│   ├── checker/            # CAS validation & prompt checking
│   └── search/             # Similarity detection & search
├── utils/                   # Enhanced utilities & performance monitoring
│   ├── config_manager.py   # Singleton configuration management
│   ├── performance_monitor.py # Concurrent processing metrics
│   ├── curriculum_strategy.py # Intelligent topic selection
│   └── taxonomy.py         # Enhanced nested taxonomy support
├── app/                     # FastAPI backend with database
├── tests/                   # Comprehensive unit & integration tests
├── config/                  # YAML-based configuration
└── taxonomy/               # Enhanced math taxonomy structure
```

---

## ⚙️ Core Components

### 🤖 Agent-Based Architecture

**Three specialized agents** handle different aspects of problem generation:

| Agent | Purpose | Key Features |
|-------|---------|--------------|
| **EngineerAgent** | Generates math problems with hints | • Few-shot examples<br>• Adversarial techniques<br>• Curriculum-guided selection |
| **CheckerAgent** | Validates content and answers | • CAS verification (SymPy)<br>• Pedagogical quality checks<br>• JSON structure validation |
| **TargetAgent** | Attempts to solve problems | • Deterministic solving (temp=0)<br>• Consistent evaluation<br>• Performance tracking |

### 🧠 Enhanced LLM Integration

- **Centralized LLM Client** with unified API for OpenAI, Gemini, and DeepSeek
- **Intelligent Caching** with temperature-aware cache keys
- **Retry Logic** with exponential backoff and jitter for concurrent scenarios
- **Performance Monitoring** with detailed metrics and thread tracking

### 🎯 Curriculum Strategy

- **Intelligent Topic Selection** based on coverage and difficulty balance
- **Adaptive Difficulty Weighting** (High School: 30%, Undergraduate: 40%, Graduate: 25%, Research: 5%)
- **Progressive Learning** with balanced topic coverage tracking
- **Enhanced Taxonomy** with nested subject→topic→difficulty structure

### ⚡ Performance Optimizations

- **Concurrent Processing** with adaptive thread pool management
- **Batch Generation** for improved API efficiency
- **Pre-filtering Heuristics** to skip trivial problems
- **Similarity Caching** with offline embedding index support

📄 See: [`core/README.md`](core/README.md)

---

### 🛠️ Enhanced Utilities

Advanced support infrastructure:

- ✅ **Singleton Configuration Management** with thread-safe access
- 💰 **Advanced Cost Tracking** with provider-specific pricing
- 🧼 **Robust JSON Parsing** with automated repair capabilities
- 🚨 **Structured Logging** with contextual information
- 📊 **Performance Monitoring** for concurrent operations
- 🎓 **Curriculum Strategy** for intelligent problem selection
- 📎 **Similarity Detection** with embedding-based comparison

📄 See: [`utils/README.md`](utils/README.md)

---

### 🚀 FastAPI Backend

Production-ready REST API with:

- **Batch Management** with real-time status tracking
- **Database Integration** using SQLAlchemy with proper schemas
- **Concurrent Generation** with progress monitoring
- **Cost Analytics** and usage statistics
- **Problem Querying** with advanced filtering
- **Health Monitoring** and system diagnostics

📄 See: [`app/README.md`](app/README.md)

---

### 🧪 Comprehensive Testing

Extensive test coverage including:

- **Unit Tests** for all core components
- **Integration Tests** for end-to-end workflows
- **Performance Tests** for concurrent processing
- **Mock-based Testing** for external API interactions
- **CAS Validation Tests** for mathematical accuracy

📄 See: [`tests/README.md`](tests/README.md)

---

## 🔐 Configuration & Setup

### Environment Variables

Create a `.env` file in the root directory:

```env
# LLM API Keys
OPENAI_KEY=your-openai-key
GEMINI_KEY=your-gemini-key
DEEPSEEK_KEY=your-fireworks-key

# Search & External APIs
TAVILY_API_KEY=your-tavily-key

# Database
DATABASE_URL=sqlite:///./database/math_agent.db

# Optional Performance Settings
MAX_CONCURRENT_THREADS=8
CACHE_ENABLED=true
SIMILARITY_THRESHOLD=0.85
```

### Configuration Files

The system uses YAML-based configuration in [`config/settings.yaml`](config/settings.yaml):

```yaml
# Model configurations for each agent
models:
  engineer:
    provider: "gemini"
    model_name: "gemini-2.5-pro"
  checker:
    provider: "openai"
    model_name: "o3"
  target:
    provider: "openai"
    model_name: "o3"

# Performance settings
performance:
  max_workers: 8
  batch_size: 5
  enable_caching: true
  
# Curriculum settings
curriculum:
  difficulty_weights:
    "High School": 0.3
    "Undergraduate": 0.4
    "Graduate": 0.25
    "Research": 0.05
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
# Using uv (recommended - faster installs)
uv pip install -r requirements.txt

# Alternative: using pip
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Create database tables
python -c "from app.models.database import init_db; init_db()"
```

---

### 3. CLI Usage (Enhanced)

**Interactive Mode** with curriculum strategy:

```bash
python core/cli/run_interactive.py
```

**Configuration-based** with YAML settings:

```bash
python core/cli/interface.py --config config/settings.yaml
```

**Results Structure:**

```
results/
└── run_2025_07_04_14_30_00/
    ├── valid.json              # Accepted problems
    ├── discarded.json          # Rejected problems
    ├── costs.json              # Detailed cost breakdown
    ├── performance_metrics.json # Concurrent processing stats
    └── curriculum_stats.json   # Topic coverage analysis
```

---

### 4. FastAPI Backend (Production-Ready)

**Start the server:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

**Key Endpoints:**

- `POST /api/generation/` → Start batch generation with curriculum
- `GET /api/generation/status/{batch_id}` → Real-time progress tracking
- `GET /api/problems/` → Query problems with advanced filters
- `GET /api/batches/` → Batch analytics and statistics
- `GET /api/health` → System health and performance metrics

---

## 📦 Enhanced API Examples

### Start Advanced Batch Generation

```bash
curl -X POST http://localhost:8000/api/generation \
  -H "Content-Type: application/json" \
  -d '{
    "num_problems": 10,
    "engineer_model": {"provider": "gemini", "model_name": "gemini-2.5-pro"},
    "checker_model": {"provider": "openai", "model_name": "o3"},
    "target_model": {"provider": "openai", "model_name": "o3"},
    "taxonomy": {
      "Linear Algebra": ["Matrix Operations", "Eigenvalues"],
      "Calculus": ["Integration", "Differential Equations"]
    },
    "use_search": true,
    "enable_cas_validation": true,
    "max_workers": 8
  }'
```

### Query Problems with Filters

```bash
# Get problems by difficulty and subject
curl "http://localhost:8000/api/problems/?difficulty=Undergraduate&subject=Linear%20Algebra&limit=5"

# Get problems that failed target model
curl "http://localhost:8000/api/problems/?target_success=false&order_by=created_at"
```

---

## 📊 Enhanced Output Structure

Each generated problem includes comprehensive metadata:

```json
{
  "problem": "Find the eigenvalues of the matrix...",
  "answer": "λ₁ = 3, λ₂ = -1",
  "hints": ["Consider the characteristic polynomial", "Factor the quadratic"],
  "metadata": {
    "subject": "Linear Algebra",
    "topic": "Eigenvalues",
    "difficulty": "Undergraduate",
    "generation_stats": {
      "tokens_used": 1250,
      "generation_time": 2.3,
      "validation_time": 0.8,
      "target_evaluation_time": 1.1
    }
  },
  "validation": {
    "checker_approved": true,
    "cas_verified": true,
    "pedagogical_score": 0.87
  },
  "target_evaluation": {
    "model_output": "I need to find the characteristic polynomial...",
    "success": false,
    "confidence": 0.23
  },
  "similarity": {
    "max_similarity": 0.34,
    "similar_problems": [...],
    "embedding": [0.1, -0.3, ...]
  },
  "costs": {
    "total_cost": 0.0045,
    "breakdown": {...}
  }
}
```

---

## 🎯 Enhanced Acceptance Criteria

A problem is accepted if it meets **all** criteria:

✅ **Validation Checks:**

- Passes CheckerAgent quality assessment
- (Optional) CAS verification confirms mathematical accuracy
- Proper JSON structure and required fields
- Pedagogical quality score above threshold

✅ **Target Model Challenge:**

- Target model fails to solve correctly
- Model confidence below success threshold
- Demonstrates genuine difficulty, not formatting issues

✅ **Uniqueness (Optional):**

- Similarity score below threshold vs. existing problems
- Embedding-based deduplication
- Topic diversity within curriculum strategy

---

## 🔧 Advanced Features

### Agent-Based Architecture

- **EngineerAgent:** Generates problems with few-shot examples and adversarial techniques
- **CheckerAgent:** Validates with CAS verification and pedagogical scoring
- **TargetAgent:** Deterministic evaluation with consistent temperature settings

### Performance Optimizations

- **Concurrent Processing:** Adaptive thread pool with performance monitoring
- **Intelligent Caching:** Temperature-aware cache keys with hit rate tracking
- **Batch Generation:** Improved API efficiency with parallel validation

### Curriculum Strategy

- **Balanced Topic Selection:** Ensures diverse coverage across subjects
- **Adaptive Difficulty:** Dynamic weighting based on generation history
- **Progressive Learning:** Tracks topic coverage for educational coherence

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit_tests/          # Unit tests only
pytest tests/test_performance_enhancements.py  # Performance tests
```

---

## 📊 Performance Monitoring

The system includes comprehensive performance monitoring:

- **Concurrent Processing Metrics:** Thread utilization, throughput, latency
- **Cache Performance:** Hit rates, lookup times, memory usage
- **Cost Analytics:** Token usage, API costs, efficiency metrics
- **Generation Quality:** Success rates, validation scores, curriculum balance

---

## 💬 API Status Endpoints

- `/api/` → Welcome message and system info
- `/api/health` → Health check with performance metrics
- `/api/generation/status/{batch_id}` → Real-time generation progress
- `/api/problems/` → Query problems with advanced filtering
- `/api/batches/` → Batch analytics and statistics

---

## 📄 License

MIT License

---

## 🙌 Credits

**Core Development Team:**

- Mirza Kamaal
- Tom Mathews
- Mintesnote Bankisra

**Enhanced with:**

- Agent-based architecture design
- Performance optimization strategies
- Curriculum-based generation algorithms
- Comprehensive testing framework
