from pydantic import Field

from app.core.config.base import BaseConfig


class AppConfig(BaseConfig):
    PROJECT_NAME: str = "Pallet Logistics System"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    # Same-origin by default (frontend is served by this app).
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]