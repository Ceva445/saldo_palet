from app.core.config.app import AppConfig
from app.core.config.auth import AuthConfig
from app.core.config.db import DbBaseConfig
from app.core.config.base import BaseConfig


class Settings(BaseConfig):
    app: AppConfig = AppConfig()
    db: DbBaseConfig = DbBaseConfig()
    auth: AuthConfig = AuthConfig()


settings = Settings()