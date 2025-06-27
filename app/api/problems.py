from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.schemas import ProblemResponse
from app.services.problem_service import get_problems, get_problem, get_problems_by_batch

router = APIRouter()

@router.get("/", response_model=List[ProblemResponse])
def get_all_problems(
    batch_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0, description="Number of problems to skip"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of problems to return"),
    db: Session = Depends(get_db)
):
    problems = get_problems(db, skip=skip, limit=limit, batch_id=batch_id, status=status)
    return problems

@router.get("/problem/{problem_id}", response_model=ProblemResponse)
def get_problem_by_id(problem_id: int, db: Session = Depends(get_db)):
    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@router.get("/batch/{batch_id}/problems", response_model=List[ProblemResponse])
def get_problems_from_batch(batch_id: int, db: Session = Depends(get_db)):
    problems = get_problems_by_batch(db, batch_id)
    return problems

@router.get("/all", response_model=List[ProblemResponse])
def get_all_problems_unlimited(
    batch_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all problems without any limit - use with caution for large datasets"""
    # Use a very high limit to effectively get all problems
    problems = get_problems(db, skip=0, limit=100000, batch_id=batch_id, status=status)
    return problems 