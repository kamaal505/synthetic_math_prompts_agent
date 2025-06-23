from core.orchestration.generate_batch import run_generation_pipeline

def run_pipeline_from_config(config: dict) -> dict:
    try:
        valid, discarded = run_generation_pipeline(config)
        return {
            "valid_prompts": valid,
            "discarded_prompts": discarded,
            "metadata": {
                "total_attempted": len(valid) + len(discarded),
                "total_accepted": len(valid)
            }
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise RuntimeError(f"Pipeline crashed: {e}")
