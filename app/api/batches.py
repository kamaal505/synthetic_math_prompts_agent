from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.models.schemas import Batch, BatchWithStats
from app.services.batch_service import get_batches, get_batch, delete_batch
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