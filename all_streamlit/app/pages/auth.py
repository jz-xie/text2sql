import streamlit as st
import httpx
import urllib
from utils.navigation import make_sidebar
from config import settings

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
    

if __name__ == "__main__":
    make_sidebar()

    auth_url="http://localhost:9000/application/o/authorize/"
    token_url = "http://localhost:9000/application/o/token/"

    st.title("Welcome to Text2SQL")

    role_name = st.text_input(
        label="Please key in a Snowflake role to login",
        placeholder="Snowflake Role Name",
        )
    login()