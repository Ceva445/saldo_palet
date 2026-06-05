from pydantic import Field

from app.core.config.base import BaseConfig


class DbBaseConfig(BaseConfig):
    DATABASE_URL: str = Field(
        ...,
        alias="DATABASE_URL",
    )

    @property
    def url(self) -> str:
        url = self.DATABASE_URL

        url = url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
        )

        url = url.replace(
            "?sslmode=require&channel_binding=require",
            "",
        )

        url = url.replace(
            "?sslmode=require",
            "",
        )

        return url