import streamlit as st
import streamlit_authenticator as stauth

# Minimal credentials
credentials = {
    "usernames": {
        "demo": {
            "email": "demo@example.com",
            "name": "Demo User",
            "password": "demo123"
        }
    }
}

cookie = {
    "name": "test_app",
    "key": "abcdef",
    "expiry_days": 1
}

preauthorized = {
    "emails": []
}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie=cookie,
    preauthorized=preauthorized
)

name, auth_status, username = authenticator.login("Login", "sidebar")

if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome {name}!")
elif auth_status is False:
    st.error("Invalid credentials")
elif auth_status is None:
    st.warning("Please enter your username and password")