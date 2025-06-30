# Project Overview

This project is a synthetic math prompt generation pipeline. Its primary purpose is to generate high-quality math problems that are difficult for large language models (LLMs) to solve correctly. The system is designed to be modular and extensible, with a clear separation of concerns between the different components.

## Directory Structure

### `app`

The `app` directory contains a FastAPI web application that exposes the core functionality of the project through a RESTful API.

- **`main.py`**: The entry point for the FastAPI application.
- **`api/routes.py`**: Defines the API endpoints, including the main `/generate` endpoint for creating new prompts.
- **`services/pipeline_service.py`**: Acts as a bridge between the API and the core application logic, translating API requests into calls to the `core` module.
- **`models/schemas.py`**: Defines the data models and schemas for API requests and responses.

### `core`

The `core` directory is the heart of the application, containing the main logic for the prompt generation pipeline.

- **`runner.py`**: The main entry point for the core logic, responsible for orchestrating the entire prompt generation process.
- **`orchestration`**: Manages the workflow of generating, validating, and evaluating prompts. It uses a parallel execution model to improve performance.
- **`engineer`**: Responsible for generating the initial math problems using an LLM.
- **`checker`**: Validates the generated prompts for correctness and logical soundness, also using an LLM.
- **`llm`**: Provides a unified interface for interacting with different LLM providers, such as OpenAI and Gemini.
- **`cli`**: A command-line interface for running the prompt generation pipeline interactively.
- **`search`**: Contains functionality for web searches to find seed content for prompt generation.

### `utils`

The `utils` directory contains a collection of helper functions and utility modules that are used throughout the project.

- **`config_manager.py`**: Centralized singleton configuration manager that provides a single source of truth for all application settings with caching capabilities.
- **`exceptions.py`**: Custom exception classes for structured error handling throughout the application.
- **`logging_config.py`**: Centralized logging configuration that replaces inconsistent print statements with proper structured logging.
- **`taxonomy.py`**: Dedicated utility for loading taxonomy files with proper error handling, eliminating code duplication.
- **`config_loader.py`**: Legacy configuration loading (superseded by `config_manager.py`).
- **`costs.py`**: Tracks the costs associated with LLM API calls.
- **`domain_taxonomy.json`**: A JSON file defining the taxonomy of subjects and topics for prompt generation.
- **`helpers.py`**: General-purpose helper functions.
- **`json_utils.py`**: Utilities for working with JSON data.
- **`save_results.py`**: Saves the generated prompts to disk.
- **`system_messages.py`**: Contains the system prompts that define the behavior of the LLMs.
- **`validation.py`**: Provides functions for data validation.

### `config`

The `config` directory contains the main configuration file for the application.

- **`settings.yaml`**: Defines the default parameters for the prompt generation pipeline, including the number of problems to generate, the models to use, and the taxonomy of subjects.

### `docs`

The `docs` directory contains project documentation.

- **`overview.md`**: This file, providing a high-level overview of the project.

---

## Core Utilities and Architectural Patterns

The system has undergone significant architectural refactoring to improve maintainability, robustness, and performance. The following core utilities implement key architectural patterns:

### Centralized Configuration Management

The [`ConfigManager`](utils/config_manager.py:18) class implements a thread-safe singleton pattern that centralizes all application configuration:

- **Single Source of Truth**: All configuration access goes through one centralized manager
- **Performance Optimization**: Caches loaded taxonomy files to avoid redundant I/O operations
- **Dot Notation Access**: Supports intuitive configuration access using dot notation (e.g., `config.get('engineer_model.provider')`)
- **Thread Safety**: Uses locks to ensure safe concurrent access in multi-threaded environments
- **Dynamic Updates**: Allows runtime configuration updates without restarting the application

This eliminates the previous pattern of scattered configuration loading throughout the codebase and provides consistent configuration access patterns.

### Standardized Error Handling

The [`exceptions.py`](utils/exceptions.py:1) module introduces a comprehensive set of custom exception classes:

- **[`ConfigError`](utils/exceptions.py:9)**: Configuration-related errors with context about the config file
- **[`TaxonomyError`](utils/exceptions.py:19)**: Taxonomy loading and validation errors
- **[`PipelineError`](utils/exceptions.py:29)**: Pipeline execution errors with stage information
- **[`ModelError`](utils/exceptions.py:39)**: LLM model interaction errors with provider/model context
- **[`ValidationError`](utils/exceptions.py:54)**: Data validation errors with field-specific information
- **[`JSONParsingError`](utils/exceptions.py:64)**: JSON parsing errors with position and context details
- **[`APIError`](utils/exceptions.py:77)**: External API interaction errors with status codes

