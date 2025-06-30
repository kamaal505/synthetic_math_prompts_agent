"""
Centralized taxonomy file loading utilities.

This module provides a single, reusable function for loading taxonomy JSON files
with proper error handling, eliminating code duplication across the codebase.
"""

import json
from pathlib import Path
from typing import Any, Dict

from utils.exceptions import TaxonomyError


def load_taxonomy_file(taxonomy_path: str | Path) -> Dict[str, Any]:
    """
    Load a taxonomy JSON file with proper error handling.

    Args:
        taxonomy_path: Path to the taxonomy JSON file (string or Path object)

    Returns:
        Dict containing the loaded taxonomy data

    Raises:
        FileNotFoundError: If the taxonomy file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    taxonomy_file_path = Path(taxonomy_path)

    if not taxonomy_file_path.exists():
        raise TaxonomyError(
            f"Taxonomy file not found: {taxonomy_file_path}",
            taxonomy_path=str(taxonomy_file_path),
        )

    with open(taxonomy_file_path, "r", encoding="utf-8") as f:
        return json.load(f)
