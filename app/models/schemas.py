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
    reference: Optional[str] = None
    hints_were_corrected: Optional[bool] = False
    target_model_answer: Optional[Any] = None


class GenerationResponse(BaseModel):
    valid_prompts: List[Prompt]
    discarded_prompts: List[Any]
    metadata: Dict[str, Any]

class GenerationStatus(BaseModel):
    batch_id: int
    total_needed: int
    valid_generated: int
    total_generated: int
    progress_percentage: float
    stats: Dict[str, int]
    batch_cost: float
    status: str

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
    reference: Optional[str] = None

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
    reference: Optional[str]

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
    reference: Optional[str]


    class Config:
        from_attributes = True

class GenerationRequest(BaseModel):
    num_problems: int
    engineer_model: ModelConfig
    checker_model: ModelConfig
    target_model: ModelConfig
    taxonomy: Optional[Dict[str, Any]] = None
    use_seed_data: Optional[bool] = False
    benchmark_name: Optional[str] = None
    seed_data: Optional[List[Dict[str, Any]]] = None
    use_search: bool = True

    @classmethod
    def validate_request(cls, values):
        use_seed = values.get("use_seed_data", False)
        taxonomy = values.get("taxonomy")
        benchmark = values.get("benchmark_name")
        seed_data = values.get("seed_data")

        if not use_seed and not taxonomy:
            raise ValueError("Must provide either taxonomy or seed_data.")

        if use_seed and not (benchmark or seed_data):
            raise ValueError("Must provide either benchmark_name or seed_data when use_seed_data is True.")

        return values

    class Config:
        extra = "forbid"
        schema_extra = {
            "example": {
                "num_problems": 5,
                "engineer_model": {"provider": "gemini", "model_name": "gemini-2.5-pro"},
                "checker_model": {"provider": "openai", "model_name": "o3"},
                "target_model": {"provider": "openai", "model_name": "o3"},
                "use_seed_data": True,
                "benchmark_name": "AIME",
                "use_search": True
            }
        }

    # Attach custom validation
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_request

class PipelineConfig(BaseModel):
    generator: Dict[str, str]
    hinter: Dict[str, str]
    checker: Dict[str, str]
    target: Dict[str, str]
    judge: Dict[str, str]

class TargetModelUpdate(BaseModel):
    target_model: ModelConfig
