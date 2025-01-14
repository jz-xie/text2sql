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
from config import get_settings

oauth_settings = get_settings().oauth

app = FastAPI()

# router = APIRouter(
#     prefix="/auth",
#     tags=['auth']
# )




oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=oauth_settings.auth_url,
    tokenUrl=oauth_settings.token_url,
)

# @lru_cache
# def get_auth_config(request:Request):
#     return {
#         "response_type": "code",
#         # "client_id": AuthSettings.model_config.get("CLIENT_ID"),
#         "client_id": "6j7nry5cequaFGGqqqBTTd1e7oy4M9pVb6bckVGa",
#         "redirect_uri": "http://127.0.0.1:8000/callback"
#         # "redirect_uri": f"{request.base_url}/{app.url_path_for('callback')}"
#     }


# login
# # redirect_uri = "https://yourapp.com/callback"
# # oauth2_scheme.

def login():
    oauth_settings = settings.oauth
    
    param = {
        "response_type": "code",
        "client_id": oauth_settings.client_id,
        "redirect_uri":  oauth_settings.redirect_uri
        }
    auth_link = f"{auth_url}?{urllib.parse.urlencode(param)}"
    st.markdown(
        f'<a href="{auth_link}" target="_self" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Login with Snowflake</a>',
        unsafe_allow_html=True
    )
    
    if st.query_params.get("code", False):
        code = st.query_params["code"]
        param.update({
            "grant_type": "authorization_code",
            "client_secret": oauth_settings.client_secret,
            "code": code
            
        })
        r = httpx.post(url=token_url,data=param)
        if r.status_code == 200:
            # print(True)/
            st.session_state["logged_in"]=True
            st.switch_page("pages/chat.py")


@app.get("/login")
async def login(config: Annotated[dict, Depends(get_settings)], request: Request):
    """Redirect to OAuth 2.0 server for login."""
    param = {
        "response_type": "code",
        "client_id": oauth_settings.client_id,
        "redirect_uri":  oauth_settings.redirect_uri
        }
    auth_link = f"{oauth_settings.auth_url}?{urllib.parse.urlencode(param)}"
    return RedirectResponse(auth_link)

@app.get("/callback")
async def callback(code: str):
    """Redirect to OAuth 2.0 server for login."""
    param = {
        "response_type": "code",
        "client_id": oauth_settings.client_id,
        "client_secret": oauth_settings.client_secret,
        "code": code
    }
    
    httpx.post(
        url=oauth_settings.token_url,
        # data={
        #     "code": code
        #     "client_id":
        #     }
    )
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