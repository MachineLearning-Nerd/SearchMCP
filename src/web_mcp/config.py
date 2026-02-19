from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SEARXNG_URL: str = Field(default="http://localhost:8080", description="SearxNG server URL")
    SEARXNG_TIMEOUT: int = Field(default=10, description="Request timeout in seconds")
    FALLBACK_ENABLED: bool = Field(default=True, description="Enable Google scraping fallback")
    RATE_LIMIT_REQUESTS: int = Field(default=30, description="Max requests per period")
    RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit period in seconds")
    MAX_CONTENT_LENGTH: int = Field(default=10000, description="Max characters in fetched content")
    DEFAULT_SEARCH_LIMIT: int = Field(default=5, description="Default number of search results")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    JSON_LOGS: bool = Field(default=False, description="Output logs in JSON format")


settings = Settings()
