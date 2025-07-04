"""
Performance monitoring utilities for concurrent processing and caching.

This module provides tools to monitor and analyze the performance of the
enhanced concurrent processing and caching systems.
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    # Timing metrics
    total_time: float = 0.0
    api_call_time: float = 0.0
    cache_lookup_time: float = 0.0
    concurrent_processing_time: float = 0.0

    # Throughput metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0

    # Concurrency metrics
    max_concurrent_threads: int = 0
    average_concurrent_threads: float = 0.0
    thread_utilization: float = 0.0

    # Cache metrics
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0
    cache_size: int = 0

    # Error metrics
    retry_count: int = 0
    timeout_count: int = 0
    error_rate: float = 0.0

    # Additional metrics
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Thread-safe performance monitor for concurrent processing and caching.

    Tracks various performance metrics including timing, throughput,
    concurrency, and cache effectiveness.
    """

    def __init__(self):
        """Initialize the performance monitor."""
        self._lock = threading.RLock()
        self._start_time = time.perf_counter()

        # Timing data
        self._request_times: List[float] = []
        self._cache_lookup_times: List[float] = []
        self._api_call_times: List[float] = []

        # Request tracking
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._cached_requests = 0
        self._retry_count = 0
        self._timeout_count = 0

        # Thread tracking
        self._active_threads: Dict[int, float] = {}  # thread_id -> start_time
        self._thread_samples: List[int] = []  # samples of concurrent thread count
        self._last_sample_time = time.perf_counter()

        # Cache tracking
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info("Performance monitor initialized")

    def start_request(self, thread_id: Optional[int] = None) -> float:
        """
        Mark the start of a request.

        Args:
            thread_id: Optional thread ID (uses current thread if not provided)

        Returns:
            Start timestamp for use with end_request
        """
        if thread_id is None:
            thread_id = threading.current_thread().ident

        start_time = time.perf_counter()

        with self._lock:
            self._active_threads[thread_id] = start_time
            self._sample_thread_count()

        return start_time

    def end_request(
        self,
        start_time: float,
        success: bool = True,
        cached: bool = False,
        retries: int = 0,
        timeout: bool = False,
        thread_id: Optional[int] = None,
    ):
        """
        Mark the end of a request and record metrics.

        Args:
            start_time: Start timestamp from start_request
            success: Whether the request was successful
            cached: Whether the response was served from cache
            retries: Number of retries performed
            timeout: Whether the request timed out
            thread_id: Optional thread ID
        """
        if thread_id is None:
            thread_id = threading.current_thread().ident

        end_time = time.perf_counter()
        duration = end_time - start_time

        with self._lock:
            # Remove from active threads
            if thread_id in self._active_threads:
                del self._active_threads[thread_id]

            # Record metrics
            self._request_times.append(duration)
            self._total_requests += 1

            if success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1

            if cached:
                self._cached_requests += 1
                self._cache_hits += 1
            else:
                self._cache_misses += 1

            self._retry_count += retries

            if timeout:
                self._timeout_count += 1

            self._sample_thread_count()

    def record_cache_lookup(self, duration: float):
        """Record cache lookup timing."""
        with self._lock:
            self._cache_lookup_times.append(duration)

    def record_api_call(self, duration: float):
        """Record API call timing."""
        with self._lock:
            self._api_call_times.append(duration)

    def _sample_thread_count(self):
        """Sample the current number of active threads."""
        current_time = time.perf_counter()

        # Sample every second
        if current_time - self._last_sample_time >= 1.0:
            self._thread_samples.append(len(self._active_threads))
            self._last_sample_time = current_time

    def get_metrics(self) -> PerformanceMetrics:
        """
        Get comprehensive performance metrics.

        Returns:
            PerformanceMetrics object with current statistics
        """
        with self._lock:
            current_time = time.perf_counter()
            total_time = current_time - self._start_time

            # Calculate timing metrics
            avg_request_time = (
                sum(self._request_times) / len(self._request_times)
                if self._request_times
                else 0.0
            )

            avg_cache_lookup_time = (
                sum(self._cache_lookup_times) / len(self._cache_lookup_times)
                if self._cache_lookup_times
                else 0.0
            )

            avg_api_call_time = (
                sum(self._api_call_times) / len(self._api_call_times)
                if self._api_call_times
                else 0.0
            )

            # Calculate concurrency metrics
            max_threads = max(self._thread_samples) if self._thread_samples else 0
            avg_threads = (
                sum(self._thread_samples) / len(self._thread_samples)
                if self._thread_samples
                else 0.0
            )

            # Calculate cache metrics
            total_cache_requests = self._cache_hits + self._cache_misses
            cache_hit_rate = (
                self._cache_hits / total_cache_requests
                if total_cache_requests > 0
                else 0.0
            )
            cache_miss_rate = 1.0 - cache_hit_rate

            # Calculate error rate
            error_rate = (
                self._failed_requests / self._total_requests
                if self._total_requests > 0
                else 0.0
            )

            # Calculate throughput
            requests_per_second = (
                self._total_requests / total_time if total_time > 0 else 0.0
            )

            return PerformanceMetrics(
                total_time=total_time,
                api_call_time=avg_api_call_time,
                cache_lookup_time=avg_cache_lookup_time,
                concurrent_processing_time=avg_request_time,
                total_requests=self._total_requests,
                successful_requests=self._successful_requests,
                failed_requests=self._failed_requests,
                cached_requests=self._cached_requests,
                max_concurrent_threads=max_threads,
                average_concurrent_threads=avg_threads,
                thread_utilization=avg_threads / max_threads
                if max_threads > 0
                else 0.0,
                cache_hit_rate=cache_hit_rate,
                cache_miss_rate=cache_miss_rate,
                cache_size=total_cache_requests,
                retry_count=self._retry_count,
                timeout_count=self._timeout_count,
                error_rate=error_rate,
                metadata={
                    "requests_per_second": requests_per_second,
                    "active_threads": len(self._active_threads),
                    "total_samples": len(self._thread_samples),
                },
            )

    def log_summary(self):
        """Log a summary of performance metrics."""
        metrics = self.get_metrics()

        logger.info("=== Performance Summary ===")
        logger.info(f"Total Time: {metrics.total_time:.2f}s")
        logger.info(f"Total Requests: {metrics.total_requests}")
        logger.info(f"Success Rate: {(1 - metrics.error_rate):.2%}")
        logger.info(f"Cache Hit Rate: {metrics.cache_hit_rate:.2%}")
        logger.info(f"Avg Concurrent Threads: {metrics.average_concurrent_threads:.1f}")
        logger.info(f"Max Concurrent Threads: {metrics.max_concurrent_threads}")
        logger.info(
            f"Requests/Second: {metrics.metadata.get('requests_per_second', 0):.2f}"
        )
        logger.info(f"Avg Request Time: {metrics.concurrent_processing_time:.3f}s")
        logger.info(f"Avg API Call Time: {metrics.api_call_time:.3f}s")
        logger.info(f"Avg Cache Lookup Time: {metrics.cache_lookup_time:.3f}s")

        if metrics.retry_count > 0:
            logger.info(f"Total Retries: {metrics.retry_count}")
        if metrics.timeout_count > 0:
            logger.info(f"Timeouts: {metrics.timeout_count}")

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._start_time = time.perf_counter()
            self._request_times.clear()
            self._cache_lookup_times.clear()
            self._api_call_times.clear()
            self._total_requests = 0
            self._successful_requests = 0
            self._failed_requests = 0
            self._cached_requests = 0
            self._retry_count = 0
            self._timeout_count = 0
            self._active_threads.clear()
            self._thread_samples.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._last_sample_time = time.perf_counter()

        logger.info("Performance monitor reset")


# Global performance monitor instance
_performance_monitor = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get the global PerformanceMonitor instance (singleton pattern).

    Returns:
        The singleton PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def reset_performance_monitor():
    """Reset the global performance monitor."""
    monitor = get_performance_monitor()
    monitor.reset()
