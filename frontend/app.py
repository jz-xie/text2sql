import streamlit as st
from time import sleep
import httpx
from navigation import make_sidebar
import webbrowser
make_sidebar()

st.title("Welcome to Text2SQL")

st.write("Please log in with a Snowflake role to continue")

role_name = st.text_input(
    label="Role Name",
    placeholder="Snowflake Role Name",
    label_visibility = 'collapsed'
    )

backend_home_url = 'http://127.0.0.1:8000'
    

def login():
    login_url = f"{backend_home_url}/login"
    # st.markdown(f'<a href="{login_url}" target="_self">LOGIN with Snowflake</a>', unsafe_allow_html=True)
    st.markdown(
    f'<a href="{login_url}" target="_self" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Login with Snowflake</a>',
    unsafe_allow_html=True
)


if __name__ == "__main__":
    login()

    # if st.button("Log in", type="primary"):
    #     if username == "test" and password == "test":
    #         st.session_state.logged_in = True
    #         st.success("Logged in successfully!")
    #         sleep(0.5)
    #         st.switch_page("pages/page1.py")
    #     else:
    #         st.error("Incorrect username or password")
