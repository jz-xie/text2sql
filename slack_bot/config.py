from pydantic_settings import BaseSettings

import logging

# Set the logging level to INFO
logging.basicConfig(level=logging.INFO)


class Settings(BaseSettings):
    slack_bot_token: str
    slack_app_token: str

    class Config:
        env_file = ".env"


settings = Settings()
