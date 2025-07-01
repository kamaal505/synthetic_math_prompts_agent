from pydantic import BaseModel
from typing import Dict, Optional, Any, List
from datetime import datetime
from decimal import Decimal


class ModelConfig(BaseModel):
    provider: str
    model_name: str


class Prompt(BaseModel):
    subject: str
    topic: str
    problem: str
    answer: str
    hints: Dict[str, str]
    hints_were_corrected: Optional[bool] = False
    target_model_answer: Optional[Any] = None


class GenerationRequest(BaseModel):
    num_problems: int
    engineer_model: ModelConfig
    checker_model: ModelConfig
    target_model: ModelConfig
    taxonomy: Dict[str, List[str]]

    class Config:
        schema_extra = {
            "example": {
                "num_problems": 1,
                "engineer_model": {
                    "provider": "gemini",
                    "model_name": "gemini-2.5-pro"
                },
                "checker_model": {
                    "provider": "openai",
                    "model_name": "o3-mini"
                },
                "target_model": {
                    "provider": "openai",
                    "model_name": "o1"
                },
                "taxonomy": {
                    "Algebra": ["Linear Equations", "Quadratic Functions"],
                    "Complex Analysis": ["Contour Integration"]
                }
            }
        }

class GenerationResponse(BaseModel):
    valid_prompts: List[Prompt]
    discarded_prompts: List[Any]
    metadata: Dict[str, Any]


class BatchBase(BaseModel):
    name: str
    taxonomy_json: Dict[str, Any]
    pipeline: Dict[str, Any]
    num_problems: int

class BatchCreate(BatchBase):
    batch_cost: Optional[Decimal] = 0.00

class Batch(BatchBase):
    id: int
    batch_cost: Decimal
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class BatchWithStats(Batch):
    stats: Dict[str, int]

class ProblemBase(BaseModel):
    subject: str
    topic: str
    question: str
    answer: str
    hints: Dict[str, Any]
    status: str

class ProblemCreate(ProblemBase):
    batch_id: int
    rejection_reason: Optional[str] = None
    problem_embedding: Optional[Dict[str, Any]] = None
    similar_problems: Dict[str, Any] = {}
    cost: Decimal = 0.00
    target_model_answer: Optional[str] = None
    hints_were_corrected: bool = False

class Problem(ProblemBase):
    id: int
    batch_id: int
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    problem_embedding: Optional[Dict[str, Any]]
    similar_problems: Dict[str, Any]
    cost: Decimal
    target_model_answer: Optional[str]
    hints_were_corrected: bool

    class Config:
        from_attributes = True

class ProblemResponse(ProblemBase):
    id: int
    batch_id: int
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    similar_problems: Dict[str, Any]
    cost: Decimal
    target_model_answer: Optional[str]
    hints_were_corrected: bool

    class Config:
        from_attributes = True

class GenerationStatus(BaseModel):
    batch_id: int
    total_needed: int
    valid_generated: int
    total_generated: int
    progress_percentage: float
    stats: Dict[str, int]
    batch_cost: float
    status: str

class PipelineConfig(BaseModel):
    generator: Dict[str, str]
    hinter: Dict[str, str]
    checker: Dict[str, str]
    target: Dict[str, str]
    judge: Dict[str, str]

class TargetModelUpdate(BaseModel):
    target_model: ModelConfig
