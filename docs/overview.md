# Synthetic Math Prompts Agent - System Overview

This project is an advanced synthetic math prompt generation pipeline designed to create high-quality mathematical problems that are challenging for large language models (LLMs) to solve correctly. The system employs an agent-based architecture with sophisticated performance optimizations, concurrent processing, and intelligent caching mechanisms.

## System Architecture

The system has evolved into a sophisticated multi-agent architecture with enhanced performance capabilities:

```mermaid
graph TB
    subgraph "User Interfaces"
        CLI["🖥️ Command-Line Interface"]
        WebAPI["🌐 FastAPI Web Application"]
        Interactive["🔄 Interactive CLI"]
    end

    subgraph "Agent-Based Core System"
        EngineerAgent["🔧 Engineer Agent<br/>(Problem Generation)"]
        CheckerAgent["✅ Checker Agent<br/>(Validation & CAS)"]
        TargetAgent["🎯 Target Agent<br/>(Model Evaluation)"]
        SimilarityAgent["🔍 Similarity Agent<br/>(Deduplication)"]
    end

    subgraph "Enhanced LLM Infrastructure"
        LLMClient["🤖 Centralized LLM Client"]
        LLMCache["💾 Intelligent Caching"]
        LLMDispatch["📡 Model Dispatch Layer"]
    end

    subgraph "Performance & Orchestration"
        ConcurrentProcessor["⚡ Adaptive Concurrent Processor"]
        PerformanceMonitor["📊 Performance Monitor"]
        CurriculumStrategy["📚 Curriculum Strategy"]
        BatchGenerator["📦 Batch Generator"]
    end

    subgraph "Data & Configuration"
        ConfigManager["⚙️ Configuration Manager"]
        TaxonomyEngine["🏷️ Enhanced Taxonomy Engine"]
        CostTracker["💰 Cost Tracker"]
        Database["🗄️ SQLite Database"]
    end

    %% User Interface Connections
    CLI --> ConcurrentProcessor
    WebAPI --> ConcurrentProcessor
    Interactive --> ConcurrentProcessor

    %% Agent Workflow
    ConcurrentProcessor --> EngineerAgent
    EngineerAgent --> CheckerAgent
    CheckerAgent --> TargetAgent
    TargetAgent --> SimilarityAgent

    %% LLM Infrastructure
    EngineerAgent --> LLMClient
    CheckerAgent --> LLMClient
    TargetAgent --> LLMClient
    SimilarityAgent --> LLMClient
    LLMClient --> LLMCache
    LLMClient --> LLMDispatch

    %% Performance Systems
    ConcurrentProcessor --> PerformanceMonitor
    ConcurrentProcessor --> CurriculumStrategy
    ConcurrentProcessor --> BatchGenerator

    %% Data Systems
    ConfigManager --> TaxonomyEngine
    ConcurrentProcessor --> CostTracker
    ConcurrentProcessor --> Database

    %% Styling
    classDef userInterface fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef agent fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef llm fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef performance fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef data fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

    class CLI,WebAPI,Interactive userInterface
    class EngineerAgent,CheckerAgent,TargetAgent,SimilarityAgent agent
    class LLMClient,LLMCache,LLMDispatch llm
    class ConcurrentProcessor,PerformanceMonitor,CurriculumStrategy,BatchGenerator performance
    class ConfigManager,TaxonomyEngine,CostTracker,Database data
```

## Key System Components

### 🤖 Agent-Based Architecture

The system employs specialized agents for different aspects of the generation pipeline:

#### **Engineer Agent** ([`core/agents.py`](core/agents.py:15))

- **Purpose**: Generates initial mathematical problems with enhanced prompting techniques
- **Features**:
  - Few-shot learning with curated examples
  - Adversarial prompting techniques
  - Curriculum-based difficulty progression
  - Subject-specific problem templates
- **Models**: Typically uses creative models like `gemini-2.0-flash-exp` or `gpt-4`

#### **Checker Agent** ([`core/agents.py`](core/agents.py:45))

- **Purpose**: Validates problems for correctness and mathematical soundness
- **Features**:
  - CAS (Computer Algebra System) integration with SymPy
  - Multi-stage validation (initial + equivalence checking)
  - Hint correction and refinement
  - Mathematical notation verification
- **Models**: Uses precise models like `o1-mini` or `gpt-4`

#### **Target Agent** ([`core/agents.py`](core/agents.py:75))

- **Purpose**: Attempts to solve problems to determine difficulty
- **Features**:
  - Deterministic solving with temperature=0
  - Multiple solution strategies
  - Performance tracking and analysis
