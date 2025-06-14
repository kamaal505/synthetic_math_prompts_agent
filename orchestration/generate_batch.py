import yaml
from pathlib import Path
from random import choice
from engineer.generate_prompt import generate_problem_shell, generate_hints
from checker.validate_prompt import validate_problem
from orchestration.evaluate_target_model import model_attempts_answer

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_generation_pipeline(config):
    accepted = []
    discarded = []

    get_seed_prompt = None
    if config.get("use_search", False):
        from search.web_search import get_seed_prompt

    target_total = config["num_problems"]
    approved_count = 0
    attempt_counter = 0

    while approved_count < target_total:
        attempt_counter += 1
        print(f"\n🔧 Attempt {attempt_counter} — Approved so far: {approved_count}/{target_total}")

        subject = choice(list(config["subjects"].keys()))
        topic = choice(config["subjects"][subject])
        seed_prompt = get_seed_prompt(subject, topic) if get_seed_prompt else None

        try:
            metadata = {"subject": subject, "topic": topic}
            core = generate_problem_shell(seed=seed_prompt, subject=subject, topic=topic)
            core.update(metadata)

            # 🔄 Generate hints as dictionary
            core["hints"] = generate_hints(core["problem"], core["answer"])

            # ✅ Validate problem and hints
            result = validate_problem(core, mode="initial")
            corrected_hints = result.get("corrected_hints")

            # Track whether checker modified the hints
            core["hints_were_corrected"] = bool(corrected_hints) and isinstance(corrected_hints, dict) and any(h.strip() for h in corrected_hints.values())

            if not result["valid"]:
                print(f"❌ Rejected: {result.get('reason', '')}")
                discarded.append({**core, "rejection_reason": result.get("reason", "")})
                continue

            # 🛠 If checker provided corrections, replace hints
            if isinstance(corrected_hints, dict) and corrected_hints:
                diffs = sum(
                    1 for k in corrected_hints
                    if k not in core["hints"] or core["hints"][k].strip() != corrected_hints[k].strip()
                )
                print(f"✍️ Checker revised {diffs} hint(s).")
                core["hints"] = corrected_hints

            elif isinstance(corrected_hints, dict) and not corrected_hints:
                print("⚠️ Checker returned empty corrected_hints — keeping original.")

            else:
                print("✅ Keeping original hints from hint generator.")

            # 🤖 Run the model's attempt at solving the problem
            model_response = model_attempts_answer(core["problem"], config["target_model"])
            core["target_model_answer"] = model_response

            # 🧪 Check model's answer against ground truth
            check = validate_problem(core, mode="equivalence_check")
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

if __name__ == "__main__":
    config_path = Path("config/settings.yaml")
    config = load_config(config_path)

    valid, rejected = run_generation_pipeline(config)

    print(f"\n✅ {len(valid)} accepted | ❌ {len(rejected)} discarded")

    from orchestration.save_results import save_prompts
    save_path = Path(config["output_dir"]) / config.get("default_batch_id", "batch_01")
    save_prompts(valid, rejected, save_path)
