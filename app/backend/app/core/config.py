"""Application configuration via environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "app API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = "app"
    POSTGRES_DB: str = "app"
    # True by default. Set POSTGRES_SSL=false for local Postgres without TLS.
    POSTGRES_SSL: bool = True

    CORS_ORIGINS: list[str] = ["http://localhost:3001"]

    KEYCLOAK_ISSUER_URL: str = "https://dev.loginproxy.gov.bc.ca/auth/realms/standard"
    KEYCLOAK_CLIENT_ID: str = "conn-hub-6434"
    SESSION_COOKIE_NAME: str = "telecom_session"
    SESSION_SECRET: str = "change-me-change-me-change-me-change-me"

    @property
    def database_url(self) -> str:
        base = (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        if self.POSTGRES_SSL:
            return f"{base}?sslmode=require"
        return base


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