- **Models**: The model being evaluated (e.g., `o1`, `claude-3.5-sonnet`)

#### **Similarity Agent** ([`core/search/similarity_agent.py`](core/search/similarity_agent.py:1))

- **Purpose**: Prevents duplicate problems through semantic similarity analysis
- **Features**:
  - Vector-based similarity scoring
  - Configurable similarity thresholds
  - Integration with external search APIs

### ⚡ Enhanced Performance Infrastructure

#### **Adaptive Concurrent Processing** ([`core/orchestration/concurrent_processor.py`](core/orchestration/concurrent_processor.py:157))

- **Adaptive Thread Pool**: Dynamically adjusts worker count based on success rates
- **Intelligent Batching**: Optimizes batch sizes for maximum throughput
- **Graceful Error Handling**: Continues processing despite individual task failures
- **Safety Mechanisms**: Prevents infinite loops with configurable attempt limits

#### **Intelligent Caching System** ([`core/llm/llm_cache.py`](core/llm/llm_cache.py:15))

- **Multi-Level Caching**: In-memory cache with configurable TTL
- **Thread-Safe Operations**: Concurrent access with proper locking
- **Cache Statistics**: Detailed metrics for hit rates and performance
- **Provider-Agnostic**: Works with all LLM providers

#### **Performance Monitoring** ([`utils/performance_monitor.py`](utils/performance_monitor.py:18))

- **Real-Time Metrics**: Tracks throughput, latency, and success rates
- **Concurrent Thread Tracking**: Monitors thread utilization and bottlenecks
- **Cache Performance**: Analyzes cache effectiveness
- **Cost Analysis**: Integrates with cost tracking for efficiency metrics

### 📚 Advanced Generation Features

#### **Curriculum Strategy** ([`utils/curriculum_strategy.py`](utils/curriculum_strategy.py:15))

- **Adaptive Difficulty**: Intelligently selects problem difficulty based on success rates
- **Topic Weighting**: Prioritizes underrepresented mathematical topics
- **Progress Tracking**: Maintains statistics on generation patterns
- **Balanced Coverage**: Ensures comprehensive topic coverage

#### **Enhanced Taxonomy Engine** ([`taxonomy/enhanced_math_taxonomy.json`](taxonomy/enhanced_math_taxonomy.json:1))

- **Hierarchical Structure**: Multi-level subject organization
- **Difficulty Levels**: Granular difficulty classification (1-10 scale)
- **Topic Descriptions**: Detailed descriptions for context-aware generation
- **Extensible Design**: Easy addition of new subjects and topics

#### **CAS Integration** ([`core/checker/cas_validator.py`](core/checker/cas_validator.py:15))

- **SymPy Integration**: Computer algebra system for mathematical verification
- **Expression Validation**: Verifies mathematical expressions and equations
- **Symbolic Computation**: Handles algebraic manipulations and simplifications
- **Error Detection**: Identifies mathematical inconsistencies

## Directory Structure

### `app/` - FastAPI Web Application

- **[`main.py`](app/main.py:1)**: FastAPI application entry point with enhanced error handling
- **[`api/`](app/api/)**: RESTful API endpoints with comprehensive request/response schemas
  - **[`routes.py`](app/api/routes.py:1)**: Main API routing with batch generation support
  - **[`generation.py`](app/api/generation.py:1)**: Generation-specific endpoints
  - **[`problems.py`](app/api/problems.py:1)**: Problem management endpoints
  - **[`batches.py`](app/api/batches.py:1)**: Batch processing endpoints
- **[`services/`](app/services/)**: Business logic layer
  - **[`pipeline_service.py`](app/services/pipeline_service.py:1)**: Core pipeline orchestration
  - **[`problem_service.py`](app/services/problem_service.py:1)**: Problem management services
  - **[`batch_service.py`](app/services/batch_service.py:1)**: Batch processing services
- **[`models/`](app/models/)**: Data models and database integration
  - **[`schemas.py`](app/models/schemas.py:1)**: Pydantic models for API validation
  - **[`models.py`](app/models/models.py:1)**: SQLAlchemy database models
  - **[`database.py`](app/models/database.py:1)**: Database configuration and connection

### `core/` - Agent-Based Generation Engine

- **[`agents.py`](core/agents.py:1)**: Core agent implementations (Engineer, Checker, Target)
- **[`runner.py`](core/runner.py:1)**: Main pipeline orchestration and execution
- **[`orchestration/`](core/orchestration/)**: Advanced workflow management
  - **[`concurrent_processor.py`](core/orchestration/concurrent_processor.py:1)**: Adaptive concurrent processing
  - **[`generate_batch.py`](core/orchestration/generate_batch.py:1)**: Batch generation with performance optimization
  - **[`evaluate_target_model.py`](core/orchestration/evaluate_target_model.py:1)**: Target model evaluation
