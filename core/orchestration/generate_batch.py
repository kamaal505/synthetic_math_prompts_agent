import concurrent.futures
import threading
from random import choice
from typing import Any, Dict, List, Tuple

from core.llm.llm_dispatch import call_checker, call_engineer, call_target_model
from core.orchestration.concurrent_processor import create_concurrent_processor
from utils.cost_estimation import safe_log_cost
from utils.costs import CostTracker
from utils.curriculum_strategy import create_curriculum_strategy
from utils.logging_config import get_logger
from utils.performance_monitor import get_performance_monitor
from utils.validation import assert_valid_model_config

from utils.benchmark_seed import load_benchmark
from utils.topic_classifier import classify_subject_topic
from random import choice

# Get logger instance
logger = get_logger(__name__)


def _generate_batch_problems(
    config: Dict[str, Any], cost_tracker: CostTracker, batch_size: int = 3
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a batch of problems using concurrent processing for improved efficiency.

    Args:
        config: Configuration dictionary
        cost_tracker: CostTracker instance
        batch_size: Number of problems to generate concurrently

    Returns:
        Tuple of (result_type, data_dict) containing multiple problems
    """
    thread_id = threading.current_thread().ident
    logger.info(f"🧵 Thread {thread_id} generating batch of {batch_size} problems concurrently")

    taxonomy = config.get("taxonomy")
    engineer_cfg = config["engineer_model"]

    # Initialize curriculum strategy for intelligent topic selection
    curriculum_strategy = create_curriculum_strategy(taxonomy) if taxonomy else None

    try:
        # Use ThreadPoolExecutor for concurrent problem generation
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(batch_size, 5)) as executor:
            # Submit all generation tasks concurrently
            future_to_index = {}
            for i in range(batch_size):
                # Use curriculum strategy for topic selection if available
                if curriculum_strategy:
                    subject, topic, difficulty_level, topic_description = curriculum_strategy.select_topic_and_difficulty()
                else:
                    # Fallback to legacy random selection
                    subject = choice(list(taxonomy.keys())) if taxonomy else config.get("subject")
                    topic = choice(taxonomy[subject]) if taxonomy else config.get("topic")
                    difficulty_level = None
                
                future = executor.submit(call_engineer, subject, topic, None, engineer_cfg, difficulty_level)
                future_to_index[future] = i

            problems = []
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_index):
                batch_index = future_to_index[future]
                try:
                    engineer_result = future.result()
                    safe_log_cost(
                        cost_tracker,
                        engineer_cfg,
                        engineer_result.get("tokens_prompt", 0),
                        engineer_result.get("tokens_completion", 0),
                        raw_output=engineer_result.get("raw_output", ""),
                        raw_prompt=engineer_result.get("raw_prompt", ""),
                    )

                    problem_data = {
                        "subject": subject,
                        "topic": topic,
                        "problem": engineer_result["problem"],
                        "answer": engineer_result["answer"],
                        "hints": engineer_result["hints"],
                        "batch_index": batch_index,
                    }
                    problems.append(problem_data)
                    logger.debug(f"✅ Completed batch problem {batch_index + 1}/{batch_size}")

                except Exception as e:
                    logger.error(f"🚨 Error generating problem {batch_index}: {str(e)}")
                    # Continue with other problems even if one fails

        if not problems:
            return "error", {
                "error": "No problems generated successfully",
                "subject": subject,
                "topic": topic,
                "batch_size": batch_size,
            }

        logger.info(f"🎯 Successfully generated {len(problems)}/{batch_size} problems in batch")
        return "batch_generated", {"problems": problems, "batch_size": len(problems)}

    except Exception as e:
        logger.error("🚨 Error in batch generation: %s", str(e), exc_info=True)
        return "error", {
            "error": str(e),
            "subject": subject,
            "topic": topic,
            "batch_size": batch_size,
        }


def _generate_and_validate_prompt(
    config: Dict[str, Any], cost_tracker: CostTracker
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate and validate a single prompt with enhanced error handling and performance monitoring.

    Args:
        config: Configuration dictionary containing model configs and generation parameters
        cost_tracker: CostTracker instance for logging costs

    Returns:
        tuple: (result_type, data_dict) where result_type is one of:
                - "accepted": prompt was generated and target model failed
                - "discarded": prompt was rejected or target model succeeded
                - "error": an error occurred during generation
    """
    
    thread_id = threading.current_thread().ident
    logger.info(f"🧵 Thread {thread_id} starting task processing")
    
    # Start performance monitoring
    perf_monitor = get_performance_monitor()
    start_time = perf_monitor.start_request(thread_id)
    
    success = False
    retries = 0

    taxonomy = config.get("taxonomy")
    engineer_cfg = config["engineer_model"]
    checker_cfg = config["checker_model"]
    target_cfg = config["target_model"]

    # Initialize curriculum strategy for intelligent topic selection
    curriculum_strategy = create_curriculum_strategy(taxonomy) if taxonomy else None
    
    try:    
        seed_mode = config.get("use_seed_data", False)
        seed = None
        subject = topic = difficulty_level = None

        if seed_mode:
            
            benchmark_name = config.get("benchmark_name", "custom_seed")

            # ✅ Use seed_data if provided, fallback only if necessary
            if "seed_data" in config:
                seed_pool = config["seed_data"]
            else:
                seed_pool = load_benchmark(benchmark_name)

            seed_problem = choice(seed_pool)

            seed = seed_problem["problem"]

            # Classify subject/topic from seed problem
            subject, topic = classify_subject_topic(
                problem_text=seed,
                model_name="gpt-4.1",
                cost_tracker=cost_tracker
            )

            if not subject or not topic:
                logger.warning(f"❌ Classification failed — subject={subject}, topic={topic}")
                return "discarded", {
                    "problem": seed,
                    "answer": seed_problem.get("answer", ""),
                    "rejection_reason": "Subject/topic classification failed",
                }
            
            logger.info(f"🔍 Classified seed: subject={subject}, topic={topic}")

        else:
            if curriculum_strategy:
                subject, topic, difficulty_level, topic_description = curriculum_strategy.select_topic_and_difficulty()
            else:
                subject = choice(list(taxonomy.keys())) if taxonomy else config.get("subject")
                topic = choice(taxonomy[subject]) if taxonomy else config.get("topic")
                difficulty_level = None
                topic_description = None

            if config.get("enable_prefiltering", False):
                if _is_problem_too_easy(subject, topic):
                    logger.info("⚡ Pre-filtered as too easy, skipping")
                    return "discarded", {
                        "subject": subject,
                        "topic": topic,
                        "difficulty_level": difficulty_level,
                        "rejection_reason": "Pre-filtered as too easy",
                    }

        # Step 1: Engineer — generate problem from taxonomy or modify seed
        engineer_result = call_engineer(subject, topic, seed, engineer_cfg, difficulty_level)
        safe_log_cost(
            cost_tracker,
            engineer_cfg,
            engineer_result.get("tokens_prompt", 0),
            engineer_result.get("tokens_completion", 0),
            raw_output=engineer_result.get("raw_output", ""),
            raw_prompt=engineer_result.get("raw_prompt", ""),
        )

        tag = seed_problem.get("tags", ["custom_seed"])[0] if seed_mode else None
        source_id = seed_problem.get("source_id", "N/A") if seed_mode else None
        reference = f"{tag}:{source_id}" if seed_mode else None

        core = {
            "subject": subject,
            "topic": topic,
            "problem": engineer_result["problem"],
            "answer": engineer_result["answer"],
            "hints": engineer_result["hints"],
            "reference": reference,
        }

        if seed_mode:
            core["benchmark_name"] = benchmark_name
            core["source_seed"] = seed


        # Step 2: Checker validation
        checker_result = call_checker(core, checker_cfg, mode="initial")
        safe_log_cost(
            cost_tracker,
            checker_cfg,
            checker_result.get("tokens_prompt", 0),
            checker_result.get("tokens_completion", 0),
            raw_output=checker_result.get("raw_output", ""),
            raw_prompt=checker_result.get("raw_prompt", ""),
        )

        corrected_hints = checker_result.get("corrected_hints")

        core["hints_were_corrected"] = (
            bool(corrected_hints)
            and isinstance(corrected_hints, dict)
            and any(h.strip() for h in corrected_hints.values())
        )

        if not checker_result["valid"]:
            logger.info(f"❌ Rejected: {checker_result.get('reason', '')}")
            return "discarded", {
                **core,
                "rejection_reason": checker_result.get("reason", ""),
            }

        if corrected_hints:
            
            logger.info(f"✍️ Checker revised {len(corrected_hints)} hint(s).")
            for idx_str, revised_hint in corrected_hints.items():
                if idx_str in core["hints"]:
                    core["hints"][idx_str] = revised_hint
                else:
                    logger.warning(f"⚠️ Hint index '{idx_str}' not found in core['hints']")

        else:
            logger.info("✅ Keeping original hints from generator.")

        # Step 3: Target model attempts (with deterministic settings)
        target_result = call_target_model(core["problem"], target_cfg)
        safe_log_cost(
            cost_tracker,
            target_cfg,
            target_result.get("tokens_prompt", 0),
            target_result.get("tokens_completion", 0),
            raw_output=target_result.get("raw_output", ""),
            raw_prompt=target_result.get("raw_prompt", ""),
        )
        core["target_model_answer"] = target_result["output"]

        # Step 4: Checker judges model's answer
        final_check = call_checker(core, checker_cfg, mode="equivalence_check")
        safe_log_cost(
            cost_tracker,
            checker_cfg,
            final_check.get("tokens_prompt", 0),
            final_check.get("tokens_completion", 0),
            raw_output=final_check.get("raw_output", ""),
            raw_prompt=final_check.get("raw_prompt", ""),
        )

        if not final_check.get("valid", False):
            logger.info("🧠 Target model failed — Accepted!")

            # Step 5: Similarity Scoring (optional, with optimization)
            if config.get("use_search", False):
                try:
                    from core.search import score_similarity

                    similarity = score_similarity(core["problem"], cost_tracker=cost_tracker)
                    core["similar_problems"] = {
                        "similarity_score": similarity.get("similarity_score"),
                        "top_matches": similarity.get("top_matches", []),
                    }
                    
                    logger.info(
                        f"🔍 Similarity score: {core['similar_problems']['similarity_score']:.3f}"
                    )
                except Exception as e:
                    logger.error(
                        "⚠️ Error scoring similarity: %s", str(e), exc_info=True
                    )
                    core["similar_problems"] = {
                        "similarity_score": None,
                        "top_matches": [],
                    }

            success = True
            result = "accepted", core
        else:
            logger.info("🟡 Model answered correctly — Discarded.")
            success = True  # Task completed successfully, even if discarded
            result = "discarded", {
                **core,
                "rejection_reason": "Target model solved correctly",
            }

    except Exception as e:
        logger.error("🚨 Error in pipeline task: %s", str(e), exc_info=True)
        success = False
        result = "error", {
            "error": str(e),
            "subject": subject,
            "topic": topic,
        }
    
    finally:
        # Record performance metrics
        perf_monitor.end_request(
            start_time=start_time,
            success=success,
            retries=retries,
            thread_id=thread_id
        )
    
    return result


def _is_problem_too_easy(subject: str, topic: str) -> bool:
    """
    Pre-filtering heuristic to identify potentially easy problems.

    Args:
        subject: Math subject
        topic: Topic within subject

    Returns:
        True if problem is likely too easy
    """
    # Simple heuristics - can be expanded
    easy_topics = {
        "arithmetic": ["addition", "subtraction", "basic multiplication"],
        "algebra": ["linear equations with one variable"],
        "geometry": ["area of rectangle", "perimeter of square"],
    }

    subject_lower = subject.lower()
    topic_lower = topic.lower()

    for easy_subject, easy_topic_list in easy_topics.items():
        if easy_subject in subject_lower:
            for easy_topic in easy_topic_list:
                if easy_topic in topic_lower:
                    return True

    return False


def run_generation_pipeline(
    config: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], CostTracker]:
    """
    Run the enhanced generation pipeline with adaptive threading, caching, and performance monitoring.

    Args:
        config: Configuration dictionary including num_problems, model configs, etc.

    Returns:
        tuple: (accepted_list, discarded_list, cost_tracker)
    """
    logger.info("🚀 Starting enhanced generation pipeline with adaptive threading and caching")

    # Initialize performance monitoring
    perf_monitor = get_performance_monitor()
    perf_monitor.reset()  # Start fresh for this pipeline run

    # Validate model configurations
    engineer_cfg = config["engineer_model"]
    checker_cfg = config["checker_model"]
    target_cfg = config["target_model"]

    assert_valid_model_config("engineer", engineer_cfg)
    assert_valid_model_config("checker", checker_cfg)
    assert_valid_model_config("target", target_cfg)

    # Initialize cost tracker
    cost_tracker = CostTracker()

    # Check if we should use the new concurrent processor
    use_enhanced_processing = config.get("use_enhanced_concurrent_processing", True)

    try:
        if use_enhanced_processing:
            result = _run_enhanced_pipeline(config, cost_tracker)
        else:
            result = _run_legacy_pipeline(config, cost_tracker)
        
        # Log performance summary
        perf_monitor.log_summary()
        
        return result
        
    except Exception as e:
        logger.error("🚨 Pipeline execution failed: %s", str(e), exc_info=True)
        perf_monitor.log_summary()  # Log performance even on failure
        raise


