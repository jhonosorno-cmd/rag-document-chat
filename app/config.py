from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "groq"
    groq_api_key: str = ""
    anthropic_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_model: str = "claude-sonnet-4-5"
    embedding_model: str = "intfloat/multilingual-e5-base"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_results: int = 6
    documents_dir: str = "./data/documents"
    chroma_path: str = "./storage/chroma"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
