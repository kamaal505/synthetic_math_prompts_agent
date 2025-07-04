"""
LLM Response Caching System

This module provides a thread-safe caching mechanism for LLM responses to avoid
redundant API calls for identical requests. It uses a combination of in-memory
caching and optional persistent storage.
"""

import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from utils.config_manager import get_config_manager

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Thread-safe cache for LLM responses.

    Provides in-memory caching with optional persistence to disk.
    Cache keys are generated from request parameters to ensure identical
    requests return cached responses.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize the LLM cache.

        Args:
            max_size: Maximum number of entries to keep in memory
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self._lock = threading.RLock()
        self._access_order = []  # For LRU eviction

        # Load configuration
        config_manager = get_config_manager()
        self.cache_enabled = config_manager.get("llm_cache_enabled", True)
        self.persistent_cache = config_manager.get("llm_cache_persistent", False)
        self.cache_dir = Path(config_manager.get("llm_cache_dir", "cache/llm"))

        if self.persistent_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"LLM cache initialized with persistent storage at {self.cache_dir}"
            )
        else:
            logger.info("LLM cache initialized with in-memory storage only")

    def _generate_cache_key(
        self, provider: str, model_name: str, prompt: str, temperature: float, **kwargs
    ) -> str:
        """
        Generate a unique cache key for the request parameters.

        Args:
            provider: LLM provider name
            model_name: Model name
            prompt: The prompt text
            temperature: Temperature setting
            **kwargs: Additional parameters

        Returns:
            SHA256 hash of the normalized request parameters
        """
        # Create a normalized representation of the request
        cache_data = {
            "provider": provider.lower(),
            "model_name": model_name,
            "prompt": prompt.strip(),
            "temperature": temperature,
            **{
                k: v
                for k, v in sorted(kwargs.items())
                if k not in ["max_retries", "retry_delay"]
            },
        }

        # Generate hash
        cache_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(cache_str.encode("utf-8")).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry has expired."""
        return time.time() - timestamp > self.ttl_seconds

    def _evict_lru(self):
        """Evict the least recently used entry."""
        if not self._access_order:
            return

        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
            logger.debug(f"Evicted LRU cache entry: {lru_key[:16]}...")

    def _load_from_disk(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load a cache entry from persistent storage."""
        if not self.persistent_cache:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check if expired
            if self._is_expired(data.get("timestamp", 0)):
                cache_file.unlink(missing_ok=True)
                return None

            return data.get("response")
        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def _save_to_disk(self, cache_key: str, response: Dict[str, Any]):
        """Save a cache entry to persistent storage."""
        if not self.persistent_cache:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            data = {"timestamp": time.time(), "response": response}
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache to disk: {e}")

    def get(
        self, provider: str, model_name: str, prompt: str, temperature: float, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get a cached response if available.

        Args:
            provider: LLM provider name
            model_name: Model name
            prompt: The prompt text
            temperature: Temperature setting
            **kwargs: Additional parameters

        Returns:
            Cached response dict or None if not found/expired
        """
        if not self.cache_enabled:
            return None

        cache_key = self._generate_cache_key(
            provider, model_name, prompt, temperature, **kwargs
        )

        with self._lock:
            # Check in-memory cache first
            if cache_key in self._cache:
                response, timestamp = self._cache[cache_key]

                if self._is_expired(timestamp):
                    # Remove expired entry
                    del self._cache[cache_key]
                    if cache_key in self._access_order:
                        self._access_order.remove(cache_key)
                else:
                    # Update access order for LRU
                    if cache_key in self._access_order:
                        self._access_order.remove(cache_key)
                    self._access_order.append(cache_key)

                    logger.debug(f"Cache hit for {provider} {model_name}")
                    return response.copy()

            # Check persistent storage
            disk_response = self._load_from_disk(cache_key)
            if disk_response:
                # Add to in-memory cache
                self._cache[cache_key] = (disk_response, time.time())
                self._access_order.append(cache_key)

                # Evict if necessary
                if len(self._cache) > self.max_size:
                    self._evict_lru()

                logger.debug(f"Cache hit from disk for {provider} {model_name}")
                return disk_response.copy()

        return None

    def put(
        self,
        provider: str,
        model_name: str,
        prompt: str,
        temperature: float,
        response: Dict[str, Any],
        **kwargs,
    ):
        """
        Store a response in the cache.

        Args:
            provider: LLM provider name
            model_name: Model name
            prompt: The prompt text
            temperature: Temperature setting
            response: The response to cache
            **kwargs: Additional parameters
        """
        if not self.cache_enabled:
            return

        cache_key = self._generate_cache_key(
            provider, model_name, prompt, temperature, **kwargs
        )

        with self._lock:
            # Store in memory
            self._cache[cache_key] = (response.copy(), time.time())

            # Update access order
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)

            # Evict if necessary
            if len(self._cache) > self.max_size:
                self._evict_lru()

            # Save to disk
            self._save_to_disk(cache_key, response)

            logger.debug(f"Cached response for {provider} {model_name}")

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

            if self.persistent_cache and self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink(missing_ok=True)

            logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics for performance monitoring."""
        with self._lock:
            # Calculate cache efficiency metrics
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for _, (_, timestamp) in self._cache.items()
                if self._is_expired(timestamp)
            )
            
            return {
                "enabled": self.cache_enabled,
                "entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "max_size": self.max_size,
                "utilization": total_entries / self.max_size if self.max_size > 0 else 0,
                "ttl_seconds": self.ttl_seconds,
                "persistent": self.persistent_cache,
                "cache_dir": str(self.cache_dir) if self.persistent_cache else None,
                "access_order_length": len(self._access_order),
            }


# Global cache instance
_llm_cache = None
_cache_lock = threading.Lock()


def get_llm_cache() -> LLMCache:
    """
    Get the global LLMCache instance (singleton pattern).

    Returns:
        The singleton LLMCache instance
    """
    global _llm_cache
    if _llm_cache is None:
        with _cache_lock:
            if _llm_cache is None:
                _llm_cache = LLMCache()
    return _llm_cache


def clear_llm_cache():
    """Clear the global LLM cache."""
    cache = get_llm_cache()
    cache.clear()
