from typing import Any, Literal

from pydantic import SecretStr, model_validator
from pydantic_core import PydanticCustomError
from pydantic_settings import BaseSettings, SettingsConfigDict

from text2sql.backend.aws_utils import get_secretsmanager_password


class OpenSearchSettings(BaseSettings):
    host: str
    port: str = "9200"
    user: str = ""
    password: SecretStr = SecretStr("")


class AzureOpenAISettings(BaseSettings):
    endpoint: str
    api_key: SecretStr
    api_version: str = "2024-10-21"
    deployment_chat: str
    deployment_embedding: str


class OAuthSettings(BaseSettings):
    auth_url: str = ""
    token_url: str =""
    client_id: str
    client_secret: SecretStr
    redirect_uri: str

class OllamaSettings(BaseSettings):
    host:str

class PostgresSettings(BaseSettings):
    db: str
    user: str
    password: SecretStr
    host: str
    port: str = "5432"
    aws_secretsmanager_secret_id: str = ""

    @model_validator(mode="before")
    def handle_password_missing(self: dict) -> Any:
        if "password" not in self:
            if "aws_secretsmanager_secret_id" in self:
                self["password"] = get_secretsmanager_password(
                    self["aws_secretsmanager_secret_id"]
                )
            else:
                raise PydanticCustomError(
                    "Postgres Authentication Error",
                    "In the absence of <password>, <aws_secretsmanager_secret_id> must be provided!",
                )

        return self


class Settings(BaseSettings):
    azure_openai: AzureOpenAISettings
    opensearch: OpenSearchSettings
    oauth: OAuthSettings
    postgres: PostgresSettings
    ollama: OllamaSettings

    env: Literal["local", "dev", "stg", "prod"] = "local"

    model_config = SettingsConfigDict(
        env_file=(".env", "/vault/secrets/creds"),
        env_nested_delimiter="__",
        extra="allow",
    )

settings = Settings()

if __name__ == "__main__":
    settings = Settings()
    print(settings.model_dump())
