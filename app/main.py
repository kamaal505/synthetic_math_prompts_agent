from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Synthetic Prompt API")
app.include_router(router)
