import pathlib
import streamlit as st
from pages.auth import login
from utils.navigation import make_sidebar

APP_DIR = pathlib.Path(__file__).parent.resolve()

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