These structured exceptions replace generic error handling and provide meaningful context for debugging and error reporting.

### Centralized Logging System

The [`logging_config.py`](utils/logging_config.py:1) module provides a standardized logging infrastructure:

- **Consistent Formatting**: Unified log format across all application components
- **Multiple Handlers**: Support for both console and file logging
- **Level Configuration**: Configurable logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Convenience Functions**: Helper functions like [`log_error()`](utils/logging_config.py:87), [`log_warning()`](utils/logging_config.py:105), [`log_info()`](utils/logging_config.py:119), and [`log_debug()`](utils/logging_config.py:133)
- **Exception Logging**: Automatic exception stack trace capture

This replaces inconsistent print statements throughout the codebase with proper structured logging.

### Centralized Taxonomy Loading

The [`taxonomy.py`](utils/taxonomy.py:1) utility provides a single, reusable function for loading taxonomy files:

- **Error Handling**: Proper exception handling with [`TaxonomyError`](utils/exceptions.py:19) for missing or invalid files
- **Path Flexibility**: Accepts both string and Path objects
- **Encoding Safety**: Ensures UTF-8 encoding for consistent file reading
- **Code Deduplication**: Eliminates redundant taxonomy loading code across modules

### gRPC Warning Suppression

To address gRPC fork support warnings that were cluttering the output, the environment variable `GRPC_ENABLE_FORK_SUPPORT=0` is now set in all application entry points:

- **[`app/main.py`](app/main.py:7)**: FastAPI application entry point
- **[`core/cli/interface.py`](core/cli/interface.py:12)**: CLI interface entry point  
- **[`core/cli/run_interactive.py`](core/cli/run_interactive.py:13)**: Interactive CLI entry point

This ensures clean output across all execution modes.

### Benefits of the Refactoring

These architectural improvements provide several key benefits:

1. **Maintainability**: Centralized utilities reduce code duplication and provide consistent patterns
2. **Robustness**: Structured error handling and logging improve debugging and error recovery
3. **Performance**: Configuration and taxonomy caching reduce redundant I/O operations
4. **Developer Experience**: Clear error messages and consistent logging improve development workflow
5. **Thread Safety**: Proper locking mechanisms ensure safe concurrent execution
6. **Scalability**: Centralized patterns make it easier to extend and modify system behavior

---

## System Architecture

```mermaid
graph TD
    subgraph User Interfaces
        CLI["Command-Line Interface (CLI)"]
        WebAPI["Web API (FastAPI)"]
    end

    subgraph Core System
        CoreOrchestration["Core Orchestration"]
        LLM_Abstraction["LLM Abstraction Layer"]
        ServicesSchemas["Services and Schemas"]
    end

    subgraph GenerationPipeline ["Generation Pipeline"]
        direction LR
        Engineer["Engineer"] --> Checker["Checker"];
        Checker --> TargetModel["Target Model"];
    end

    %% Interactions
    CLI --> CoreOrchestration;
    WebAPI --> ServicesSchemas;
    ServicesSchemas --> CoreOrchestration;
    CoreOrchestration --> GenerationPipeline;
    GenerationPipeline --> LLM_Abstraction;

    %% Style Definitions
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef subgraphStyle fill:#ececff,stroke:#999,stroke-width:2px,color:#333;
    classDef pipeline fill:#e0f2f1,stroke:#00796b,stroke-width:2px;

    class CLI,WebAPI,CoreOrchestration,LLM_Abstraction,ServicesSchemas subgraphStyle;
    class Engineer,Checker,TargetModel pipeline;
```

The application is a synthetic prompt generation system designed to produce high-quality, validated prompts for evaluating language models. It is built with a modular architecture that separates concerns between the user-facing interfaces (a web API and a command-line interface), the core orchestration logic, and the underlying language model interactions.

### Key Components

- **Entry Points:** The system offers two primary ways to initiate the prompt generation process:
  - **Web API:** A FastAPI application, defined in [`app/main.py`](app/main.py:8), provides a RESTful interface for generating prompts. It exposes a `/generate` endpoint that accepts a JSON payload specifying the generation parameters. The API routes are defined in [`app/api/routes.py`](app/api/routes.py:1), and the request/response data structures are defined using Pydantic models in [`app/models/schemas.py`](app/models/schemas.py:1).
  - **Command-Line Interface (CLI):** An interactive CLI, implemented in [`core/cli/run_interactive.py`](core/cli/run_interactive.py:1), allows users to run the generation pipeline directly from the terminal. It provides prompts for customizing the generation parameters or using the defaults from the configuration file.

