from pydantic_settings import BaseSettings, SettingsConfigDict
# from fastapi import 
from functools import lru_cache

class AuthSettings(BaseSettings):
    client_id: str
    client_secret: str
    
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_auth_settings():
    return AuthSettings().model_dump()
# def get_auth_config(request:Request):
#     return {
#         "response_type": "code",
#         # "client_id": AuthSettings.model_config.get("CLIENT_ID"),
#         "client_id": "6j7nry5cequaFGGqqqBTTd1e7oy4M9pVb6bckVGa",
#         "redirect_uri": "http://127.0.0.1:8000/callback"
#         # "redirect_uri": f"{request.base_url}/{app.url_path_for('callback')}"
#     }