from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    OWNER_EMAIL: str = "founder@example.com"
    OWNER_PASSWORD: str = "changeme123"
    JWT_SECRET: str = "dev_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24h

    DATABASE_URL: str = "postgresql+asyncpg://wavy:wavy@db:5432/wavyos"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:4200"

    # Web Intelligence
    SERPER_API_KEY: Optional[str] = None
    ENABLE_WEB_INTELLIGENCE: bool = True
    SCAN_COOLDOWN_HOURS: int = 1
    MAX_NEWS_RESULTS: int = 20
    WEBSITE_SCRAPE_ENABLED: bool = True
    JSE_DATA_ENABLED: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
