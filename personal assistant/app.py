"""
AGENTX - Your AI-Powered Personal Assistant
Main application controller and router for Streamlit.
"""

import streamlit as st
from pathlib import Path
import config
from modules import database

# Page Configuration - Must be first Streamlit command
st.set_page_config(
    page_title="AGENTX – AI Personal Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Initialize persistent SQLite database
database.init_db()

# 2. Inject Custom Theme CSS
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Import Page Modules
from pages import dashboard
from pages import assistant
from pages import tasks
from pages import planner
from pages import notes
from pages import documents
from pages import settings

# 4. Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
        <div style="font-size: 24px; font-weight: 800; background: linear-gradient(90deg, #00d2ff, #9d4edd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            ⚡ AGENTX
        </div>
        <div style="font-size: 12px; color: #8b949e; letter-spacing: 0.05em; text-transform: uppercase;">
            Autonomous AI Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Status indicator
    if config.is_demo_mode():
        st.markdown('<div class="status-pill-demo" style="text-align: center; margin-bottom: 16px;">⚡ Demo Mode Active</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-pill-live" style="text-align: center; margin-bottom: 16px;">🟢 Groq ({config.get_model()})</div>', unsafe_allow_html=True)

    # Navigation choices
    nav_options = [
        "Dashboard",
        "AI Assistant",
        "Task Manager",
        "Daily Planner",
        "My Notes",
        "Document Assistant",
        "Settings"
    ]

    # Handle internal redirects
    if "nav_selection" not in st.session_state:
        st.session_state["nav_selection"] = "Dashboard"

    # Radio selection for navigation
    selected_page = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state["nav_selection"]),
        label_visibility="collapsed"
    )

    # Sync state if user clicked radio
    if selected_page != st.session_state["nav_selection"]:
        st.session_state["nav_selection"] = selected_page
        st.rerun()

    # Sidebar Quick Stats
    st.markdown("<hr style='margin: 20px 0 12px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    stats = database.get_task_statistics()
    st.markdown(f"""
    <div style="font-size: 12px; color: #8b949e; line-height: 1.8;">
        <div>📌 <b>Pending:</b> <span style="color: #faad14;">{stats['pending']}</span></div>
        <div>✅ <b>Completed:</b> <span style="color: #52c41a;">{stats['completed']}</span></div>
        <div>🔥 <b>High Priority:</b> <span style="color: #ff4d4f;">{stats['high_priority']}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="margin-top: 24px; font-size: 11px; color: #484f58; text-align: center;">
        AGENTX v2.4 &bull; Groq &bull; SQLite<br>College AI/ML Engineering Project
    </div>
    """, unsafe_allow_html=True)

# 5. Route to Active Page View
current_page = st.session_state["nav_selection"]

if current_page == "Dashboard":
    dashboard.render()
elif current_page == "AI Assistant":
    assistant.render()
elif current_page == "Task Manager":
    tasks.render()
elif current_page == "Daily Planner":
    planner.render()
elif current_page == "My Notes":
    notes.render()
elif current_page == "Document Assistant":
    documents.render()
elif current_page == "Settings":
    settings.render()

