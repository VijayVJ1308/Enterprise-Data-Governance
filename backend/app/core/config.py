import os

try:
    # pyrefly: ignore [missing-import]
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        # pyrefly: ignore [missing-import]
        from pydantic import BaseSettings
    except ImportError:
        class BaseSettings:
            pass


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Data Quality & Data Governance Platform"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-32-chars-minimum-length-change-in-prod")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres_password_dev")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "enterprise_governance_db")

    @property
    def DATABASE_URL(self) -> str:
        override_url = os.getenv("DATABASE_URL")
        if override_url:
            return override_url
        # Fall back to SQLite if PostgreSQL driver is not installed or in local dev/test environment
        try:
            import psycopg2
            return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        except ImportError:
            return "sqlite:///./dev_governance.db"


settings = Settings()
