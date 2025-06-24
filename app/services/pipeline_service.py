from app.models.schemas import GenerationRequest
from core.runner import run_pipeline_from_config

def run_pipeline(request: GenerationRequest):
    config = {
        "num_problems": request.num_problems,
        "engineer_model": request.engineer_model.dict(),
        "checker_model": request.checker_model.dict(),
        "target_model": request.target_model.dict(),
        "taxonomy": request.taxonomy
    }
    return run_pipeline_from_config(config)

