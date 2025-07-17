from app.models.schemas import GenerationRequest
from core.runner import run_pipeline_from_config
from fastapi import BackgroundTasks
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services import batch_service, problem_service
from app.models.schemas import BatchCreate, ProblemCreate
from datetime import datetime
from decimal import Decimal
import json
from utils.similarity_utils import fetch_embedding

def run_pipeline(request: GenerationRequest):
    config = {
        "num_problems": request.num_problems,
        "engineer_model": request.engineer_model.dict(),
        "checker_model": request.checker_model.dict(),
        "target_model": request.target_model.dict(),
        "use_search": request.use_search,
    }

    if request.use_seed_data:
        config["use_seed_data"] = True
        # 👇 Only include if explicitly provided
        if request.benchmark_name:
            config["benchmark_name"] = request.benchmark_name
        if request.seed_data:
            config["seed_data"] = request.seed_data
    else:
        config["taxonomy"] = request.taxonomy

    return run_pipeline_from_config(config)


async def run_pipeline_background(
    batch_id: int,
    config: dict
):
    """Background task to run the pipeline and save results to BigQuery"""
    try:
        # Run the blocking pipeline in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(executor, run_pipeline_from_config, config)
        
        valid_prompts = result["valid_prompts"]
        discarded_prompts = result["discarded_prompts"]
        total_cost = result["total_cost"]
        
        # Update batch cost with the total cost from the pipeline
        batch_service.update_batch_cost(batch_id, total_cost)
        
        # Save valid prompts to BigQuery
        for prompt in valid_prompts:
            # Fetch embedding for the problem text
            problem_text = prompt["problem"]
            try:
                embedding_list = fetch_embedding(problem_text)
                # Convert list to dict for storage
                problem_embedding = {"embedding": embedding_list}
            except Exception as e:
                print(f"Failed to fetch embedding for problem: {str(e)}")
                problem_embedding = None
            
            problem_data = {
                "batch_id": batch_id,
                "subject": prompt["subject"],
                "topic": prompt["topic"],
                "question": prompt["problem"],
                "answer": prompt["answer"],
                "hints": prompt["hints"],
                "status": "valid",
                "target_model_answer": prompt.get("target_model_answer"),
                "hints_were_corrected": prompt.get("hints_were_corrected", False),
                "cost": 0.00,  # No cost calculation as requested
                "problem_embedding": problem_embedding,
                "similar_problems": prompt.get("similar_problems", {}),
                "reference": prompt.get("reference")
            }
            problem_service.create_problem(problem_data)
        
        # Save discarded prompts to BigQuery
        for prompt in discarded_prompts:
            problem_text = prompt.get("problem", "")
            problem_embedding = None
            if problem_text:
                try:
                    embedding_list = fetch_embedding(problem_text)
                    problem_embedding = {"embedding": embedding_list}
                except Exception as e:
                    print(f"Failed to fetch embedding for discarded problem: {str(e)}")
            problem_data = {
                "batch_id": batch_id,
                "subject": prompt.get("subject", ""),
                "topic": prompt.get("topic", ""),
                "question": prompt.get("problem", ""),
                "answer": prompt.get("answer", ""),
                "hints": prompt.get("hints", {}),
                "status": "discarded",
                "rejection_reason": prompt.get("rejection_reason", ""),
                "target_model_answer": prompt.get("target_model_answer"),
                "hints_were_corrected": prompt.get("hints_were_corrected", False),
                "cost": 0.00,
                "problem_embedding": problem_embedding,
                "similar_problems": prompt.get("similar_problems", {})
            }
            problem_service.create_problem(problem_data)
        print(f"Background pipeline completed for batch {batch_id}. Total cost: ${total_cost:.6f}")
    except Exception as e:
        print(f"Error in background pipeline: {str(e)}")

def start_generation_with_database(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """Start generation and save to BigQuery"""
    try:
        # Create batch record with initial cost of 0.00
        batch_data = {
            "name": f"Batch_{request.target_model.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "taxonomy_json": request.taxonomy or {},
            "pipeline": {
                "engineer_model": request.engineer_model.dict() if hasattr(request.engineer_model, 'dict') else request.engineer_model,
                "checker_model": request.checker_model.dict() if hasattr(request.checker_model, 'dict') else request.checker_model,
                "target_model": request.target_model.dict() if hasattr(request.target_model, 'dict') else request.target_model,
                "use_seed_data": request.use_seed_data,
                "benchmark_name": request.benchmark_name,
            },
            "num_problems": request.num_problems,
            "batch_cost": 0.00
        }
        batch = batch_service.create_batch(batch_data)
        # Prepare config for background task
        config = {
            "num_problems": request.num_problems,
            "engineer_model": batch_data["pipeline"]["engineer_model"],
            "checker_model": batch_data["pipeline"]["checker_model"],
            "target_model": batch_data["pipeline"]["target_model"],
            "use_search": request.use_search,
        }
        if request.use_seed_data:
            config["use_seed_data"] = True
            config["benchmark_name"] = request.benchmark_name
            if request.seed_data:
                config["seed_data"] = request.seed_data
        else:
            config["taxonomy"] = request.taxonomy
        # Start background task
        background_tasks.add_task(
            run_pipeline_background,
            batch["id"],
            config
        )
        return {
            "status": "started",
            "batch_id": batch["id"],
            "message": f"Generation started for batch {batch['id']}. Generating {request.num_problems} valid problems.",
            "total_cost": 0.00
        }
    except Exception as e:
        raise RuntimeError(f"Failed to start generation: {str(e)}")

