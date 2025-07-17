from fastapi import APIRouter, HTTPException
from app.models.schemas import BatchCreate, Batch
from app.services import batch_service
from typing import List

router = APIRouter()

@router.post("/", response_model=Batch)
def create_batch(batch: BatchCreate):
    """Create a new batch."""
    try:
        return batch_service.create_batch(batch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")

@router.get("/", response_model=List[Batch])
def get_batches(skip: int = 0, limit: int = 100):
    """Get all batches with pagination."""
    try:
        return batch_service.get_batches(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batches: {str(e)}")

@router.get("/{batch_id}", response_model=Batch)
def get_batch(batch_id: int):
    """Get a specific batch by ID."""
    try:
        batch = batch_service.get_batch(batch_id)
        if batch is None:
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch: {str(e)}")

@router.delete("/{batch_id}")
def delete_batch(batch_id: int):
    """Delete a batch and all its associated problems."""
    try:
        success = batch_service.delete_batch(batch_id)
        if not success:
            raise HTTPException(status_code=404, detail="Batch not found")
        return {"message": "Batch deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete batch: {str(e)}")

@router.get("/{batch_id}/problems-count")
def get_batch_problems_count(batch_id: int):
    """Get the number of problems for a specific batch."""
    try:
        return batch_service.get_problems_count(batch_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get problems count: {str(e)}")

@router.put("/{batch_id}/cost")
def update_batch_cost(batch_id: int, cost: float):
    """Update the cost for a batch."""
    try:
        batch = batch_service.update_batch_cost(batch_id, cost)
        if batch is None:
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update batch cost: {str(e)}")

@router.put("/{batch_id}/target-model")
def update_batch_target_model(batch_id: int, target_model: dict):
    """Update the target model configuration for a batch."""
    try:
        batch = batch_service.update_batch_target_model(batch_id, target_model)
        if batch is None:
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update target model: {str(e)}") 