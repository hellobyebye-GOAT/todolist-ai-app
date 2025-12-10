import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- Page Setup ---
st.set_page_config(page_title="AI To-Do List", layout="centered")
st.title("🧠 AI-Powered To-Do List")

# --- Authentication Config ---
config = {
    'credentials': {
        'usernames': {
            'demo': {
                'email': 'demo@example.com',
                'name': 'Demo User',
                'password': stauth.Hasher(['demo123']).generate()[0]
            }
        }
    },
    'cookie': {
        'name': 'todo_app',
        'key': 'abcdef',
        'expiry_days': 30
    },
    'preauthorized': {
        'emails': []
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Invalid credentials")
elif authentication_status is None:
    st.warning("Please enter your username and password")
elif authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome {name}!")
    st.write("🎉 You’re logged in! Ready to build your to-do list.")