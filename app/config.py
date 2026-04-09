# config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    ai_provider: Literal["claude", "ollama"] = Field(default="ollama")

    ollama_model: str = Field(default="qwen2.5:3b")
    ollama_url: str = Field(default="http://ollama:11434")

    # Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Database
    postgres_user: str = Field(default="")
    postgres_password: str = Field(default="")
    postgres_db: str = Field(default="")

    vault_token: str = Field(default="")

    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    report_email_to: str = Field(default="")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()