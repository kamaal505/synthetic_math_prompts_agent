from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.schemas import Batch, BatchWithStats, TargetModelUpdate
from app.services.batch_service import get_batches, get_batch, delete_batch, update_batch_target_model, get_problems_count
from app.services.problem_service import get_problem_stats

router = APIRouter()

@router.get("/", response_model=List[BatchWithStats])
def get_all_batches(db: Session = Depends(get_db)):
    batches = get_batches(db)
    result = []
    for batch in batches:
        stats = get_problem_stats(db, batch.id)
        batch_dict = Batch.from_orm(batch).dict()
        batch_dict['stats'] = stats
        result.append(BatchWithStats(**batch_dict))
    return result

@router.get("/{batch_id}", response_model=BatchWithStats)
def get_batch_by_id(batch_id: int, db: Session = Depends(get_db)):
    batch = get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get problem statistics
    stats = get_problem_stats(db, batch_id)
    
    # Convert to dict and add stats
    batch_dict = Batch.from_orm(batch).dict()
    batch_dict['stats'] = stats
    
    return BatchWithStats(**batch_dict)

@router.delete("/{batch_id}")
def delete_batch_by_id(batch_id: int, db: Session = Depends(get_db)):
    success = delete_batch(db, batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"message": "Batch deleted"}

@router.patch("/{batch_id}/target-model")
def update_target_model(batch_id: int, target_update: TargetModelUpdate, db: Session = Depends(get_db)):
    """Update the target model for a specific batch"""
    # Check if batch exists
    batch = get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Update the target model
    updated_batch = update_batch_target_model(db, batch_id, target_update.target_model.dict())
    if not updated_batch:
        raise HTTPException(status_code=500, detail="Failed to update target model")
    
    return {
        "message": "Target model updated successfully",
        "batch_id": batch_id,
        "new_target_model": target_update.target_model.dict()
    }

@router.get("/problems/count")
def get_problems_count_endpoint(batch_id: Optional[int] = Query(None, description="Optional batch ID to get count for specific batch"), db: Session = Depends(get_db)):
    """Get the number of problems - either for a specific batch or total across all batches"""
    if batch_id is not None:
        # Check if batch exists
        batch = get_batch(db, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Get count for specific batch
        result = get_problems_count(db, batch_id)
        result["batch_name"] = batch.name
        
        return result
    else:
        # Get total count across all batches
        return get_problems_count(db) 