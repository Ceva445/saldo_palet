# Configuration module
from app.core.config.app import AppConfig
from app.core.config.auth import AuthConfig
from app.core.config.db import DbConfig
from app.core.config.base import BaseConfig


class Settings(BaseConfig):
    app: AppConfig = AppConfig()
    db: DbConfig = DbConfig()
    auth: AuthConfig = AuthConfig()


settings = Settings()