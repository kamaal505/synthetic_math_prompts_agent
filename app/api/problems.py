from fastapi import APIRouter, HTTPException
from app.models.schemas import ProblemCreate, Problem
from app.services import problem_service
from typing import List, Optional

router = APIRouter()

@router.post("/", response_model=Problem)
def create_problem(problem: ProblemCreate):
    """Create a new problem."""
    try:
        return problem_service.create_problem(problem)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create problem: {str(e)}")

@router.get("/", response_model=List[Problem])
def get_problems(skip: int = 0, limit: int = 1000, 
                batch_id: Optional[int] = None, status: Optional[str] = None):
    """Get problems with filtering and pagination."""
    try:
        return problem_service.get_problems(skip=skip, limit=limit, 
                                          batch_id=batch_id, status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get problems: {str(e)}")

@router.get("/{problem_id}", response_model=Problem)
def get_problem(problem_id: int):
    """Get a specific problem by ID."""
    try:
        problem = problem_service.get_problem(problem_id)
        if problem is None:
            raise HTTPException(status_code=404, detail="Problem not found")
        return problem
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get problem: {str(e)}")

@router.get("/problem/{problem_id}", response_model=Problem)
def get_problem_detail(problem_id: int):
    """Get a specific problem by ID with 'problem' in the path."""
    try:
        problem = problem_service.get_problem(problem_id)
        if problem is None:
            raise HTTPException(status_code=404, detail="Problem not found")
        return problem
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get problem: {str(e)}")

@router.get("/batch/{batch_id}", response_model=List[Problem])
def get_problems_by_batch(batch_id: int):
    """Get all problems for a specific batch."""
    try:
        return problem_service.get_problems_by_batch(batch_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch problems: {str(e)}")

@router.get("/batch/{batch_id}/stats")
def get_batch_problem_stats(batch_id: int):
    """Get problem statistics for a specific batch."""
    try:
        return problem_service.get_problem_stats(batch_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get problem stats: {str(e)}") 