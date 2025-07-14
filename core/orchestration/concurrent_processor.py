"""
Enhanced Concurrent Processing for Batch Generation

This module provides adaptive ThreadPool management and enhanced concurrent
processing capabilities for the problem generation pipeline.
"""

import concurrent.futures
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from utils.config_manager import get_config_manager

logger = logging.getLogger(__name__)


class AdaptiveThreadPool:
    """
    Adaptive ThreadPool that dynamically adjusts worker count based on
    success/discard rates and system performance.
    """

    def __init__(
        self,
        initial_workers: int = 5,
        min_workers: int = 2,
        max_workers: int = 20,
        adaptation_interval: int = 10,
        target_success_rate: float = 0.05,
    ):
        """
        Initialize the adaptive thread pool.

        Args:
            initial_workers: Initial number of worker threads
            min_workers: Minimum number of workers
            max_workers: Maximum number of workers
            adaptation_interval: Number of completed tasks between adaptations
            target_success_rate: Target success rate for optimization
        """
        self.initial_workers = initial_workers
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.adaptation_interval = adaptation_interval
        self.target_success_rate = target_success_rate

        self.current_workers = initial_workers
        self.completed_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.last_adaptation_time = time.time()

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        logger.info(
            f"Initialized adaptive thread pool: {initial_workers} workers "
            f"(range: {min_workers}-{max_workers})"
        )

    def _calculate_success_rate(self) -> float:
        """Calculate the current success rate."""
        if self.completed_tasks == 0:
            return 0.0
        return self.successful_tasks / self.completed_tasks

    def _should_adapt(self) -> bool:
        """Check if adaptation should occur."""
        return (
            self.completed_tasks > 0
            and self.completed_tasks % self.adaptation_interval == 0
            and time.time() - self.last_adaptation_time
            > 30  # At least 30 seconds between adaptations
        )

    def _adapt_worker_count(self) -> int:
        """
        Adapt the worker count based on performance metrics.

        Returns:
            New worker count
        """
        success_rate = self._calculate_success_rate()

        # If success rate is too low, reduce workers to avoid wasting resources
        if success_rate < self.target_success_rate * 0.5:
            new_workers = max(self.min_workers, int(self.current_workers * 0.8))
            logger.info(
                f"Low success rate ({success_rate:.2%}), reducing workers: "
                f"{self.current_workers} → {new_workers}"
            )

        # If success rate is good, consider increasing workers
        elif success_rate > self.target_success_rate * 1.2:
            new_workers = min(self.max_workers, int(self.current_workers * 1.2))
            logger.info(
                f"Good success rate ({success_rate:.2%}), increasing workers: "
                f"{self.current_workers} → {new_workers}"
            )

        # Success rate is acceptable, maintain current level
        else:
            new_workers = self.current_workers
            logger.debug(
                f"Success rate acceptable ({success_rate:.2%}), maintaining {new_workers} workers"
            )

        self.last_adaptation_time = time.time()
        return new_workers

    def record_task_result(self, success: bool):
        """
        Record the result of a completed task.

        Args:
            success: Whether the task was successful
        """
        with self._lock:
            self.completed_tasks += 1
            if success:
                self.successful_tasks += 1
            else:
                self.failed_tasks += 1

    def should_stop(self) -> bool:
        """Check if processing should stop."""
        return self._stop_event.is_set()

    def signal_stop(self):
        """Signal all workers to stop gracefully."""
        self._stop_event.set()
        logger.info("Stop signal sent to all workers")

    def get_current_workers(self) -> int:
        """Get the current number of workers."""
        with self._lock:
            if self._should_adapt():
                self.current_workers = self._adapt_worker_count()
            return self.current_workers

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._lock:
            success_rate = self._calculate_success_rate()
            return {
                "current_workers": self.current_workers,
                "completed_tasks": self.completed_tasks,
                "successful_tasks": self.successful_tasks,
                "failed_tasks": self.failed_tasks,
                "success_rate": success_rate,
                "target_success_rate": self.target_success_rate,
            }


