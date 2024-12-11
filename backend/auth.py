from functools import lru_cache
import os
import urllib.parse
from fastapi import FastAPI, Depends, Request, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from pydantic import BaseModel
from typing_extensions import Annotated
import httpx
import urllib
from config import AuthSettings

app = FastAPI()

# router = APIRouter(
#     prefix="/auth",
#     tags=['auth']
# )



auth_url="http://localhost:9000/application/o/authorize/"
token_url = "http://localhost:9000/application/o/token/"

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=auth_url,
    tokenUrl=token_url,
)

@lru_cache
def get_auth_config(request:Request):
    return {
        "response_type": "code",
        # "client_id": AuthSettings.model_config.get("CLIENT_ID"),
        "client_id": "6j7nry5cequaFGGqqqBTTd1e7oy4M9pVb6bckVGa",
        "redirect_uri": "http://127.0.0.1:8000/callback"
        # "redirect_uri": f"{request.base_url}/{app.url_path_for('callback')}"
    }


# login
# # redirect_uri = "https://yourapp.com/callback"
# # oauth2_scheme.


@app.get("/login")
async def login(config: Annotated[dict, Depends(get_auth_config)], request: Request):
    """Redirect to OAuth 2.0 server for login."""
    auth_link = f"{auth_url}?{urllib.parse.urlencode(config)}"
    return RedirectResponse(auth_link)

@app.get("/callback")
async def callback(code: str):
    """Redirect to OAuth 2.0 server for login."""
    print(code)
    return RedirectResponse("https://www.google.com")


from fastapi.security import OAuth2AuthorizationCodeBearer



# @app.get("/users/my_profile")
# def get_my_google_profile(token: str = Depends(oauth2_google)):
#     # I have no idea where to get user profile on google or what the parameters are. It is vendor specific.
#     # Check their doc.
#     with requests.get("https://google's profile getting api", params={"access_token" : token}) as response:
#         return response.json()


# from fastapi import FastAPI, Depends, Query, Path

# app = FastAPI()

# def get_query_param(q: str = None):
#     return q
# Query()
# @app.get("/items/")
# async def read_items(query: str = Depends(get_query_param)):
#     return {"query": query}

# @app.get("/items/{item_id}")
# async def read_item(item_id):
#     return {"item_id": item_id}