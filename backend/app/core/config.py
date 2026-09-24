from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central app configuration, loaded from environment variables / .env.

    Using pydantic-settings here means every setting is type-checked at
    startup -- if JWT_SECRET is missing or ACCESS_TOKEN_EXPIRE_MINUTES is not
    a number, the app fails fast with a clear error instead of crashing
    later on some random request. This is a common FastAPI pattern worth
    understanding well for your viva.
    """

    app_name: str = "DevPulse API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # MySQL connection string, e.g.
    # mysql+pymysql://devpulse:devpulse@localhost:3306/devpulse
    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    github_api_url: str = "https://api.github.com"
    github_token: str | None = None

    # Minimum number of seconds a user must wait between two /github/sync
    # calls. This is a deliberately simple, in-database rate limit (no
    # Redis needed) that protects both GitHub's API quota and your own DB.
    sync_cooldown_seconds: int = 120

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"

    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
