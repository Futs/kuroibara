from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Application
    APP_NAME: str = "Kuroibara"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_URL: str = "http://localhost:8000"
    SECRET_KEY: str
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    # Database
    DATABASE_URL: Optional[str] = None  # Direct database URL (takes precedence)
    DB_CONNECTION: str = "postgresql+asyncpg"
    DB_HOST: str = "postgres"
    DB_PORT: str = "5432"
    DB_DATABASE: str = "kuroibara"
    DB_USERNAME: str = "kuroibara"
    DB_PASSWORD: str = "password"

    @property
    def DATABASE_URI(self) -> str:
        """Construct database URI from individual components or use direct URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"{self.DB_CONNECTION}://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"

    # Valkey (Redis)
    VALKEY_HOST: str = "valkey"
    VALKEY_PORT: int = 6379
    VALKEY_PASSWORD: Optional[str] = None
    VALKEY_DB: int = 0

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "/app/storage"
    MAX_UPLOAD_SIZE: str = "100MB"

    # Email
    MAIL_MAILER: str = "smtp"
    MAIL_HOST: str = "mailhog"
    MAIL_PORT: int = 1025
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_ENCRYPTION: Optional[str] = None
    MAIL_FROM_ADDRESS: str = "noreply@kuroibara.app"
    MAIL_FROM_NAME: str = "Kuroibara"

    # 2FA
    TWO_FA_ISSUER: str = "Kuroibara"

    # Provider monitoring
    ENABLE_PROVIDER_MONITORING: bool = True

    # Database initialization
    ENABLE_DB_INIT: bool = True


settings = Settings()
