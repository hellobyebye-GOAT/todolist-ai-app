import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="AI To-Do List", layout="centered", initial_sidebar_state="expanded")
st.title("🧠 AI-Powered To-Do List")

# --- Auth Config (demo credentials) ---
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

# --- Login ---
try:
    name, authentication_status, username = authenticator.login("Login", "main")
except KeyError:
    # Catch cleared state after logout
    authentication_status = None
    name = None
    username = None

# --- Helper: DB connection ---
def get_conn():
    if "conn" not in st.session_state:
        st.session_state.conn = sqlite3.connect("tasks.db", check_same_thread=False)
    return st.session_state.conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            task TEXT NOT NULL,
            due TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

# --- CRUD operations ---
def add_task(user, task, due):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (user, task, due, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (user, task, due, datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()

def list_tasks(user, sort_by="due", only_status=None):
    conn = get_conn()
    c = conn.cursor()
    base = "SELECT id, task, due, status, created_at FROM tasks WHERE user=?"
    params = [user]
    if only_status:
        base += " AND status=?"
        params.append(only_status)
    if sort_by == "due":
        base += " ORDER BY COALESCE(due, ''), status DESC"
    elif sort_by == "created":
        base += " ORDER BY created_at DESC"
    elif sort_by == "status":
        base += " ORDER BY status ASC, COALESCE(due, '')"
    else:
        base += " ORDER BY id DESC"
    c.execute(base, params)
    return c.fetchall()

def toggle_complete(task_id, complete=True):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tasks SET status=? WHERE id=?", ("done" if complete else "pending", task_id))
    conn.commit()

def delete_task(task_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()

def update_task(task_id, new_text, new_due):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tasks SET task=?, due=? WHERE id=?", (new_text, new_due, task_id))
    conn.commit()

# --- UI Flow ---
if authentication_status is False:
    st.error("Invalid credentials")
elif authentication_status is None:
    st.warning("Please enter your username and password")
elif authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome {name}!")
    st.write("🎉 You’re logged in! Ready to build your to-do list.")

    # Initialize DB once logged in
    init_db()

    # --- Add Task ---
    st.subheader("Add a task")
    with st.form("add_task_form", clear_on_submit=True):
        task_text = st.text_input("Task description", placeholder="e.g., Draft Einstein speech section")
        due_input = st.date_input("Due date (optional)", value=None, format="YYYY-MM-DD")
        submitted = st.form_submit_button("Add task")
        if submitted:
            if task_text.strip():
                due_str = due_input.isoformat() if due_input else None
                add_task(username, task_text.strip(), due_str)
                st.success("Task added.")
            else:
                st.warning("Please enter a task description.")

    # --- Filters & Sorting ---
    st.subheader("Your tasks")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        sort_choice = st.selectbox("Sort by", ["due", "created", "status"], index=0)
    with col2:
        status_filter = st.selectbox("Filter", ["all", "pending", "done"], index=0)
    with col3:
        st.info("Tip: Use Edit to change text or due date. Toggle to mark done.")

    status_arg = None if status_filter == "all" else status_filter
    tasks = list_tasks(username, sort_by=sort_choice, only_status=status_arg)

    # --- Task List ---
    if not tasks:
        st.caption("No tasks yet. Add your first task above.")
    else:
        for tid, ttext, tdue, tstatus, created in tasks:
            exp = st.expander(f"📝 {ttext} | Due: {tdue or '—'} | Status: {tstatus}", expanded=False)
            with exp:
                c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
                with c1:
                    if tstatus != "done":
                        if st.button("Mark done ✅", key=f"done_{tid}"):
                            toggle_complete(tid, True)
                            st.rerun()
                    else:
                        if st.button("Mark pending ⏳", key=f"pend_{tid}"):
                            toggle_complete(tid, False)
                            st.rerun()
                with c2:
                    if st.button("Delete 🗑️", key=f"del_{tid}"):
                        delete_task(tid)
                        st.rerun()
                with c3:
                    edit_key = f"edit_{tid}"
                    if st.button("Edit ✏️", key=edit_key):
                        st.session_state[f"editing_{tid}"] = True

                if st.session_state.get(f"editing_{tid}", False):
                    st.write("Edit task")
                    new_text = st.text_input("Task", value=ttext, key=f"txt_{tid}")
                    new_due = st.date_input(
                        "Due date (optional)",
                        value=None if tdue is None or tdue == "" else datetime.fromisoformat(tdue).date(),
                        format="YYYY-MM-DD",
                        key=f"due_{tid}"
                    )
                    ec1, ec2 = st.columns([1, 1])
                    with ec1:
                        if st.button("Save changes 💾", key=f"save_{tid}"):
                            update_task(tid, new_text.strip(), new_due.isoformat() if new_due else None)
                            st.session_state[f"editing_{tid}"] = False
                            st.success("Task updated.")
                            st.rerun()
                    with ec2:
                        if st.button("Cancel ✖️", key=f"cancel_{tid}"):
                            st.session_state[f"editing_{tid}"] = False
                            st.rerun()
else:
    st.info("You have logged out. Please log in again.")