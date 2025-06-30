import concurrent.futures
import threading
from random import choice

from core.llm.llm_dispatch import call_checker, call_engineer, call_target_model
from utils.costs import CostTracker
from utils.logging_config import log_error, log_info
from utils.validation import assert_valid_model_config


def _generate_and_validate_prompt(config, cost_tracker):
    """
    Generate and validate a single prompt.

    Args:
        config: Configuration dictionary containing model configs and generation parameters
        cost_tracker: CostTracker instance for logging costs

    Returns:
        tuple: (result_type, data_dict) where result_type is one of:
                - "accepted": prompt was generated and target model failed
                - "discarded": prompt was rejected or target model succeeded
                - "error": an error occurred during generation
    """
    # Log thread start with thread ID
    thread_id = threading.current_thread().ident
    log_info(f"🧵 Thread {thread_id} starting task processing")

    taxonomy = config.get("taxonomy")
    subject = choice(list(taxonomy.keys())) if taxonomy else config.get("subject")
    topic = choice(taxonomy[subject]) if taxonomy else config.get("topic")

    get_seed_prompt = None
    if config.get("use_search", False):
        from search.web_search import get_seed_prompt

    seed_prompt = get_seed_prompt(subject, topic) if get_seed_prompt else None

    engineer_cfg = config["engineer_model"]
    checker_cfg = config["checker_model"]
    target_cfg = config["target_model"]

    try:
        # Step 1: Engineer
        engineer_result = call_engineer(subject, topic, seed_prompt, engineer_cfg)
        cost_tracker.log(
            engineer_cfg,
            engineer_result["tokens_prompt"],
            engineer_result["tokens_completion"],
        )
        core = {
            "subject": subject,
            "topic": topic,
            "problem": engineer_result["problem"],
            "answer": engineer_result["answer"],
            "hints": engineer_result["hints"],
        }

        # Step 2: Checker validation
        checker_result = call_checker(core, checker_cfg, mode="initial")
        cost_tracker.log(
            checker_cfg,
            checker_result["tokens_prompt"],
            checker_result["tokens_completion"],
        )

        corrected_hints = checker_result.get("corrected_hints")

        core["hints_were_corrected"] = (
            bool(corrected_hints)
            and isinstance(corrected_hints, dict)
            and any(h.strip() for h in corrected_hints.values())
        )

        if not checker_result["valid"]:
            log_info(f"❌ Rejected: {checker_result.get('reason', '')}")
            return "discarded", {
                **core,
                "rejection_reason": checker_result.get("reason", ""),
            }

        if corrected_hints:
            log_info(f"✍️ Checker revised {len(corrected_hints)} hint(s).")
            core["hints"] = corrected_hints
        else:
            log_info("✅ Keeping original hints from generator.")

        # Step 3: Target model attempts
        target_result = call_target_model(core["problem"], target_cfg)
        cost_tracker.log(
            target_cfg,
            target_result["tokens_prompt"],
            target_result["tokens_completion"],
        )
        core["target_model_answer"] = target_result["output"]

        # Step 4: Checker judges model's answer
        final_check = call_checker(core, checker_cfg, mode="equivalence_check")
        cost_tracker.log(
            checker_cfg, final_check["tokens_prompt"], final_check["tokens_completion"]
        )

        if not final_check.get("valid", False):
            log_info("🧠 Target model failed — Accepted!")
            return "accepted", core
        else:
            log_info("🟡 Model answered correctly — Discarded.")
            return "discarded", {
                **core,
                "rejection_reason": "Target model solved correctly",
            }

    except Exception as e:
        log_error(f"🚨 Error in pipeline task", exception=e)
        return "error", {
            "error": str(e),
            "subject": subject,
            "topic": topic,
            "seed_prompt": seed_prompt,
        }


def run_generation_pipeline(config):
    """
    Runs the full synthetic prompt generation pipeline with parallel execution and tracks cost.

    Returns:
        accepted: List of approved problems
        discarded: List of rejected or failed problems
        cost_tracker: CostTracker instance with cost breakdown
    """
    accepted = []
    discarded = []
    cost_tracker = CostTracker()

    target_total = config["num_problems"]
    approved_count = 0
    attempt_counter = 0

    engineer_cfg = config["engineer_model"]
    checker_cfg = config["checker_model"]
    target_cfg = config["target_model"]

    assert_valid_model_config("engineer", engineer_cfg)
    assert_valid_model_config("checker", checker_cfg)
    assert_valid_model_config("target", target_cfg)

    # Get number of workers from config, default to 10
    max_workers = config.get("max_workers", 10)

    # Log parallel execution start with worker count
    log_info(f"🚀 Starting parallel execution with {max_workers} worker threads")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit initial batch of tasks
        futures = []

        while approved_count < target_total:
            # Calculate how many more attempts we need to submit
            # We want to keep a reasonable number of futures in flight
            batch_size = min(
                max_workers * 2, target_total - approved_count + len(discarded)
            )

            # Submit new tasks if we need more futures
            while len(futures) < batch_size and (approved_count < target_total):
                attempt_counter += 1
                future = executor.submit(
                    _generate_and_validate_prompt, config, cost_tracker
                )
                futures.append((future, attempt_counter))

            # Process completed futures
            if futures:
                # Wait for at least one future to complete
                completed_futures = []
                for future, attempt_num in futures:
                    if future.done():
                        completed_futures.append((future, attempt_num))

                # If no futures are done yet, wait for the first one
                if not completed_futures:
                    done_futures = concurrent.futures.as_completed(
                        [f[0] for f in futures], timeout=None
                    )
                    first_done = next(done_futures)
                    # Find the corresponding attempt number
                    for future, attempt_num in futures:
                        if future == first_done:
                            completed_futures.append((future, attempt_num))
                            break

                # Process all completed futures
                for future, attempt_num in completed_futures:
                    try:
                        result_type, data = future.result()
                        log_info(
                            f"🔧 Attempt {attempt_num} — Approved so far: {approved_count}/{target_total}"
                        )

                        if result_type == "accepted":
                            accepted.append(data)
                            approved_count += 1
                        else:  # "discarded" or "error"
                            discarded.append(data)
                    except Exception as e:
                        log_error(
                            f"🚨 Future execution error in attempt {attempt_num}", exception=e
                        )
                        discarded.append(
                            {"error": str(e), "attempt_number": attempt_num}
                        )

                    # Remove completed future from the list
                    futures.remove((future, attempt_num))

    return accepted, discarded, cost_tracker
