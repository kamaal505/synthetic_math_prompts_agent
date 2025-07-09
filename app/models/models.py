from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    taxonomy_json = Column(JSON)
    pipeline = Column(JSON)
    num_problems = Column(Integer)
    batch_cost = Column(Numeric(12, 6), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    problems = relationship("Problem", back_populates="batch")

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(100))
    topic = Column(String(100))
    question = Column(Text)
    answer = Column(Text)
    hints = Column(JSON)
    rejection_reason = Column(Text, nullable=True)
    status = Column(String(20))  # 'discarded', 'solved', 'valid'
    batch_id = Column(Integer, ForeignKey("batches.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    problem_embedding = Column(JSON, nullable=True)
    similar_problems = Column(JSON, default={})
    cost = Column(Numeric(10, 6), default=0.00)
    target_model_answer = Column(Text, nullable=True)
    hints_were_corrected = Column(Integer, default=0)  # 0 = false, 1 = true
    reference = Column(String(255), nullable=True)

    batch = relationship("Batch", back_populates="problems") 