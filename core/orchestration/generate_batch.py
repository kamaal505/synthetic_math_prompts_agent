from pathlib import Path
from random import choice
from core.llm.llm_dispatch import call_engineer, call_checker, call_target_model
from utils.validation import assert_valid_model_config
from utils.costs import CostTracker
import json


def run_generation_pipeline(config):
    """
    Runs the full synthetic prompt generation pipeline and tracks cost.

    Returns:
        accepted: List of approved problems
        discarded: List of rejected or failed problems
        cost_tracker: CostTracker instance with cost breakdown
    """
    accepted = []
    discarded = []
    cost_tracker = CostTracker()

    get_seed_prompt = None
    if config.get("use_search", False):
        from search.web_search import get_seed_prompt

    target_total = config["num_problems"]
    approved_count = 0
    attempt_counter = 0

    engineer_cfg = config["engineer_model"]
    checker_cfg = config["checker_model"]
    target_cfg = config["target_model"]

    assert_valid_model_config("engineer", engineer_cfg)
    assert_valid_model_config("checker", checker_cfg)
    assert_valid_model_config("target", target_cfg)

    while approved_count < target_total:
        attempt_counter += 1
        print(f"\n🔧 Attempt {attempt_counter} — Approved so far: {approved_count}/{target_total}")

        taxonomy = config.get("taxonomy")
        subject = choice(list(taxonomy.keys())) if taxonomy else config.get("subject")
        topic = choice(taxonomy[subject]) if taxonomy else config.get("topic")

        seed_prompt = get_seed_prompt(subject, topic) if get_seed_prompt else None

        try:
            # Step 1: Engineer
            print(f"\n🤖 Calling ENGINEER model ({engineer_cfg['provider']}/{engineer_cfg['model_name']})...")
            engineer_result = call_engineer(subject, topic, seed_prompt, engineer_cfg)
            cost_tracker.log(engineer_cfg, engineer_result["tokens_prompt"], engineer_result["tokens_completion"])
            print(f"✅ ENGINEER Response:")
            print(f"   Subject: {engineer_result['subject']}")
            print(f"   Topic: {engineer_result['topic']}")
            print(f"   Problem: {engineer_result['problem'][:100]}...")
            print(f"   Answer: {engineer_result['answer']}")
            print(f"   Hints: {len(engineer_result['hints'])} hints generated")
            
            core = {
                "subject": engineer_result["subject"],
                "topic": engineer_result["topic"],
                "problem": engineer_result["problem"],
                "answer": engineer_result["answer"],
                "hints": engineer_result["hints"]
            }

            # Step 2: Checker validation
            print(f"\n🔍 Calling CHECKER model ({checker_cfg['provider']}/{checker_cfg['model_name']}) for initial validation...")
            checker_result = call_checker(core, checker_cfg, mode="initial")
            cost_tracker.log(checker_cfg, checker_result["tokens_prompt"], checker_result["tokens_completion"])
            print(f"✅ CHECKER Response:")
            print(f"   Valid: {checker_result['valid']}")
            if not checker_result['valid']:
                print(f"   Reason: {checker_result.get('reason', 'No reason provided')}")
            if checker_result.get('corrected_hints'):
                print(f"   Corrected hints: {len(checker_result['corrected_hints'])} hints revised")

            corrected_hints = checker_result.get("corrected_hints")

            core["hints_were_corrected"] = (
                bool(corrected_hints)
                and isinstance(corrected_hints, dict)
                and any(h.strip() for h in corrected_hints.values())
            )

            if not checker_result["valid"]:
                print(f"❌ Rejected: {checker_result.get('reason', '')}")
                discarded.append({**core, "rejection_reason": checker_result.get("reason", "")})
                continue

            if corrected_hints:
                print(f"✍️ Checker revised {len(corrected_hints)} hint(s).")
                core["hints"] = corrected_hints
            else:
                print("✅ Keeping original hints from generator.")

            # Step 3: Target model attempts
            print(f"\n🧠 Calling TARGET model ({target_cfg['provider']}/{target_cfg['model_name']}) to solve the problem...")
            target_result = call_target_model(core["problem"], target_cfg)
            cost_tracker.log(target_cfg, target_result["tokens_prompt"], target_result["tokens_completion"])
            print(f"✅ TARGET Response:")
            print(f"   Model Answer: {target_result['output']}")
            print(f"   Expected Answer: {core['answer']}")
            
            core["target_model_answer"] = target_result["output"]

            # Step 4: Checker judges model's answer
            print(f"\n🔍 Calling CHECKER model ({checker_cfg['provider']}/{checker_cfg['model_name']}) for equivalence check...")
            final_check = call_checker(core, checker_cfg, mode="equivalence_check")
            cost_tracker.log(checker_cfg, final_check["tokens_prompt"], final_check["tokens_completion"])
            print(f"✅ CHECKER Equivalence Response:")
            print(f"   Valid (model solved correctly): {final_check.get('valid', False)}")
            if final_check.get('reason'):
                print(f"   Reason: {final_check['reason']}")

            if not final_check.get("valid", False):
                print("🧠 Target model failed — Accepted!")
                accepted.append(core)
                approved_count += 1
            else:
                print("🟡 Model answered correctly — Discarded.")
                discarded.append({**core, "rejection_reason": "Target model solved correctly"})

        except Exception as e:
            print(f"🚨 Error: {e}")
            discarded.append({
                "error": str(e),
                "subject": subject,
                "topic": topic,
                "seed_prompt": seed_prompt
            })

    return accepted, discarded, cost_tracker
