from sqlalchemy.orm import Session
from app.models.models import Problem
from app.models.schemas import ProblemCreate
from typing import List, Optional

def create_problem(db: Session, problem: ProblemCreate) -> Problem:
    db_problem = Problem(**problem.dict())
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem

def get_problem(db: Session, problem_id: int) -> Optional[Problem]:
    return db.query(Problem).filter(Problem.id == problem_id).first()

def get_problems(
    db: Session, 
    skip: int = 0, 
    limit: int = 1000,
    batch_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[Problem]:
    query = db.query(Problem)
    
    if batch_id:
        query = query.filter(Problem.batch_id == batch_id)
    if status:
        query = query.filter(Problem.status == status)
    
    return query.offset(skip).limit(limit).all()

def get_problems_by_batch(db: Session, batch_id: int) -> List[Problem]:
    return db.query(Problem).filter(Problem.batch_id == batch_id).all()

def get_problem_stats(db: Session, batch_id: int) -> dict:
    stats = {
        'discarded': db.query(Problem).filter(
            Problem.batch_id == batch_id, 
            Problem.status == 'discarded'
        ).count(),
        'valid': db.query(Problem).filter(
            Problem.batch_id == batch_id, 
            Problem.status == 'valid'
        ).count()
    }
    return stats 