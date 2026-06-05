from pydantic import Field

from app.core.config.base import BaseConfig


class AppConfig(BaseConfig):
    PROJECT_NAME: str = "Pallet Logistics System"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False