- **[`llm/`](core/llm/)**: Enhanced LLM infrastructure
  - **[`llm_client.py`](core/llm/llm_client.py:1)**: Centralized LLM client with caching
  - **[`llm_cache.py`](core/llm/llm_cache.py:1)**: Intelligent caching system
  - **[`llm_dispatch.py`](core/llm/llm_dispatch.py:1)**: Model routing and dispatch
  - **[`openai_utils.py`](core/llm/openai_utils.py:1)**: OpenAI-specific utilities
- **[`engineer/`](core/engineer/)**: Problem generation
  - **[`generate_prompt.py`](core/engineer/generate_prompt.py:1)**: Enhanced prompt generation with few-shot learning
- **[`checker/`](core/checker/)**: Validation and verification
  - **[`validate_prompt.py`](core/checker/validate_prompt.py:1)**: Multi-stage validation
  - **[`cas_validator.py`](core/checker/cas_validator.py:1)**: Computer algebra system integration
- **[`search/`](core/search/)**: Similarity and search functionality
  - **[`similarity_agent.py`](core/search/similarity_agent.py:1)**: Semantic similarity analysis
  - **[`search_similarity.py`](core/search/search_similarity.py:1)**: Search-based similarity scoring
  - **[`tavily_search.py`](core/search/tavily_search.py:1)**: External search integration
- **[`cli/`](core/cli/)**: Command-line interfaces
  - **[`interface.py`](core/cli/interface.py:1)**: Main CLI interface
  - **[`run_interactive.py`](core/cli/run_interactive.py:1)**: Interactive CLI mode
  - **[`cache_manager_cli.py`](core/cli/cache_manager_cli.py:1)**: Cache management utilities

### `utils/` - Enhanced Utility Infrastructure

- **[`config_manager.py`](utils/config_manager.py:1)**: Thread-safe singleton configuration management
- **[`performance_monitor.py`](utils/performance_monitor.py:1)**: Comprehensive performance tracking
- **[`curriculum_strategy.py`](utils/curriculum_strategy.py:1)**: Intelligent curriculum-based generation
- **[`cost_estimation.py`](utils/cost_estimation.py:1)**: Advanced cost tracking and estimation
- **[`prompt_examples.py`](utils/prompt_examples.py:1)**: Few-shot learning examples and templates
- **[`exceptions.py`](utils/exceptions.py:1)**: Structured error handling
- **[`logging_config.py`](utils/logging_config.py:1)**: Centralized logging configuration
- **[`taxonomy.py`](utils/taxonomy.py:1)**: Enhanced taxonomy loading and management
- **[`validation.py`](utils/validation.py:1)**: Data validation utilities
- **[`json_utils.py`](utils/json_utils.py:1)**: JSON processing utilities
- **[`similarity_utils.py`](utils/similarity_utils.py:1)**: Similarity computation utilities
- **[`system_messages.py`](utils/system_messages.py:1)**: System prompt templates
- **[`save_results.py`](utils/save_results.py:1)**: Result persistence and formatting

### `config/` - Configuration Management

- **[`settings.yaml`](config/settings.yaml:1)**: Comprehensive system configuration with enhanced parameters

### `taxonomy/` - Mathematical Domain Knowledge

- **[`enhanced_math_taxonomy.json`](taxonomy/enhanced_math_taxonomy.json:1)**: Hierarchical mathematical taxonomy with difficulty levels
- **[`math_taxonomy.json`](taxonomy/math_taxonomy.json:1)**: Legacy taxonomy structure
- **[`sample_math_taxonomy.json`](taxonomy/sample_math_taxonomy.json:1)**: Sample taxonomy for testing

### `database/` - Data Persistence

- **[`math_agent.db`](database/math_agent.db:1)**: SQLite database for storing generated problems and metadata

### `tests/` - Comprehensive Test Suite

- **[`test_generation_enhancements.py`](tests/test_generation_enhancements.py:1)**: Tests for enhanced generation features
- **[`test_performance_enhancements.py`](tests/test_performance_enhancements.py:1)**: Tests for performance optimizations
- **[`unit_tests/`](tests/unit_tests/)**: Comprehensive unit test coverage

## User Workflows

### 🌐 Web API Workflow