def _run_enhanced_pipeline(
    config: Dict[str, Any], cost_tracker: CostTracker
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], CostTracker]:
    """
    Run the pipeline using the enhanced concurrent processor.

    Args:
        config: Configuration dictionary
        cost_tracker: Cost tracking instance

    Returns:
        Tuple of (accepted, discarded, cost_tracker)
    """
    logger.info("Using enhanced concurrent processing with adaptive threading")

    # Create concurrent processor
    processor = create_concurrent_processor(config)

    # Define task arguments generator
    def generate_task_args():
        return (config, cost_tracker)

    # Define progress callback
    def progress_callback(progress_info: Dict[str, Any]):
        stats = progress_info.get("stats", {})
        logger.info(
            f"📊 Progress: {progress_info['approved']}/{progress_info['target']} "
            f"(Workers: {stats.get('current_workers', 'N/A')}, "
            f"Success Rate: {stats.get('success_rate', 0):.1%})"
        )

    # Process the batch
    accepted, discarded, errors = processor.process_batch(
        task_func=_generate_and_validate_prompt,
        task_args_generator=generate_task_args,
        progress_callback=progress_callback,
    )

    # Combine discarded and errors for backward compatibility
    all_discarded = discarded + errors

    logger.info(
        f"✅ Enhanced pipeline completed: {len(accepted)} accepted, "
        f"{len(all_discarded)} discarded/errors"
    )

    return accepted, all_discarded, cost_tracker


