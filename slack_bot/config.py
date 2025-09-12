from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

import logging

# Set the logging level to INFO
logging.basicConfig(level=logging.INFO)


class OpenAI(BaseSettings):
    azure_endpoint: str
    azure_deployment: str = "your-azure-deployment"
    api_key: str
    api_version: str = "2024-02-15"


class Settings(BaseSettings):
    slack_bot_token: str
    slack_app_token: str

    openai: Optional[OpenAI] = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
