"""
Curriculum-based generation strategy for controlling difficulty and topic selection.

This module provides intelligent topic and difficulty selection based on the
enhanced taxonomy structure as part of Phase 3 improvements.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from utils.taxonomy import (
    VALID_DIFFICULTY_LEVELS,
    get_random_topic_with_level,
    get_topic_info,
)

logger = logging.getLogger(__name__)


class CurriculumStrategy:
    """
    Curriculum-based strategy for intelligent problem generation.

    This class manages the selection of topics and difficulty levels
    to create a balanced and progressive learning experience.
    """

    def __init__(self, taxonomy_data: Dict[str, Any]):
        """
        Initialize the curriculum strategy.

        Args:
            taxonomy_data: The loaded taxonomy data
        """
        self.taxonomy_data = taxonomy_data
        self.generation_history = []
        self.difficulty_weights = {
            "High School": 0.3,
            "Undergraduate": 0.4,
            "Graduate": 0.25,
            "Research": 0.05,
        }

        # Track topic coverage for balanced generation
        self.topic_coverage = {}
        self._initialize_topic_coverage()

    def _initialize_topic_coverage(self):
        """Initialize topic coverage tracking."""
        for subject, topics in self.taxonomy_data.items():
            if isinstance(topics, dict):  # New nested format
                for topic in topics.keys():
                    key = f"{subject}::{topic}"
                    self.topic_coverage[key] = 0
            elif isinstance(topics, list):  # Legacy format
                for topic in topics:
                    key = f"{subject}::{topic}"
                    self.topic_coverage[key] = 0

    def select_topic_and_difficulty(
        self,
        preferred_difficulty: Optional[str] = None,
        preferred_subject: Optional[str] = None,
        balance_coverage: bool = True,
    ) -> Tuple[str, str, Optional[str], Optional[str]]:
        """
        Select a topic and difficulty level using curriculum strategy.

        Args:
            preferred_difficulty: Optional preferred difficulty level
            preferred_subject: Optional preferred subject
            balance_coverage: Whether to balance topic coverage

        Returns:
            Tuple of (subject, topic, difficulty_level, topic_description)
        """
        # Determine difficulty level
        if preferred_difficulty and preferred_difficulty in VALID_DIFFICULTY_LEVELS:
            difficulty_level = preferred_difficulty
        else:
            difficulty_level = self._select_difficulty_level()

        # Select topic based on strategy
        if balance_coverage and not preferred_subject:
            subject, topic, topic_info = self._select_balanced_topic(difficulty_level)
        elif preferred_subject:
            subject, topic, topic_info = self._select_topic_from_subject(
                preferred_subject, difficulty_level
            )
        else:
            subject, topic, topic_info = self._select_random_topic(difficulty_level)

        # Update coverage tracking
        coverage_key = f"{subject}::{topic}"
        if coverage_key in self.topic_coverage:
            self.topic_coverage[coverage_key] += 1

        # Record in generation history
        self.generation_history.append(
            {
                "subject": subject,
                "topic": topic,
                "difficulty_level": difficulty_level,
                "topic_description": topic_info.get("description"),
            }
        )

        topic_description = topic_info.get("description")

        logger.info(
            f"Selected topic: {subject} - {topic} "
            f"(level: {difficulty_level}, coverage: {self.topic_coverage.get(coverage_key, 0)})"
        )

        return subject, topic, difficulty_level, topic_description

    def _select_difficulty_level(self) -> str:
        """Select difficulty level based on weighted distribution."""
        # Adjust weights based on generation history
        adjusted_weights = self._adjust_difficulty_weights()

        # Weighted random selection
        levels = list(adjusted_weights.keys())
        weights = list(adjusted_weights.values())

        return random.choices(levels, weights=weights)[0]

    def _adjust_difficulty_weights(self) -> Dict[str, float]:
        """Adjust difficulty weights based on recent generation history."""
        if len(self.generation_history) < 10:
            return self.difficulty_weights.copy()

        # Count recent difficulty levels
        recent_history = self.generation_history[-10:]
        recent_counts = {}

        for entry in recent_history:
            level = entry["difficulty_level"]
            recent_counts[level] = recent_counts.get(level, 0) + 1

        # Adjust weights to balance distribution
        adjusted_weights = {}
        total_recent = len(recent_history)

        for level, base_weight in self.difficulty_weights.items():
            recent_proportion = recent_counts.get(level, 0) / total_recent
            target_proportion = base_weight

            # Reduce weight if over-represented, increase if under-represented
            adjustment = 1.0 + (target_proportion - recent_proportion)
            adjusted_weights[level] = max(0.05, base_weight * adjustment)

        # Normalize weights
        total_weight = sum(adjusted_weights.values())
        for level in adjusted_weights:
            adjusted_weights[level] /= total_weight

        return adjusted_weights

    def _select_balanced_topic(
        self, difficulty_level: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Select topic with balanced coverage consideration."""
        # Find topics with lowest coverage
        min_coverage = min(self.topic_coverage.values()) if self.topic_coverage else 0
        under_covered_topics = [
            key
            for key, count in self.topic_coverage.items()
            if count <= min_coverage + 1
        ]

        # Filter by difficulty level if specified
        if difficulty_level:
            filtered_topics = []
            for topic_key in under_covered_topics:
                subject, topic = topic_key.split("::", 1)
                topic_info = get_topic_info(self.taxonomy_data, subject, topic)
                if topic_info.get("level") == difficulty_level:
                    filtered_topics.append(topic_key)

            if filtered_topics:
                under_covered_topics = filtered_topics

        if under_covered_topics:
            # Select from under-covered topics
            selected_key = random.choice(under_covered_topics)
            subject, topic = selected_key.split("::", 1)
            topic_info = get_topic_info(self.taxonomy_data, subject, topic)
            return subject, topic, topic_info
        else:
            # Fall back to random selection
            return self._select_random_topic(difficulty_level)

    def _select_topic_from_subject(
        self, subject: str, difficulty_level: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Select topic from a specific subject."""
        if subject not in self.taxonomy_data:
            logger.warning(f"Subject '{subject}' not found in taxonomy")
            return self._select_random_topic(difficulty_level)

        subject_topics = self.taxonomy_data[subject]

        if isinstance(subject_topics, dict):  # New nested format
            # Filter by difficulty if specified
            if difficulty_level:
                matching_topics = [
                    topic
                    for topic, info in subject_topics.items()
                    if info.get("level") == difficulty_level
                ]
            else:
                matching_topics = list(subject_topics.keys())

            if not matching_topics:
                logger.warning(
                    f"No topics found for {subject} at {difficulty_level} level"
                )
                return self._select_random_topic(difficulty_level)

            topic = random.choice(matching_topics)
            topic_info = subject_topics[topic]

        else:  # Legacy format
            topic = random.choice(subject_topics)
            topic_info = {}

        return subject, topic, topic_info

    def _select_random_topic(
        self, difficulty_level: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Select a random topic, optionally filtered by difficulty."""
        try:
            return get_random_topic_with_level(self.taxonomy_data, difficulty_level)
        except Exception as e:
            logger.error(f"Failed to select random topic: {str(e)}")
            # Fall back to first available topic
            for subject, topics in self.taxonomy_data.items():
                if isinstance(topics, dict):
                    topic = next(iter(topics.keys()))
                    topic_info = topics[topic]
                elif isinstance(topics, list):
                    topic = topics[0]
                    topic_info = {}
                else:
                    continue
                return subject, topic, topic_info

            raise ValueError("No topics available in taxonomy")

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about the generation history."""
        if not self.generation_history:
            return {"total_generated": 0}

        # Count by difficulty level
        difficulty_counts = {}
        for entry in self.generation_history:
            level = entry["difficulty_level"]
            difficulty_counts[level] = difficulty_counts.get(level, 0) + 1

        # Count by subject
        subject_counts = {}
        for entry in self.generation_history:
            subject = entry["subject"]
            subject_counts[subject] = subject_counts.get(subject, 0) + 1

        # Coverage statistics
        total_topics = len(self.topic_coverage)
        covered_topics = sum(1 for count in self.topic_coverage.values() if count > 0)
        coverage_percentage = (
            (covered_topics / total_topics * 100) if total_topics > 0 else 0
        )

        return {
            "total_generated": len(self.generation_history),
            "difficulty_distribution": difficulty_counts,
            "subject_distribution": subject_counts,
            "topic_coverage": {
                "total_topics": total_topics,
                "covered_topics": covered_topics,
                "coverage_percentage": coverage_percentage,
            },
            "recent_topics": [
                f"{entry['subject']} - {entry['topic']}"
                for entry in self.generation_history[-5:]
            ],
        }

    def reset_coverage(self):
        """Reset topic coverage tracking."""
        for key in self.topic_coverage:
            self.topic_coverage[key] = 0
        logger.info("Topic coverage tracking reset")

    def set_difficulty_weights(self, weights: Dict[str, float]):
        """
        Set custom difficulty level weights.

        Args:
            weights: Dictionary mapping difficulty levels to weights
        """
        # Validate and normalize weights
        valid_weights = {}
        for level, weight in weights.items():
            if level in VALID_DIFFICULTY_LEVELS and weight >= 0:
                valid_weights[level] = weight

        if valid_weights:
            total_weight = sum(valid_weights.values())
            if total_weight > 0:
                self.difficulty_weights = {
                    level: weight / total_weight
                    for level, weight in valid_weights.items()
                }
                logger.info(f"Updated difficulty weights: {self.difficulty_weights}")
            else:
                logger.warning("All weights are zero, keeping current weights")
        else:
            logger.warning("No valid weights provided, keeping current weights")


def create_curriculum_strategy(taxonomy_data: Dict[str, Any]) -> CurriculumStrategy:
    """
    Create a curriculum strategy instance.

    Args:
        taxonomy_data: The loaded taxonomy data

    Returns:
        CurriculumStrategy instance
    """
    return CurriculumStrategy(taxonomy_data)
