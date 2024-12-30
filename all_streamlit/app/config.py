from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class OpenSearchSettings(BaseSettings):
    host:str
    port:int
    user:str
    password: SecretStr

class OllamaSettings(BaseSettings):
    host:str

class OAuthSettings(BaseSettings):
    client_id:str
    client_secret:str
    redirect_uri:str

class Settings(BaseSettings):
    ollama: OllamaSettings
    opensearch: OpenSearchSettings
    oauth: OAuthSettings
    
    model_config = SettingsConfigDict(env_file='.env', env_nested_delimiter="__")
    
settings = Settings()

if __name__ == '__main__':
    settings = Settings()
    print(settings.model_dump())