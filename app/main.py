import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.exc import register_exception_handlers
from app.middleware.logging import log_requests
from app.routers.area import router as area_router
from app.routers.auth import router as auth_router
from app.routers.pallet import router as pallet_router
from app.routers.report import router as report_router
from app.routers.supplier import router as supplier_router
from app.routers.transaction import router as transaction_router
from app.routers.unit import router as unit_router
from app.routers.users import router as users_router

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started")
    yield
    logger.info("Application stopped")


app = FastAPI(
    title=settings.app.PROJECT_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(log_requests)

register_exception_handlers(app)


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
app.include_router(users_router)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


@app.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/admin")
async def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html")


@app.get("/stock")
async def stock_page(request: Request):
    return templates.TemplateResponse(request, "stock.html")


@app.get("/change-password")
async def change_password_page(request: Request):
    return templates.TemplateResponse(request, "change_password.html")
