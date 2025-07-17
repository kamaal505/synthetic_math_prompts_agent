import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings

app = FastAPI(
    title="Math Agent API",
    description="API for generating synthetic math problems",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main router
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("Math Agent API starting up...")
    print(f"Using BigQuery for data storage")
    print(f"Project: {settings.get('bigquery', {}).get('project_id', 'turing-gpt')}")
    print(f"Dataset: {settings.get('bigquery', {}).get('dataset_id', 'math_agent_dataset')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    print("Math Agent API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
