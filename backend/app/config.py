from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)

    # App
    APP_NAME: str = "Siru HealthHub FHIR API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "debug", "dev", "development")
        return bool(v)
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fhir_user:fhir_pass@postgres:5432/fhir_db"
    
    # Security & Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://localhost"]
    
    # FHIR
    FHIR_BASE_URL: str = "http://localhost:8000/fhir"
    FHIR_VERSION: str = "4.0.1"

settings = Settings()

