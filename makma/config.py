from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MAKMA_", env_file=".env", extra="ignore")
    data_dir: Path = Path("data")
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = "qwen3:4b-q4_K_M"
    provider: str = "ollama"
    openai_url: str = "http://127.0.0.1:8001/v1"
    api_key: str = ""
    remote_models: bool = False
    external_research: bool = False
    concurrency: int = Field(default=1, ge=1, le=6)
    context_length: int = Field(default=4096, ge=2048, le=32768)
    max_output_tokens: int = Field(default=1200, ge=128, le=4096)
    token_budget: int = Field(default=24000, ge=4096)
    sandbox_image: str = "makma-sandbox:0.1"
    sandbox_timeout: int = Field(default=45, ge=5, le=300)
    scheduler_interval: float = 0.5
    memory_weights: tuple[float, float, float, float, float] = (.35, .20, .20, .15, .10)

