from app.services.bigquery_service import bigquery_service
from app.models.schemas import BatchCreate
from typing import List, Optional

def create_batch(batch) -> dict:
    """Create a new batch using BigQuery."""
    if isinstance(batch, dict):
        batch_data = batch
    else:
        batch_data = batch.dict()
    return bigquery_service.create_batch(batch_data)

def get_batch(batch_id: int) -> Optional[dict]:
    """Get a batch by ID using BigQuery."""
    return bigquery_service.get_batch(batch_id)

def get_batches(skip: int = 0, limit: int = 100) -> List[dict]:
    """Get all batches with pagination using BigQuery."""
    return bigquery_service.get_batches(skip=skip, limit=limit)

def delete_batch(batch_id: int) -> bool:
    """Delete a batch using BigQuery."""
    return bigquery_service.delete_batch(batch_id)

def update_batch_cost(batch_id: int, cost: float) -> Optional[dict]:
    """Update batch cost using BigQuery."""
    success = bigquery_service.update_batch_cost(batch_id, cost)
    if success:
        return bigquery_service.get_batch(batch_id)
    return None

def update_batch_target_model(batch_id: int, target_model: dict) -> Optional[dict]:
    """Update the target model configuration for a batch using BigQuery."""
    # Get current batch
    batch = bigquery_service.get_batch(batch_id)
    if not batch:
        return None
    
    # Update the pipeline with new target model
    pipeline = batch.get("pipeline", {})
    pipeline['target_model'] = target_model
    
    # Update the batch (we'll need to implement this method)
    # For now, return the updated batch data
    batch["pipeline"] = pipeline
    return batch

def get_problems_count(batch_id: Optional[int] = None) -> dict:
    """Get the number of problems using BigQuery."""
    return bigquery_service.get_problems_count(batch_id) 