from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import GenerationRequest, GenerationStatus
from app.services.pipeline_service import start_generation_with_database
from app.services.batch_service import get_batch
from app.services.problem_service import get_problem_stats

router = APIRouter()

@router.post("/")
async def start_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start problem generation for a new batch"""
    try:
        result = start_generation_with_database(request, background_tasks, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{batch_id}", response_model=GenerationStatus)
async def get_generation_status(batch_id: int, db: Session = Depends(get_db)):
    """Get the current status of batch generation"""
    batch = get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get problem statistics
    stats = get_problem_stats(db, batch_id)
    
    total_generated = stats['discarded'] + stats['solved'] + stats['valid']
    progress = (stats['valid'] / batch.num_problems * 100) if batch.num_problems > 0 else 0
    
    return GenerationStatus(
        batch_id=batch_id,
        total_needed=batch.num_problems,
        valid_generated=stats['valid'],
        total_generated=total_generated,
        progress_percentage=round(progress, 2),
        stats=stats,
        batch_cost=float(batch.batch_cost),
        status="completed" if stats['valid'] >= batch.num_problems else "in_progress"
    ) 