import streamlit as st
import streamlit_authenticator as stauth
import openai
import sqlite3
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="AI To-Do List", layout="centered")
st.title("🧠 AI-Powered To-Do List")

# --- User Authentication ---
# Pre-hashed password for 'demo123'
hashed_passwords = [
    'pbkdf2:sha256:260000$WmZK1XkUuKJvJm$e3f6d5c9e5f4a9d6e7f4b9c6e8f4d9c6e7f4b9c6e8f4d9c6e7f4b9c6e8f4d9c6'
]

config = {
    'credentials': {
        'usernames': {
            'demo': {
                'name': 'Demo User',
                'password': hashed_passwords[0]
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

authenticator = stauth.Authenticate(config)
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Invalid credentials")
elif authentication_status is None:
    st.warning("Please enter your username and password")
elif authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Welcome {name}!")

    # --- Database Setup ---
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (user TEXT, task TEXT, due TEXT, status TEXT)''')
    conn.commit()

    # --- Add Task ---
    st.subheader("Add a Task")
    task_input = st.text_input("Describe your task in natural language:")
    if st.button("Add Task"):
        if task_input:
            parsed_task = task_input
            due_date = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO tasks VALUES (?, ?, ?, ?)", (username, parsed_task, due_date, "pending"))
            conn.commit()
            st.success("Task added!")

    # --- Show Tasks ---
    st.subheader("Your Tasks")
    c.execute("SELECT task, due, status FROM tasks WHERE user=?", (username,))
    rows = c.fetchall()
    for row in rows:
        st.write(f"📝 {row[0]} — Due: {row[1]} — Status: {row[2]}")