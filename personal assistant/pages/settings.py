"""
Settings Page for AGENTX.
Manages API credentials, LLM configuration, connectivity verification,
database state resets, and presentation guidance.
"""

import streamlit as st
import config
from modules import database

def render():
    st.markdown("## ⚙️ System Settings & Configuration")
    st.caption("Configure Groq LLM connectivity, verify system parameters, or manage presentation data.")

    # 1. API Status Card
    is_demo = config.is_demo_mode()
    curr_key = config.get_api_key()
    curr_url = config.get_base_url()
    curr_model = config.get_model()

    if is_demo:
        st.warning(
            "⚡ **Demo Mode is Active:** No valid Groq API key is detected. "
            "AGENTX is operating using built-in deterministic heuristic planning and offline simulation. "
            "To unlock full LLM reasoning, enter your free Groq API key below."
        )
    else:
        st.success(
            f"🟢 **Live LLM Active:** Connected to `{curr_model}` via Groq OpenAI-compatible API "
            f"(Key: `{config.mask_api_key(curr_key)}`)."
        )

    # 2. API Configuration Form
    with st.container():
        st.markdown("### 🔑 Groq API Configuration")
        st.caption("Get a free, ultra-fast API key from [Groq Console](https://console.groq.com/keys).")

        new_key = st.text_input(
            "Groq API Key (starts with gsk_...)",
            value=curr_key,
            type="password",
            help="Your API key is stored securely in your local .env file and never exposed in UI or logs."
        )

        col_url, col_model = st.columns(2)
        with col_url:
            new_url = st.text_input("Base URL", value=curr_url)
        with col_model:
            model_idx = config.AVAILABLE_MODELS.index(curr_model) if curr_model in config.AVAILABLE_MODELS else 0
            new_model = st.selectbox("LLM Model", options=config.AVAILABLE_MODELS, index=model_idx)

        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("💾 Save Settings", use_container_width=True):
                success = config.save_config(new_key, new_url, new_model)
                if success:
                    st.success("Configuration saved to .env!")
                    st.rerun()
                else:
                    st.error("Failed to save configuration.")

        with btn_c2:
            if st.button("🔌 Test API Connection", use_container_width=True):
                with st.spinner("Pinging LLM endpoint..."):
                    ok, msg = config.test_api_connection(new_key or curr_key, new_url, new_model)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    st.markdown("<hr style='margin: 20px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # 3. Database & Memory Operations
    st.markdown("### 🗄️ Database & Memory Management")
    db_col1, db_col2 = st.columns(2)

    with db_col1:
        st.markdown("**Restore Sample Demo Dataset**")
        st.caption("Resets tasks, notes, timetable, and documents to a fresh presentation-ready state.")
        if st.button("🔄 Reset to Demo Data", use_container_width=True):
            database.reset_database()
            st.success("Database restored to clean presentation state!")
            st.rerun()

    with db_col2:
        st.markdown("**Clear Conversation History**")
        st.caption("Clears all past assistant chat logs and reasoning records.")
        if st.button("🗑️ Clear Chat Memory", use_container_width=True):
            database.clear_chat_history()
            st.success("Chat history cleared.")
            st.rerun()

    st.markdown("<hr style='margin: 20px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # 4. College Presentation Demonstration Guide
    with st.expander("🎓 College Project Presentation Checklist & Demo Script", expanded=False):
        st.markdown("""
        #### How to present AGENTX to evaluators:
        1. **Introduction (1 min):**
           - Present AGENTX as an autonomous Personal Assistant combining Groq LLMs with modular tools and SQLite persistent memory.
           - Highlight that unlike standard chatbots, AGENTX executes multi-step plans and real database actions.
        2. **Core Feature 1: The Agentic Workflow (2 mins):**
           - Go to **AI Assistant**.
           - Click or type: `Help me organize my day and create three important tasks.`
           - Expand the **🧠 View Agent Reasoning & Tool Trace** to demonstrate:
             - **Intent Classification** (`multi_step_workflow`)
             - **Reasoning formulation**
             - **Step-by-step Tool Execution** (`task_create_batch` and `schedule_generate`)
             - **Result Verification**
        3. **Core Feature 2: Smart Task Management (1.5 mins):**
           - Go to **Task Manager**.
           - Demonstrate natural language extraction: `Submit project report tomorrow 5 PM High Priority`.
           - Show instant parsing into title, priority, due date, and category.
        4. **Core Feature 3: AI Daily Planner (1.5 mins):**
           - Go to **Daily Planner**.
           - Show the time-blocked schedule with priority categorization and progress toggling.
        5. **Core Feature 4: Document Analysis & Notes (1.5 mins):**
           - Go to **Document Assistant** to show context-aware Q&A on the sample technical specification.
           - Go to **My Notes** to show automatic AI summary and key point extraction.
        6. **Robustness & Architecture:**
           - Explain fallback Demo Mode, modular separation of concerns, and clean SQLite schema.
        """)

