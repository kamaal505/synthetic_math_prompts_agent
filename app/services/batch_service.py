from sqlalchemy.orm import Session
from app.models.models import Batch
from app.models.schemas import BatchCreate
from typing import List, Optional

def create_batch(db: Session, batch: BatchCreate) -> Batch:
    db_batch = Batch(**batch.dict())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_batch(db: Session, batch_id: int) -> Optional[Batch]:
    return db.query(Batch).filter(Batch.id == batch_id).first()

def get_batches(db: Session, skip: int = 0, limit: int = 100) -> List[Batch]:
    return db.query(Batch).offset(skip).limit(limit).all()

def delete_batch(db: Session, batch_id: int) -> bool:
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if batch:
        db.delete(batch)
        db.commit()
        return True
    return False

def update_batch_cost(db: Session, batch_id: int, cost: float) -> Optional[Batch]:
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if batch:
        batch.batch_cost = cost
        db.commit()
        db.refresh(batch)
    return batch 