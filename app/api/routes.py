from fastapi import APIRouter, Depends
from app.models.schemas import GenerationRequest, GenerationResponse
from app.services.pipeline_service import run_pipeline
from . import batches, problems, generation
from utils.google_auth import verify_company_email

router = APIRouter()

@router.post("/generate", response_model=GenerationResponse)
def generate_prompts(request: GenerationRequest):
    return run_pipeline(request)

# Include new routers
router.include_router(batches.router, prefix="/batches", tags=["batches"], dependencies=[Depends(verify_company_email)])
router.include_router(problems.router, prefix="/problems", tags=["problems"], dependencies=[Depends(verify_company_email)])
router.include_router(generation.router, prefix="/generation", tags=["generation"], dependencies=[Depends(verify_company_email)])
