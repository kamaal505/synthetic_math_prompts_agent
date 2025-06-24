from pydantic import BaseModel
from typing import Dict, Optional, Any, List


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
