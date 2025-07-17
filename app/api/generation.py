from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import GenerationRequest, GenerationStatus
from app.services.pipeline_service import start_generation_with_database
from app.services import batch_service
from app.services import problem_service

router = APIRouter()

@router.post("/")
async def start_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """Start problem generation for a new batch"""
    try:
        return start_generation_with_database(request, background_tasks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{batch_id}", response_model=GenerationStatus)
async def get_generation_status(batch_id: int):
    """Get the current status of batch generation"""
    batch = batch_service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get problem statistics
    stats = problem_service.get_problem_stats(batch_id)
    
    total_generated = stats.get('discarded', 0) + stats.get('solved', 0) + stats.get('valid', 0)
    progress = (stats.get('valid', 0) / batch['num_problems'] * 100) if batch['num_problems'] > 0 else 0
    
    return GenerationStatus(
        batch_id=batch_id,
        total_needed=batch['num_problems'],
        valid_generated=stats.get('valid', 0),
        total_generated=total_generated,
        progress_percentage=round(progress, 2),
        stats=stats,
        batch_cost=float(batch['batch_cost']),
        status="completed" if stats.get('valid', 0) >= batch['num_problems'] else "in_progress"
    ) 