def _run_legacy_pipeline(
    config: Dict[str, Any], cost_tracker: CostTracker
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], CostTracker]:
    """
    Run the pipeline using the legacy concurrent processing (for backward compatibility).

    Args:
        config: Configuration dictionary
        cost_tracker: Cost tracking instance

    Returns:
        Tuple of (accepted, discarded, cost_tracker)
    """
    logger.info("Using legacy concurrent processing")

    accepted = []
    discarded = []

    target_total = config["num_problems"]
    approved_count = 0
    attempt_counter = 0

    max_workers = config.get("max_workers", 10)
    logger.info(f"🚀 Starting parallel execution with {max_workers} worker threads")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        while approved_count < target_total:
            batch_size = min(
                max_workers * 2, target_total - approved_count + len(discarded)
            )

            while len(futures) < batch_size and (approved_count < target_total):
                attempt_counter += 1
                future = executor.submit(
                    _generate_and_validate_prompt, config, cost_tracker
                )
                futures.append((future, attempt_counter))

            if futures:
                completed_futures = []
                for future, attempt_num in futures:
                    if future.done():
                        completed_futures.append((future, attempt_num))

                if not completed_futures:
                    done_futures = concurrent.futures.as_completed(
                        [f[0] for f in futures], timeout=None
                    )
                    first_done = next(done_futures)
                    for future, attempt_num in futures:
                        if future == first_done:
                            completed_futures.append((future, attempt_num))
                            break

                for future, attempt_num in completed_futures:
                    try:
                        result_type, data = future.result()
                        logger.info(
                            f"🔧 Attempt {attempt_num} — Approved so far: {approved_count}/{target_total}"
                        )

                        if result_type == "accepted":
                            accepted.append(data)
                            approved_count += 1
                        else:
                            discarded.append(data)
                    except Exception as e:
                        logger.error(
                            "🚨 Future execution error in attempt %s: %s",
                            attempt_num,
                            str(e),
                            exc_info=True,
                        )
                        discarded.append(
                            {"error": str(e), "attempt_number": attempt_num}
                        )

                    futures.remove((future, attempt_num))

    return accepted, discarded, cost_tracker