from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class OpenSearchSettings(BaseSettings):
    host: str
    port: int
    user: str = ""
    password: SecretStr = SecretStr("")


class OllamaSettings(BaseSettings):
    host: str


class OAuthSettings(BaseSettings):
    auth_url: str
    token_url: str
    redirect_uri: str
    client_id: str
    client_secret: str

class PostgresSettings(BaseSettings):
    db: str
    host: str
    port: int
    user: str = ""
    password: SecretStr = SecretStr("")

class Settings(BaseSettings):
    ollama: OllamaSettings
    opensearch: OpenSearchSettings
    oauth: OAuthSettings
    db: PostgresSettings

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


@lru_cache
def get_settings():
    return Settings()


if __name__ == "__main__":
    print(get_settings().model_dump())