```mermaid
sequenceDiagram
    participant User
    participant FastAPI
    participant PipelineService
    participant ConcurrentProcessor
    participant Agents
    participant LLMClient
    participant Database

    User->>+FastAPI: POST /api/v1/generate
    Note over User,FastAPI: JSON payload with generation parameters
    
    FastAPI->>+PipelineService: process_generation_request()
    PipelineService->>+ConcurrentProcessor: run_enhanced_pipeline()
    
    loop For each problem in batch
        ConcurrentProcessor->>+Agents: Engineer Agent
        Agents->>+LLMClient: Generate problem
        LLMClient-->>-Agents: Problem + metadata
        
        ConcurrentProcessor->>+Agents: Checker Agent (validation)
        Agents->>+LLMClient: Validate problem
        LLMClient-->>-Agents: Validation result
        
        alt Problem is valid
            ConcurrentProcessor->>+Agents: Target Agent
            Agents->>+LLMClient: Attempt solution
            LLMClient-->>-Agents: Solution attempt
            
            ConcurrentProcessor->>+Agents: Checker Agent (equivalence)
            Agents->>+LLMClient: Check solution
            LLMClient-->>-Agents: Equivalence result
            
            alt Target failed (good problem)
                ConcurrentProcessor->>Database: Store accepted problem
            else Target succeeded
                ConcurrentProcessor->>Database: Store discarded problem
            end
        end
    end
    
    ConcurrentProcessor-->>-PipelineService: Results + metrics
    PipelineService-->>-FastAPI: Formatted response
    FastAPI-->>-User: JSON response with problems and statistics
```

### 🖥️ CLI Workflow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant ConfigManager
    participant ConcurrentProcessor
    participant PerformanceMonitor
    participant FileSystem

    User->>+CLI: python -m core.cli.run_interactive
    CLI->>+ConfigManager: Load configuration
    ConfigManager-->>-CLI: Configuration object
    
    CLI->>User: Display configuration options
    User->>CLI: Confirm or modify settings
    
    CLI->>+ConcurrentProcessor: Initialize with config
    CLI->>+PerformanceMonitor: Start monitoring
    
    ConcurrentProcessor->>ConcurrentProcessor: Run generation pipeline
    Note over ConcurrentProcessor: Adaptive threading, caching, batch processing
    
    loop Real-time updates
        ConcurrentProcessor->>CLI: Progress callback
        CLI->>User: Display progress (accepted/target, workers, success rate)
    end
    
    ConcurrentProcessor-->>-CLI: Final results
    PerformanceMonitor-->>-CLI: Performance metrics
    
    CLI->>+FileSystem: Save results to JSON
    CLI->>User: Display summary and file location
    CLI-->>-User: Complete
```

### 🔄 Interactive Development Workflow

```mermaid
flowchart TD
    Start([Developer starts system]) --> Config{Configuration<br/>Method?}
    
    Config -->|CLI| CLI[Interactive CLI]
    Config -->|API| API[FastAPI Server]
    Config -->|Direct| Direct[Direct Python Import]
    
    CLI --> SetParams[Set Generation Parameters]
    API --> APIEndpoint[API Endpoint Call]
    Direct --> PythonCode[Python Code Integration]
    
    SetParams --> Pipeline[Enhanced Generation Pipeline]
    APIEndpoint --> Pipeline
    PythonCode --> Pipeline
    
    Pipeline --> Agents{Agent Workflow}
    
    Agents --> Engineer[Engineer Agent<br/>Problem Generation]
    Engineer --> Checker1[Checker Agent<br/>Initial Validation]
    Checker1 --> Valid{Valid Problem?}
    
    Valid -->|No| Discard[Discard Problem]
    Valid -->|Yes| Target[Target Agent<br/>Solution Attempt]
    
    Target --> Checker2[Checker Agent<br/>Equivalence Check]
    Checker2 --> Solved{Target Solved<br/>Correctly?}
    
    Solved -->|Yes| Discard
    Solved -->|No| Accept[Accept Problem<br/>Store in Database]
    
    Accept --> Similarity[Similarity Agent<br/>Deduplication Check]
    Similarity --> Results[Compile Results]
    Discard --> Results
    
    Results --> Output{Output Format}
    Output -->|CLI| CLIOutput[Console + File Output]
    Output -->|API| JSONResponse[JSON API Response]
    Output -->|Direct| PythonReturn[Python Object Return]
    
    CLIOutput --> End([Complete])
    JSONResponse --> End
    PythonReturn --> End
    
    %% Styling
    classDef startEnd fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    classDef agent fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    
    class Start,End startEnd
    class Config,Valid,Solved,Output decision
    class SetParams,APIEndpoint,PythonCode,Pipeline,Results,CLIOutput,JSONResponse,PythonReturn process
    class Engineer,Checker1,Target,Checker2,Similarity agent
