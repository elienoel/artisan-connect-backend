from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Artisan Connect API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg2://artisan:artisan@postgres:5432/artisan_connect"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "artisan"
    MINIO_SECRET_KEY: str = "artisan123"
    MINIO_BUCKET: str = "artisan-connect"
    MINIO_SECURE: bool = False
    MINIO_PUBLIC_URL: str = "http://localhost:9000"

    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()
