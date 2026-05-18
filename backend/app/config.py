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

    # ChromaDB
    chroma_persist_dir: str = Field(default="./data/chroma_db", env="CHROMA_PERSIST_DIR")

    # Data paths
    csv_data_path: str = Field(default="./data/bibalex_full_museum_data.csv", env="CSV_DATA_PATH")

    # Embedding model
    embedding_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        env="EMBEDDING_MODEL",
    )

    # Corrective RAG configuration
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    max_rewrite_attempts: int = Field(default=2, env="MAX_REWRITE_ATTEMPTS")
    relevance_threshold: float = Field(default=0.3, env="RELEVANCE_THRESHOLD")

    # LLM model
    llm_model: str = Field(default="llama-3.3-70b-versatile", env="LLM_MODEL")

    # STT model
    stt_model: str = Field(default="whisper-large-v3", env="STT_MODEL")

    # API server
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # CORS origins
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")

    # ChromaDB collection name
    chroma_collection_name: str = Field(default="bibalex_artifacts", env="CHROMA_COLLECTION_NAME")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton settings instance
settings = Settings()