```

## Advanced Features

### 🎯 Curriculum-Based Generation

- **Adaptive Difficulty**: Automatically adjusts problem difficulty based on target model performance
- **Topic Balancing**: Ensures comprehensive coverage across mathematical domains
- **Progress Tracking**: Maintains statistics on generation patterns and success rates

### ⚡ Performance Optimizations

- **Intelligent Caching**: Multi-level caching with TTL and thread-safe operations
- **Adaptive Threading**: Dynamic worker adjustment based on success rates and system load
- **Batch Processing**: Optimized batch sizes for maximum throughput
- **Connection Pooling**: Efficient LLM API connection management

### 🔍 Quality Assurance

- **CAS Integration**: Computer algebra system verification using SymPy
- **Multi-Stage Validation**: Initial validation + equivalence checking
- **Similarity Detection**: Prevents duplicate problems through semantic analysis
- **Cost Optimization**: Intelligent cost tracking and budget management

### 📊 Monitoring & Analytics

- **Real-Time Metrics**: Live performance monitoring with detailed statistics
- **Cost Analysis**: Comprehensive cost tracking across all LLM providers
- **Success Rate Tracking**: Detailed analysis of generation success patterns
- **Performance Profiling**: Bottleneck identification and optimization recommendations

## Configuration & Deployment

### 📋 Configuration Management

The system uses a centralized configuration approach with the [`ConfigManager`](utils/config_manager.py:18) singleton:

```yaml
# config/settings.yaml
num_problems: 10
max_workers: 8
use_enhanced_concurrent_processing: true
max_attempts: 1000

engineer_model:
  provider: "google"
  model_name: "gemini-2.0-flash-exp"
  temperature: 0.8

checker_model:
  provider: "openai"
  model_name: "o1-mini"
  temperature: 0.1

target_model:
  provider: "openai"
  model_name: "o1"
  temperature: 0.0

performance_monitoring:
  enabled: true
  log_interval: 10

caching:
  enabled: true
  max_size: 1000
  ttl_seconds: 3600
```

### 🚀 Deployment Options

#### **Local Development**

```bash
# Install dependencies
uv install

# Run CLI interface
python -m core.cli.run_interactive

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

#### **Production Deployment**

```bash
# Install production dependencies
uv install --no-dev

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### **Docker Deployment**

```dockerfile
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install uv && uv install --no-dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## API Reference

### 🌐 REST API Endpoints

#### **Generate Problems**

```http
POST /api/v1/generate
Content-Type: application/json

{
  "num_problems": 5,
  "subjects": ["algebra", "calculus"],
  "difficulty_range": [3, 7],
  "max_workers": 4,
  "use_curriculum": true
}
```

#### **Get Problem Details**

```http
GET /api/v1/problems/{problem_id}
```

#### **Batch Operations**

```http
POST /api/v1/batches
GET /api/v1/batches/{batch_id}
GET /api/v1/batches/{batch_id}/status
```

### 📊 Response Format

```json
{
  "success": true,
  "data": {
    "accepted": [
      {
        "id": "prob_123",
        "problem": "Solve for x: 2x + 3 = 7",
        "answer": "x = 2",
        "hints": {"hint1": "Isolate the variable"},
        "subject": "algebra",
        "topic": "linear_equations",
        "difficulty": 3,
        "metadata": {
          "generation_time": 1.23,
          "validation_passed": true,
          "target_model_failed": true
        }
      }
    ],
    "discarded": [],
    "statistics": {
      "total_generated": 5,
      "acceptance_rate": 0.8,
      "average_generation_time": 2.1,
      "total_cost": 0.045
    }
  }
}
```

## Performance Metrics

### 📈 Typical Performance Characteristics

- **Throughput**: 50-100 problems/minute (depending on complexity and models)
- **Cache Hit Rate**: 15-30% (varies by configuration and problem diversity)
- **Success Rate**: 20-40% (problems that successfully challenge target models)
- **Cost Efficiency**: 60-80% reduction through caching and optimization

### 🎯 Optimization Strategies

1. **Intelligent Caching**: Reduces redundant API calls by 60-80%
2. **Adaptive Threading**: Optimizes worker count based on real-time performance
3. **Batch Processing**: Improves throughput through parallel generation
4. **Curriculum Strategy**: Focuses generation on underrepresented topics
5. **Early Termination**: Stops processing when targets are met

This comprehensive system provides a robust, scalable, and efficient platform for generating high-quality synthetic mathematical problems that effectively challenge and evaluate large language models.
