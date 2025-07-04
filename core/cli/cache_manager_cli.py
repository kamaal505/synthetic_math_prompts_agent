"""
Cache and Performance Management CLI

This module provides command-line tools for managing the LLM cache
and monitoring performance of the synthetic math prompts system.
"""

import argparse
import sys
from pathlib import Path

from utils.logging_config import get_logger
from utils.performance_monitor import (
    create_cache_manager,
    create_performance_monitor,
    print_cache_info,
    print_performance_report,
)

# Get logger instance
logger = get_logger(__name__)


def handle_cache_info():
    """Display cache information."""
    try:
        cache_manager = create_cache_manager()
        cache_info = cache_manager.get_cache_info()
        print_cache_info(cache_info)
    except Exception as e:
        logger.error(f"Failed to get cache info: {e}")
        return 1
    return 0


def handle_cache_clear():
    """Clear the LLM cache."""
    try:
        cache_manager = create_cache_manager()

        # Ask for confirmation
        response = input("Are you sure you want to clear the cache? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("Cache clear cancelled.")
            return 0

        success = cache_manager.clear_cache()
        if success:
            print("✅ Cache cleared successfully.")
        else:
            print("❌ Failed to clear cache.")
            return 1
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return 1
    return 0


def handle_cache_optimize():
    """Optimize the cache storage."""
    try:
        cache_manager = create_cache_manager()
        result = cache_manager.optimize_cache()

        print("Cache Optimization Results:")
        print(f"  Initial entries: {result['initial_entries']}")
        print(f"  Final entries: {result['final_entries']}")
        print(f"  Entries removed: {result['entries_removed']}")
        print(f"  Success: {result['optimization_successful']}")

    except Exception as e:
        logger.error(f"Failed to optimize cache: {e}")
        return 1
    return 0


def handle_performance_test():
    """Run a performance test with monitoring."""
    try:
        from core.orchestration.generate_batch import run_generation_pipeline
        from utils.config_manager import get_config_manager

        # Load configuration
        config_manager = get_config_manager()
        config_manager.load_config(Path("config/settings.yaml"))

        # Override for a small test
        config_manager.set("num_problems", 3)
        config_manager.set("max_workers", 2)

        # Create performance monitor
        monitor = create_performance_monitor()
        monitor.start_monitoring()

        print("🚀 Running performance test with 3 problems...")

        # Run the pipeline
        config = config_manager.get_all()
        accepted, discarded, cost_tracker = run_generation_pipeline(config)

        # Stop monitoring and get report
        report = monitor.stop_monitoring()

        print(f"\n📊 Test Results:")
        print(f"  Accepted: {len(accepted)}")
        print(f"  Discarded: {len(discarded)}")

        # Print performance report
        print_performance_report(report)

    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return 1
    return 0


def create_parser():
    """Create the argument parser for cache management CLI."""
    parser = argparse.ArgumentParser(
        description="Cache and Performance Management for Synthetic Math Prompts Agent"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Cache management commands
    cache_parser = subparsers.add_parser("cache", help="Cache management")
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_action", help="Cache actions"
    )

    cache_subparsers.add_parser("info", help="Show cache information and statistics")
    cache_subparsers.add_parser("clear", help="Clear all cached responses")
    cache_subparsers.add_parser("optimize", help="Optimize cache storage")

    # Performance commands
    perf_parser = subparsers.add_parser("performance", help="Performance monitoring")
    perf_subparsers = perf_parser.add_subparsers(
        dest="perf_action", help="Performance actions"
    )

    perf_subparsers.add_parser("test", help="Run a performance test with monitoring")

    return parser


def main():
    """Main entry point for the cache manager CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "cache":
            if not args.cache_action:
                print("Cache command requires an action. Use --help for options.")
                return 1

            if args.cache_action == "info":
                return handle_cache_info()
            elif args.cache_action == "clear":
                return handle_cache_clear()
            elif args.cache_action == "optimize":
                return handle_cache_optimize()
            else:
                print(f"Unknown cache action: {args.cache_action}")
                return 1

        elif args.command == "performance":
            if not args.perf_action:
                print("Performance command requires an action. Use --help for options.")
                return 1

            if args.perf_action == "test":
                return handle_performance_test()
            else:
                print(f"Unknown performance action: {args.perf_action}")
                return 1

        else:
            print(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
