"""
Custom exception classes for the synthetic math prompts agent.

This module defines application-specific exceptions to provide more meaningful
error handling throughout the codebase.
"""


class ConfigError(Exception):
    """Raised when there are configuration-related errors."""

    def __init__(self, message: str, config_path: str = None):
        self.config_path = config_path
        if config_path:
            message = f"Configuration error in '{config_path}': {message}"
        super().__init__(message)


class TaxonomyError(Exception):
    """Raised when there are taxonomy-related errors."""

    def __init__(self, message: str, taxonomy_path: str = None):
        self.taxonomy_path = taxonomy_path
        if taxonomy_path:
            message = f"Taxonomy error in '{taxonomy_path}': {message}"
        super().__init__(message)


class PipelineError(Exception):
    """Raised when there are pipeline execution errors."""

    def __init__(self, message: str, stage: str = None):
        self.stage = stage
        if stage:
            message = f"Pipeline error in stage '{stage}': {message}"
        super().__init__(message)


class ModelError(Exception):
    """Raised when there are model-related errors."""

    def __init__(self, message: str, model_name: str = None, provider: str = None):
        self.model_name = model_name
        self.provider = provider
        if model_name and provider:
            message = f"Model error with '{provider}/{model_name}': {message}"
        elif model_name:
            message = f"Model error with '{model_name}': {message}"
        elif provider:
            message = f"Model error with provider '{provider}': {message}"
        super().__init__(message)


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str = None):
        self.field = field
        if field:
            message = f"Validation error for field '{field}': {message}"
        super().__init__(message)


class JSONParsingError(Exception):
    """Raised when JSON parsing fails."""

    def __init__(self, message: str, position: int = None, context: str = None):
        self.position = position
        self.context = context
        if position is not None and context:
            message = f"JSON parsing error at position {position}: {message}\nContext: {context}"
        elif position is not None:
            message = f"JSON parsing error at position {position}: {message}"
        super().__init__(message)


class APIError(Exception):
    """Raised when external API calls fail."""

    def __init__(self, message: str, status_code: int = None, api_name: str = None):
        self.status_code = status_code
        self.api_name = api_name
        if api_name and status_code:
            message = f"API error from '{api_name}' (status {status_code}): {message}"
        elif api_name:
            message = f"API error from '{api_name}': {message}"
        elif status_code:
            message = f"API error (status {status_code}): {message}"
        super().__init__(message)
