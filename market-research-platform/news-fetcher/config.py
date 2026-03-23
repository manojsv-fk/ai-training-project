# filepath: market-research-platform/news-fetcher/config.py
# Application configuration using Pydantic Settings.
# All values are read from environment variables (or .env file).

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # -- LLM Provider ("groq", "gemini", or "openai") ----------------------
    llm_provider: str = "gemini"

    # -- Embedding Provider ("huggingface", "gemini", or "openai") --------
    embedding_provider: str = "huggingface"
    huggingface_embedding_model: str = "all-MiniLM-L12-v2"

    # -- Gemini -------------------------------------------------------------
    gemini_api_key: str = ""
    gemini_llm_model: str = "models/gemini-2.0-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"

    # -- Groq ---------------------------------------------------------------
    groq_api_key: str = ""
    groq_llm_model: str = "llama-3.3-70b-versatile"

    # -- OpenAI -------------------------------------------------------------
    openai_api_key: str = ""
    openai_llm_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # -- PostgreSQL (shared with main backend) ------------------------------
    postgres_user: str = "mrip"
    postgres_password: str = "mrip_secret"
    postgres_db: str = "market_research"
    postgres_host: str = "db"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Sync URL used by LlamaIndex PGVectorStore initialization."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # -- News fetching ------------------------------------------------------
    news_fetch_interval_minutes: int = 30
    news_categories: str = "markets,industry,tech,economy"
    et_base_url: str = "https://economictimes.indiatimes.com"

    # -- LlamaIndex chunking ------------------------------------------------
    chunk_size: int = 512
    chunk_overlap: int = 128

    # -- App ----------------------------------------------------------------
    log_level: str = "INFO"


# Singleton settings instance
settings = Settings()
