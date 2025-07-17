from fastapi import APIRouter
from app.api import batches, problems, generation

router = APIRouter()

router.include_router(batches.router, prefix="/batches", tags=["batches"])
router.include_router(problems.router, prefix="/problems", tags=["problems"])
router.include_router(generation.router, prefix="/generation", tags=["generation"])

@router.get("/")
def read_root():
    return {"message": "Math Agent API is running"}

@router.get("/health")
def health_check():
    return {"status": "healthy"}
