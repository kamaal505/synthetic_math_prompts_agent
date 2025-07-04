"""
Centralized taxonomy file loading utilities.

This module provides functions for loading and validating taxonomy JSON files
with proper error handling and structure validation for Phase 3 enhancements.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

from utils.exceptions import TaxonomyError

logger = logging.getLogger(__name__)

# Valid difficulty levels for taxonomy validation
VALID_DIFFICULTY_LEVELS = {
    "Elementary School",
    "Middle School",
    "High School",
    "Undergraduate",
    "Graduate",
    "Research"
}


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
        taxonomy_data = json.load(f)
    
    # Validate taxonomy structure if it follows the new nested format
    if _is_nested_taxonomy(taxonomy_data):
        validate_nested_taxonomy_structure(taxonomy_data)
        logger.info(f"Loaded and validated nested taxonomy with {len(taxonomy_data)} subjects")
    else:
        logger.info(f"Loaded legacy taxonomy with {len(taxonomy_data)} subjects")
    
    return taxonomy_data


def _is_nested_taxonomy(taxonomy_data: Dict[str, Any]) -> bool:
    """
    Check if taxonomy follows the new nested structure.
    
    Args:
        taxonomy_data: The loaded taxonomy data
        
    Returns:
        True if it's a nested taxonomy, False if it's legacy format
    """
    if not taxonomy_data:
        return False
        
    # Check first subject to determine format
    first_subject = next(iter(taxonomy_data.values()))
    
    # Legacy format: subject -> [topic1, topic2, ...]
    if isinstance(first_subject, list):
        return False
        
    # New format: subject -> {topic: {level, description}}
    if isinstance(first_subject, dict):
        first_topic = next(iter(first_subject.values()), {})
        return isinstance(first_topic, dict) and ("level" in first_topic or "description" in first_topic)
    
    return False


def validate_nested_taxonomy_structure(taxonomy_data: Dict[str, Any]) -> None:
    """
    Validate that the taxonomy follows the expected nested structure.
    
    Expected format:
    {
        "subject": {
            "topic": {
                "level": "High School",
                "description": "Topic description"
            }
        }
    }
    
    Args:
        taxonomy_data: The taxonomy data to validate
        
    Raises:
        TaxonomyError: If the structure is invalid
    """
    if not isinstance(taxonomy_data, dict):
        raise TaxonomyError("Taxonomy must be a dictionary")
    
    invalid_levels = set()
    
    for subject, topics in taxonomy_data.items():
        if not isinstance(topics, dict):
            raise TaxonomyError(f"Subject '{subject}' must contain a dictionary of topics")
            
        for topic, topic_data in topics.items():
            if not isinstance(topic_data, dict):
                raise TaxonomyError(f"Topic '{topic}' in subject '{subject}' must be a dictionary")
            
            # Check for required fields
            level = topic_data.get("level")
            if level and level not in VALID_DIFFICULTY_LEVELS:
                invalid_levels.add(level)
    
    if invalid_levels:
        raise TaxonomyError(
            f"Invalid difficulty levels found: {invalid_levels}. "
            f"Valid levels are: {VALID_DIFFICULTY_LEVELS}"
        )


def get_topic_info(taxonomy_data: Dict[str, Any], subject: str, topic: str) -> Dict[str, Any]:
    """
    Get information about a specific topic from the taxonomy.
    
    Args:
        taxonomy_data: The loaded taxonomy data
        subject: The subject name
        topic: The topic name
        
    Returns:
        Dictionary containing topic information (level, description)
        Returns empty dict if not found or if using legacy format
    """
    if not _is_nested_taxonomy(taxonomy_data):
        return {}
        
    subject_data = taxonomy_data.get(subject, {})
    if not isinstance(subject_data, dict):
        return {}
        
    return subject_data.get(topic, {})


def get_random_topic_with_level(taxonomy_data: Dict[str, Any], difficulty_level: str = None) -> tuple[str, str, Dict[str, Any]]:
    """
    Get a random topic, optionally filtered by difficulty level.
    
    Args:
        taxonomy_data: The loaded taxonomy data
        difficulty_level: Optional difficulty level to filter by
        
    Returns:
        Tuple of (subject, topic, topic_info)
        
    Raises:
        TaxonomyError: If no topics match the criteria
    """
    import random
    
    if not _is_nested_taxonomy(taxonomy_data):
        # Legacy format - pick random subject and topic
        subjects = list(taxonomy_data.keys())
        if not subjects:
            raise TaxonomyError("No subjects found in taxonomy")
            
        subject = random.choice(subjects)
        topics = taxonomy_data[subject]
        if not topics:
            raise TaxonomyError(f"No topics found for subject '{subject}'")
            
        topic = random.choice(topics)
        return subject, topic, {}
    
    # New nested format
    matching_topics = []
    
    for subject, topics in taxonomy_data.items():
        for topic, topic_info in topics.items():
            if difficulty_level is None or topic_info.get("level") == difficulty_level:
                matching_topics.append((subject, topic, topic_info))
    
    if not matching_topics:
        level_msg = f" at '{difficulty_level}' level" if difficulty_level else ""
        raise TaxonomyError(f"No topics found{level_msg}")
    
    return random.choice(matching_topics)
