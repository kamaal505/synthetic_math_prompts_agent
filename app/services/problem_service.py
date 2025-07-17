from app.services.bigquery_service import bigquery_service
from app.models.schemas import ProblemCreate
from typing import List, Optional

def create_problem(problem) -> dict:
    """Create a new problem using BigQuery."""
    if isinstance(problem, dict):
        problem_data = problem
    else:
        problem_data = problem.dict()
    return bigquery_service.create_problem(problem_data)

def get_problem(problem_id: int) -> Optional[dict]:
    """Get a problem by ID using BigQuery."""
    return bigquery_service.get_problem(problem_id)

def get_problems(skip: int = 0, limit: int = 1000, 
                batch_id: Optional[int] = None, status: Optional[str] = None) -> List[dict]:
    """Get problems with filtering and pagination using BigQuery."""
    return bigquery_service.get_problems(skip=skip, limit=limit, 
                                       batch_id=batch_id, status=status)

def get_problems_by_batch(batch_id: int) -> List[dict]:
    """Get all problems for a specific batch using BigQuery."""
    return bigquery_service.get_problems_by_batch(batch_id)

def get_problem_stats(batch_id: int) -> dict:
    """Get problem statistics for a batch using BigQuery."""
    return bigquery_service.get_problem_stats(batch_id)

def delete_problems_by_batch(batch_id: int) -> bool:
    """Delete all problems for a specific batch using BigQuery."""
    return bigquery_service.delete_problems_by_batch(batch_id) 