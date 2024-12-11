import streamlit as st
import httpx

backend_home_url = 'http://127.0.0.1:8000'

def login():
    auth_url = httpx.get(
        url= f"{backend_home_url}/login"
    )
    # print(auth_url)
    print(auth_url)
    # st.redirect(auth_url)
    # return auth_url
    

def main():
    # st.link_button(
    #     label="LOGIN",
    #     url=
    # )
    login_url = f"{backend_home_url}/login"
    st.markdown(f'<a href="{login_url}" target="_self">LOGIN with Snowflake</a>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
    # backend_home_url = 'http://127.0.0.1:8000'
    # auth_url = httpx.get(
    #     url= 
    # )
    # # print(auth_url)
    # print(auth_url.)
