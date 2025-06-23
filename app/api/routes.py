from fastapi import APIRouter
from app.models.schemas import GenerationRequest, GenerationResponse
from app.services.pipeline_service import run_pipeline

router = APIRouter()

@router.post("/generate", response_model=GenerationResponse)
def generate_prompts(request: GenerationRequest):
    return run_pipeline(request)
