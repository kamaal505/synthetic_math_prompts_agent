from pathlib import Path
from random import choice
from core.engineer.generate_prompt import generate_full_problem
from core.checker.validate_prompt import validate_problem
from core.orchestration.evaluate_target_model import model_attempts_answer

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
            print(f"\n🚀 Starting generation for {subject} - {topic}")
            core = generate_full_problem(
                seed=seed_prompt,
                subject=subject,
                topic=topic,
                provider=engineer_cfg.get("provider", "gemini"),
                model_name=engineer_cfg.get("model_name", "gemini-2.5-pro")
            )
            core.update({"subject": subject, "topic": topic})

            print(f"\n🔍 Starting initial validation...")
            result = validate_problem(
                core, mode="initial",
                provider=checker_cfg.get("provider", "openai"),
                model_name=checker_cfg.get("model_name", "o3-mini")
            )
            corrected_hints = result.get("corrected_hints")

            core["hints_were_corrected"] = bool(corrected_hints) and isinstance(corrected_hints, dict) and any(h.strip() for h in corrected_hints.values())

            # if not result["valid"]:
            #     print(f"❌ Rejected: {result.get('reason', '')}")
            #     discarded.append({**core, "rejection_reason": result.get("reason", "")})
            #     continue

            if isinstance(corrected_hints, dict) and corrected_hints:
                print(f"✍️ Checker revised {len(corrected_hints)} hint(s).")
                core["hints"] = corrected_hints
            elif isinstance(corrected_hints, dict):
                print("⚠️ Checker returned empty corrected_hints — keeping original.")
            else:
                print("✅ Keeping original hints from generator.")

            print(f"\n🎯 Getting target model answer...")
            core["target_model_answer"] = model_attempts_answer(core["problem"], config["target_model"])

            print(f"\n🔍 Starting equivalence check...")
            check = validate_problem(
                core, mode="equivalence_check",
                provider=checker_cfg.get("provider", "openai"),
                model_name=checker_cfg.get("model_name", "o3-mini")
            )

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
