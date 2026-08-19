"""
Ortam değişkenlerinden (env) okunan merkezi ayarlar.
Yerelde .env dosyası, Docker'da docker-compose environment bloğu kullanılır.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Genel
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Veritabanı (PostgreSQL + pgvector)
    database_url: str = "postgresql+psycopg://bdte:bdte@localhost:5432/bdte"

    # LLM (Ollama — self-hosted, açık kaynak)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # TTS (Coqui TTS servis adresi — ayrı bir konteynerde çalışır)
    tts_base_url: str = "http://localhost:5002"

    # Embedding modeli (sentence-transformers, çok dilli TR/EN)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
