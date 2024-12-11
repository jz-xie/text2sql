from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    client_id: str
    client_secret: str
    
    model_config = SettingsConfigDict(env_file=".env")