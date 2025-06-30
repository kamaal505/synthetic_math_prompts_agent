import os

from fastapi import FastAPI

from app.api.routes import router

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
app = FastAPI(title="Synthetic Prompt API")
app.include_router(router)
