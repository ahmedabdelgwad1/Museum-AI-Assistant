"""Application configuration using pydantic-settings."""

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Groq API — supports comma-separated list for rotation on rate-limit
    groq_api_key: str = Field(..., env="GROQ_API_KEY")

    @property
    def groq_api_keys(self) -> list[str]:
        """Return a list of all configured Groq API keys."""
        return [k.strip() for k in self.groq_api_key.split(",") if k.strip()]

    # Supabase
    supabase_url: str = Field(default="https://fyeoccqyylbomsmwjwxh.supabase.co", env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    supabase_table: str = Field(default="museum_artifacts", env="SUPABASE_TABLE")
    supabase_function: str = Field(default="match_artifacts", env="SUPABASE_FUNCTION")

    # Data paths
    csv_data_path: str = Field(default="./data/bibalex_full_museum_data.csv", env="CSV_DATA_PATH")

    # Embedding model
    embedding_model: str = Field(
        default="intfloat/multilingual-e5-base",
        env="EMBEDDING_MODEL",
    )

    # Corrective RAG configuration
    top_k_results: int = Field(default=3, env="TOP_K_RESULTS")
    max_rewrite_attempts: int = Field(default=2, env="MAX_REWRITE_ATTEMPTS")
    relevance_threshold: float = Field(default=0.3, env="RELEVANCE_THRESHOLD")

    # LLM model
    llm_model: str = Field(default="llama-3.3-70b-versatile", env="LLM_MODEL")

    # STT model
    stt_model: str = Field(default="whisper-large-v3", env="STT_MODEL")

    # API server
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # Daily.co API Key
    daily_api_key: str = Field(default="", env="DAILY_API_KEY")

    # CORS origins
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton settings instance
settings = Settings()
