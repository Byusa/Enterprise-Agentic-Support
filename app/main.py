from fastapi import FastAPI

from app.database import Base, engine
from app import models

app = FastAPI(
    title="Vrize Agentic Support",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": "configured",
    }