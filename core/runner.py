from core.orchestration.generate_batch import run_generation_pipeline

def run_pipeline_from_config(config: dict) -> dict:
    try:
        print(f"\n🚀 Starting Math Agent Pipeline...")
        print(f"   Target problems: {config.get('num_problems', 'N/A')}")
        print(f"   Engineer: {config.get('engineer_model', {}).get('provider', 'N/A')}/{config.get('engineer_model', {}).get('model_name', 'N/A')}")
        print(f"   Checker: {config.get('checker_model', {}).get('provider', 'N/A')}/{config.get('checker_model', {}).get('model_name', 'N/A')}")
        print(f"   Target: {config.get('target_model', {}).get('provider', 'N/A')}/{config.get('target_model', {}).get('model_name', 'N/A')}")
        print(f"   Subject: {config.get('subject', 'N/A')}")
        print(f"   Topic: {config.get('topic', 'N/A')}")
        print("=" * 60)
        
        valid, discarded, cost_tracker = run_generation_pipeline(config)
        total_cost = cost_tracker.get_total_cost()
        
        print(f"\n🎉 Pipeline completed!")
        print(f"   Valid problems: {len(valid)}")
        print(f"   Discarded problems: {len(discarded)}")
        print(f"   Total cost: ${total_cost:.4f}")
        
        return {
            "valid_prompts": valid,
            "discarded_prompts": discarded,
            "total_cost": total_cost,
            "metadata": {
                "total_attempted": len(valid) + len(discarded),
                "total_accepted": len(valid)
            }
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise RuntimeError(f"Pipeline crashed: {e}")