- **Configuration:** The application's behavior is configured through the centralized [`ConfigManager`](utils/config_manager.py:18) singleton, which loads settings from [`config/settings.yaml`](config/settings.yaml:1). This provides a single source of truth for all configuration with caching capabilities and thread-safe access patterns.

- **Core Orchestration:** The heart of the system is the orchestration layer, managed by [`core/orchestration/generate_batch.py`](core/orchestration/generate_batch.py:1). This component is responsible for running the end-to-end prompt generation pipeline. It uses a multi-threaded approach with a `ThreadPoolExecutor` to generate and validate multiple prompts in parallel, significantly speeding up the process.

- **Generation Pipeline:** The core pipeline consists of a sequence of steps that leverage different language models to generate, validate, and test the synthetic prompts:
    1. **Engineer:** A "generator" model (e.g., `gemini-2.5-pro`) creates an initial problem, answer, and hints based on a given subject and topic.
    2. **Checker (Initial Validation):** A "checker" model (e.g., `o3-mini`) validates the generated problem for clarity, correctness, and adherence to guidelines. It can also correct the hints if necessary.
    3. **Target Model Evaluation:** The "target" model (e.g., `o1`) attempts to solve the validated problem.
    4. **Checker (Equivalence Check):** The checker model evaluates the target model's answer to determine if it is correct. The prompt is "accepted" if the target model fails to answer correctly, as this indicates the prompt is sufficiently challenging.

- **LLM Abstraction:** The system abstracts the interactions with different language models through a dispatch layer in [`core/llm/llm_dispatch.py`](core/llm/llm_dispatch.py:1). This component provides wrapper functions (`call_engineer`, `call_checker`, `call_target_model`) that route the calls to the appropriate model-specific implementation based on the configuration.

- **Services and Schemas:** The API is structured with a service layer ([`app/services/pipeline_service.py`](app/services/pipeline_service.py:1)) that acts as a bridge between the API routes and the core runner. It translates the incoming API request into the configuration format expected by the pipeline. Pydantic schemas in [`app/models/schemas.py`](app/models/schemas.py:1) ensure that the data exchanged through the API is well-structured and validated.

- **Utilities:** The application is supported by a comprehensive set of utility modules that handle configuration management ([`utils/config_manager.py`](utils/config_manager.py:1)), structured error handling ([`utils/exceptions.py`](utils/exceptions.py:1)), centralized logging ([`utils/logging_config.py`](utils/logging_config.py:1)), taxonomy loading ([`utils/taxonomy.py`](utils/taxonomy.py:1)), cost tracking ([`utils/costs.py`](utils/costs.py:1)), and result persistence ([`utils/save_results.py`](utils/save_results.py:1)).

### Primary User Workflow

The following Mermaid.js diagram illustrates the primary user workflow, from initiating a request to the final output.

```mermaid
sequenceDiagram
    participant User
    participant API
    participant CLI
    participant Orchestrator
    participant Engineer
    participant Checker
    participant TargetModel

    User->>+API: POST /generate (JSON payload)
    API->>+Orchestrator: run_pipeline(config)
    Orchestrator->>-API: Return {valid, discarded}
    API->>-User: 200 OK (JSON response)

    User->>+CLI: run_interactive.py
    CLI->>+Orchestrator: run_generation_pipeline(config)
    Orchestrator-->>Engineer: call_engineer()
    Engineer-->>Orchestrator: Return {problem, answer, hints}
    Orchestrator-->>Checker: call_checker(mode="initial")
    Checker-->>Orchestrator: Return {valid, corrected_hints}
    alt Prompt is valid
        Orchestrator-->>TargetModel: call_target_model()
        TargetModel-->>Orchestrator: Return {answer}
        Orchestrator-->>Checker: call_checker(mode="equivalence_check")
        Checker-->>Orchestrator: Return {valid}
        alt Target model failed
            Orchestrator-->>Orchestrator: Accept prompt
        else Target model succeeded
            Orchestrator-->>Orchestrator: Discard prompt
        end
    else Prompt is invalid
        Orchestrator-->>Orchestrator: Discard prompt
    end
    Orchestrator->>-CLI: Return {valid, discarded}
    CLI->>-User: Print results and save to file
```
