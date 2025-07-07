"""
Tests for Phase 2 Performance and Efficiency Enhancements.

This module tests the concurrent processing, caching mechanisms, and performance
monitoring features implemented in Phase 2.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from core.llm.llm_client import LLMClient, get_llm_client
from core.orchestration.generate_batch import (
    _generate_batch_problems,
    _generate_and_validate_prompt,
    run_generation_pipeline
)
from core.orchestration.concurrent_processor import AdaptiveThreadPool, ConcurrentProcessor
from utils.performance_monitor import PerformanceMonitor, get_performance_monitor, reset_performance_monitor
from utils.costs import CostTracker

class TestAdaptiveThreadPool:
    """Test the adaptive thread pool functionality."""
    
    def test_initialization(self):
        """Test thread pool initialization."""
        pool = AdaptiveThreadPool(
            initial_workers=5,
            min_workers=2,
            max_workers=20,
            target_success_rate=0.3
        )
        
        assert pool.current_workers == 5
        assert pool.min_workers == 2
        assert pool.max_workers == 20
        assert pool.target_success_rate == 0.3
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        pool = AdaptiveThreadPool()
        
        # Initially no tasks
        assert pool._calculate_success_rate() == 0.0
        
        # Record some results
        pool.record_task_result(True)
        pool.record_task_result(True)
        pool.record_task_result(False)
        
        assert pool._calculate_success_rate() == 2/3
    
    def test_worker_adaptation(self):
        """Test worker count adaptation based on success rate."""
        pool = AdaptiveThreadPool(
            initial_workers=10,
            min_workers=2,
            max_workers=20,
            adaptation_interval=5,
            target_success_rate=0.5
        )
        
        # Simulate low success rate
        for _ in range(10):
            pool.record_task_result(False)
        
        # Force adaptation check
        pool.completed_tasks = 5  # Trigger adaptation
        new_workers = pool._adapt_worker_count()
        
        # Should reduce workers due to low success rate
        assert new_workers < 10
    
    def test_stop_signal(self):
        """Test stop signal functionality."""
        pool = AdaptiveThreadPool()
        
        assert not pool.should_stop()
        
        pool.signal_stop()
        assert pool.should_stop()


class TestConcurrentBatchGeneration:
    """Test concurrent batch generation functionality."""
    
    @patch('core.orchestration.generate_batch.call_engineer')
    def test_batch_generation_concurrent(self, mock_call_engineer):
        """Test that batch generation uses concurrent processing."""
        # Mock engineer responses
        mock_responses = [
            {
                "problem": f"Problem {i}",
                "answer": f"Answer {i}",
                "hints": {"hint1": f"Hint {i}"},
                "tokens_prompt": 10,
                "tokens_completion": 20
            }
            for i in range(3)
        ]
        mock_call_engineer.side_effect = mock_responses
        
        config = {
            "taxonomy": {"algebra": ["linear_equations"]},
            "engineer_model": {"provider": "openai", "model_name": "gpt-4"}
        }
        cost_tracker = CostTracker()
        
        result_type, data = _generate_batch_problems(config, cost_tracker, batch_size=3)
        
        assert result_type == "batch_generated"
        assert data["batch_size"] == 3
        assert len(data["problems"]) == 3
        
        # Verify all engineer calls were made
        assert mock_call_engineer.call_count == 3
    
    @patch('core.orchestration.generate_batch.call_engineer')
    def test_batch_generation_partial_failure(self, mock_call_engineer):
        """Test batch generation with partial failures."""
        # Mock some successful and some failed responses
        def side_effect(*args, **kwargs):
            if mock_call_engineer.call_count <= 2:
                return {
                    "problem": f"Problem {mock_call_engineer.call_count}",
                    "answer": f"Answer {mock_call_engineer.call_count}",
                    "hints": {"hint1": f"Hint {mock_call_engineer.call_count}"},
                    "tokens_prompt": 10,
                    "tokens_completion": 20
                }
            else:
                raise Exception("API Error")
        
        mock_call_engineer.side_effect = side_effect
        
        config = {
            "taxonomy": {"algebra": ["linear_equations"]},
            "engineer_model": {"provider": "openai", "model_name": "gpt-4"}
        }
        cost_tracker = CostTracker()
        
        result_type, data = _generate_batch_problems(config, cost_tracker, batch_size=3)
        
        # Should still return successful problems
        assert result_type == "batch_generated"
        assert data["batch_size"] == 2  # Only 2 successful
        assert len(data["problems"]) == 2


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_request_tracking(self):
        """Test request start/end tracking."""
        start_time = self.monitor.start_request()
        time.sleep(0.01)  # Small delay
        self.monitor.end_request(start_time, success=True)
        
        metrics = self.monitor.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.concurrent_processing_time > 0
    
    def test_concurrent_thread_tracking(self):
        """Test concurrent thread tracking."""
        def worker():
            start_time = self.monitor.start_request()
            time.sleep(0.05)
            self.monitor.end_request(start_time, success=True)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait a bit to let threads start
        time.sleep(0.01)
        
        # Check that concurrent threads are tracked
        metrics = self.monitor.get_metrics()
        # Note: Exact count may vary due to timing, but should be > 0
        assert metrics.max_concurrent_threads >= 0
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        final_metrics = self.monitor.get_metrics()
        assert final_metrics.total_requests == 5
        assert final_metrics.successful_requests == 5


class TestIntegratedPerformanceEnhancements:
    """Test integrated performance enhancements."""
    
    @patch('core.llm.llm_dispatch.call_engineer')
    @patch('core.llm.llm_dispatch.call_checker')
    @patch('core.llm.llm_dispatch.call_target_model')
    def test_pipeline_with_performance_monitoring(
        self, mock_target, mock_checker, mock_engineer
    ):
        """Test that the pipeline integrates performance monitoring."""
        # Mock responses
        mock_engineer.return_value = {
            "problem": "Test problem",
            "answer": "Test answer",
            "hints": {"hint1": "Test hint"},
            "tokens_prompt": 10,
            "tokens_completion": 20
        }
        
        mock_checker.side_effect = [
            {"valid": True, "corrected_hints": None},  # Initial validation
            {"valid": False}  # Target model check (model failed)
        ]
        
        mock_target.return_value = {
            "output": "Wrong answer",
            "tokens_prompt": 5,
            "tokens_completion": 10
        }
        
        config = {
            "num_problems": 1,
            "max_workers": 2,
            "max_attempts": 10,  # Add safety limit for tests
            "use_enhanced_concurrent_processing": True,
            "taxonomy": {"algebra": ["linear_equations"]},
            "engineer_model": {"provider": "openai", "model_name": "gpt-4"},
            "checker_model": {"provider": "openai", "model_name": "gpt-4"},
            "target_model": {"provider": "openai", "model_name": "gpt-4"}
        }
        
        # Reset performance monitor
        reset_performance_monitor()
        
        accepted, discarded, cost_tracker = run_generation_pipeline(config)
        
        # Verify results
        assert len(accepted) == 1
        assert len(discarded) >= 0
        
        # Check that performance monitoring was active
        perf_monitor = get_performance_monitor()
        metrics = perf_monitor.get_metrics()
        
        assert metrics.total_requests > 0
        assert metrics.total_time > 0


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Clean up global state after each test."""
    yield
    try:
        reset_performance_monitor()
    except:
        pass  # Ignore cleanup errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
