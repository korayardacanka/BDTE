"""
Centralized settings read from environment variables.
Uses a local .env file in development, docker-compose environment blocks in
production-like deployments.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Database — currently SQLite (see the note in app/database.py).
    # If real RAG/pgvector is needed later, just point this at a
    # PostgreSQL address, e.g.:
    # "postgresql+psycopg://bdte:bdte@localhost:5432/bdte"
    database_url: str = "sqlite:///./bdte.db"

    # LLM (Ollama — self-hosted, open source)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # TTS (Coqui TTS service address — used directly in-process here)
    tts_base_url: str = "http://localhost:5002"

    # Embedding model (sentence-transformers, multilingual)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
