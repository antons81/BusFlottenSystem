from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    # AI Provider
    ai_provider: Literal["claude", "ollama"] = Field(
        default="ollama",
        description="AI-Anbieter: 'claude' oder 'ollama'"
    )
    ollama_model: str = Field(
        default="llama3.1",
        description="Ollama-Modell (z.B. llama3.1, mistral)"
    )
    ollama_url: str = Field(
        default="http://ollama:11434",
        description="Ollama API URL"
    )

    # Claude
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")

    # DB
    postgres_user: str = Field(default="")
    postgres_password: str = Field(default="")
    postgres_db: str = Field(default="")

    # Vault
    vault_token: str = Field(default="")

    # SMTP
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    report_email_to: str = Field(default="")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()