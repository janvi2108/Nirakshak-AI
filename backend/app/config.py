from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://nirakshak:nirakshak123@postgres:5432/nirakshak_db"
    postgres_user: str = "nirakshak"
    postgres_password: str = "nirakshak123"
    postgres_db: str = "nirakshak_db"
    redis_url: str = "redis://redis:6379/0"
    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin123"
    s3_bucket_name: str = "nirakshak-docs"
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    mlflow_tracking_uri: str = "http://mlflow:5000"
    openai_api_key: str = ""
    groq_api_key: str = ""
    groq_api_url: str = ""  # set to your Groq API endpoint, e.g. https://api.groq.example/v1/chat
    ml_artifacts_path: str = "/ml/artifacts"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
