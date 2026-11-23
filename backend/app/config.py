from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TechInterview API"
    google_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    data_dir: Path = PROJECT_ROOT / "backend" / "data"
    document_manifest: Path = PROJECT_ROOT / "backend" / "documents.json"
    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "floor-supervisor"
    trace_content: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
