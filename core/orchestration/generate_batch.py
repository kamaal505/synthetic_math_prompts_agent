from pathlib import Path
from random import choice
from core.llm.llm_dispatch import call_engineer, call_checker, call_target_model
from utils.validation import assert_valid_model_config

def run_generation_pipeline(config):
    accepted = []
    discarded = []

    get_seed_prompt = None
    if config.get("use_search", False):
        from search.web_search import get_seed_prompt

    target_total = config["num_problems"]
    approved_count = 0
    attempt_counter = 0

    engineer_cfg = config.get("engineer_model", {})
    checker_cfg = config.get("checker_model", {})
    target_cfg = config.get("target_model", {})

    # Validate configs before starting
    assert_valid_model_config("engineer", engineer_cfg)
    assert_valid_model_config("checker", checker_cfg)
    assert_valid_model_config("target", target_cfg)

    while approved_count < target_total:
        attempt_counter += 1
        print(f"\n🔧 Attempt {attempt_counter} — Approved so far: {approved_count}/{target_total}")

        taxonomy = config.get("taxonomy")
        if taxonomy:
            subject = choice(list(taxonomy.keys()))
            topic = choice(taxonomy[subject])
        else:
            subject = config.get("subject")
            topic = config.get("topic")

        seed_prompt = get_seed_prompt(subject, topic) if get_seed_prompt else None

        try:
            # Step 1: Engineer generates full problem
            core = call_engineer(subject, topic, seed_prompt, engineer_cfg)
            core.update({"subject": subject, "topic": topic})

            # Step 2: Checker validates problem + hints
            result = call_checker(core, checker_cfg, mode="initial")
            corrected_hints = result.get("corrected_hints")

            core["hints_were_corrected"] = (
                bool(corrected_hints)
                and isinstance(corrected_hints, dict)
                and any(h.strip() for h in corrected_hints.values())
            )

            if not result["valid"]:
                print(f"❌ Rejected: {result.get('reason', '')}")
                discarded.append({**core, "rejection_reason": result.get("reason", "")})
                continue

            if isinstance(corrected_hints, dict) and corrected_hints:
                print(f"✍️ Checker revised {len(corrected_hints)} hint(s).")
                core["hints"] = corrected_hints
            elif isinstance(corrected_hints, dict):
                print("⚠️ Checker returned empty corrected_hints — keeping original.")
            else:
                print("✅ Keeping original hints from generator.")

            # Step 3: Target model attempts the problem
            core["target_model_answer"] = call_target_model(core["problem"], target_cfg)

            # Step 4: Checker evaluates model's answer for correctness
            check = call_checker(core, checker_cfg, mode="equivalence_check")

            if not check.get("valid", False):
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

    return accepted, discarded
