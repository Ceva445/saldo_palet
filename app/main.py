# Placeholder for main FastAPI application entry point
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application started")
    yield
    print("Application stopped")


app = FastAPI(
    title=settings.app.PROJECT_NAME,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}