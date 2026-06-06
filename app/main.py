# Placeholder for main FastAPI application entry point
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.logging import log_requests

from app.routers.auth import router as auth_router
from app.routers.area import router as area_router
from app.routers.pallet import router as pallet_router
from app.routers.supplier import router as supplier_router
from app.routers.transaction import router as transaction_router
from app.routers.unit import router as unit_router
from app.routers.report import router as report_router


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

app.middleware("http")(log_requests)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(area_router)
app.include_router(supplier_router)
app.include_router(unit_router)
app.include_router(pallet_router)
app.include_router(transaction_router)
app.include_router(report_router)