class ConcurrentProcessor:
    """
    Enhanced concurrent processor for batch generation with adaptive threading
    and improved error handling.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the concurrent processor.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ConcurrentProcessor")

        # Initialize adaptive thread pool
        initial_workers = config.get("max_workers", 10)
        min_workers = max(2, initial_workers // 4)
        max_workers = min(50, initial_workers * 3)

        self.thread_pool = AdaptiveThreadPool(
            initial_workers=initial_workers,
            min_workers=min_workers,
            max_workers=max_workers,
            adaptation_interval=config.get("adaptation_interval", 10),
            target_success_rate=config.get("target_success_rate", 0.3),
        )

        # Results storage
        self.accepted = []
        self.discarded = []
        self.errors = []
        self._results_lock = threading.Lock()

        # Progress tracking
        self.target_count = config.get("num_problems", 10)
        self.approved_count = 0
        self.attempt_counter = 0

        self.logger.info(
            f"Initialized concurrent processor for {self.target_count} problems"
        )

    def _process_single_task(
        self, task_func: Callable, task_args: Tuple, attempt_num: int
    ) -> Tuple[str, Dict[str, Any], int]:
        """
        Process a single task with error handling.

        Args:
            task_func: Function to execute
            task_args: Arguments for the function
            attempt_num: Attempt number for tracking

        Returns:
            Tuple of (result_type, data, attempt_num)
        """
        try:
            if self.thread_pool.should_stop():
                return "stopped", {"reason": "Stop signal received"}, attempt_num

            result_type, data = task_func(*task_args)

            # Record success/failure for adaptation
            success = result_type == "accepted"
            self.thread_pool.record_task_result(success)

            return result_type, data, attempt_num

        except Exception as e:
            self.logger.error(
                f"Task execution error in attempt {attempt_num}: {str(e)}"
            )
            self.thread_pool.record_task_result(False)
            return (
                "error",
                {"error": str(e), "attempt_number": attempt_num},
                attempt_num,
            )

    def _update_results(self, result_type: str, data: Dict[str, Any], attempt_num: int):
        """
        Update results in a thread-safe manner.

        Args:
            result_type: Type of result ("accepted", "discarded", "error", "stopped")
            data: Result data
            attempt_num: Attempt number
        """
        with self._results_lock:
            if result_type == "accepted":
                self.accepted.append(data)
                self.approved_count += 1
                self.logger.info(
                    f"✅ Attempt {attempt_num} — Approved: {self.approved_count}/{self.target_count}"
                )
            elif result_type == "discarded":
                self.discarded.append(data)
                self.logger.debug(f"❌ Attempt {attempt_num} — Discarded")
            elif result_type == "error":
                self.errors.append(data)
                self.logger.warning(f"🚨 Attempt {attempt_num} — Error")
            elif result_type == "stopped":
                self.logger.info(f"⏹️ Attempt {attempt_num} — Stopped")

    def process_batch(
        self,
        task_func: Callable,
        task_args_generator: Callable[[], Tuple],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process tasks concurrently with adaptive threading.

        Args:
            task_func: Function to execute for each task
            task_args_generator: Function that generates arguments for each task
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (accepted_results, discarded_results, error_results)
        """
        self.logger.info(
            f"Starting concurrent batch processing with adaptive threading"
        )

        start_time = time.time()
        max_attempts = self.config.get("max_attempts", self.target_count * 100)  # Safety limit

        # Use a context manager for proper cleanup
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.thread_pool.get_current_workers()
        ) as executor:
            futures = []

            while (
                self.approved_count < self.target_count
                and not self.thread_pool.should_stop()
                and self.attempt_counter < max_attempts
            ):
                # Adapt worker count if needed
                current_workers = self.thread_pool.get_current_workers()

                # Submit new tasks up to the current worker limit
                while (
                    len(futures) < current_workers * 2  # Keep pipeline full
                    and self.approved_count < self.target_count
                    and not self.thread_pool.should_stop()
                ):
                    self.attempt_counter += 1
                    task_args = task_args_generator()

                    future = executor.submit(
                        self._process_single_task,
                        task_func,
                        task_args,
                        self.attempt_counter,
                    )
                    futures.append(future)

                if not futures:
                    break

                # Process completed futures
                completed_futures = []
                for future in futures:
                    if future.done():
                        completed_futures.append(future)

                # If no futures are done, wait for at least one
                if not completed_futures and futures:
                    try:
                        done_futures = concurrent.futures.as_completed(futures, timeout=1.0)
                        first_done = next(done_futures)
                        completed_futures.append(first_done)
                    except (StopIteration, concurrent.futures.TimeoutError):
                        continue  # Timeout occurred, continue loop

                # Process completed futures
                for future in completed_futures:
                    try:
                        result_type, data, attempt_num = future.result()
                        self._update_results(result_type, data, attempt_num)

                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(
                                {
                                    "approved": self.approved_count,
                                    "target": self.target_count,
                                    "attempt": attempt_num,
                                    "stats": self.thread_pool.get_stats(),
                                }
                            )

                    except Exception as e:
                        self.logger.error(f"Future result error: {str(e)}")
                        self.errors.append({"error": str(e), "future_error": True})

                    futures.remove(future)

                # Check if we should stop early
                if self.approved_count >= self.target_count:
                    self.thread_pool.signal_stop()
                    break

        # Check if we hit the max attempts limit
        if self.attempt_counter >= max_attempts:
            self.logger.warning(
                f"Reached maximum attempts limit ({max_attempts}). "
                f"Stopping with {self.approved_count}/{self.target_count} approved."
            )

        # Log final statistics
        elapsed_time = time.time() - start_time
        stats = self.thread_pool.get_stats()

        self.logger.info(
            f"Batch processing completed in {elapsed_time:.1f}s: "
            f"{self.approved_count} accepted, {len(self.discarded)} discarded, "
            f"{len(self.errors)} errors (Success rate: {stats['success_rate']:.2%})"
        )

        return self.accepted, self.discarded, self.errors


def create_concurrent_processor(config: Dict[str, Any]) -> ConcurrentProcessor:
    """
    Factory function to create a ConcurrentProcessor instance.

    Args:
        config: Configuration dictionary

    Returns:
        Configured ConcurrentProcessor instance
    """
    return ConcurrentProcessor(config)
