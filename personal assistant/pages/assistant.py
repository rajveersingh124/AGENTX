"""
AI Assistant Page for AGENTX.
Provides interactive conversational interface, transparent Agentic AI reasoning,
multi-step execution trace, and pre-built demonstration scenarios.
"""

import streamlit as st
import json
from modules import database
from modules import agent
import config

def render():
    st.markdown("## 🤖 AGENTX Intelligence Hub")
    st.caption("Interact with your autonomous personal assistant. State your goal, and AGENTX will plan and execute.")

    # Top Demonstration Scenario Pills
    st.markdown("**💡 Quick Demonstration Scenarios (Click to test):**")
    p1, p2, p3, p4 = st.columns(4)
    quick_prompt = None

    with p1:
        if st.button("🎯 Organize My Day (3 Tasks)", use_container_width=True):
            quick_prompt = "Help me organize my day and create three important tasks."
    with p2:
        if st.button("➕ Add Urgent Task", use_container_width=True):
            quick_prompt = "Add task: Submit AI Agent documentation by Friday 5 PM with High priority"
    with p3:
        if st.button("🗓️ Build Daily Schedule", use_container_width=True):
            quick_prompt = "Generate an optimized daily schedule based on my pending tasks"
    with p4:
        if st.button("⚡ Productivity Check", use_container_width=True):
            quick_prompt = "Give me a daily productivity briefing and suggest my next best action"

    # Header controls
    c_left, c_right = st.columns([4, 1])
    with c_right:
        if st.button("🗑️ Clear History", use_container_width=True):
            database.clear_chat_history()
            st.toast("Chat history cleared.")
            st.rerun()

    # Load history from SQLite
    history = database.get_chat_history(limit=40)

    # Render Chat History
    for msg in history:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

            # If there is agent reasoning recorded, show transparency expander
            if msg.get("agent_thought"):
                try:
                    thought = json.loads(msg["agent_thought"])
                    with st.expander("🧠 View Agent Reasoning & Tool Trace", expanded=False):
                        st.markdown(f"**Identified Intent:** `{thought.get('intent')}`")
                        st.markdown(f"**Agent Reasoning:** *{thought.get('reasoning')}*")
                        if thought.get("plan"):
                            st.markdown("**Execution Plan:**")
                            for s in thought.get("plan", []):
                                st.markdown(f"- {s}")
                        if thought.get("tool_executions"):
                            st.markdown("**Tools Executed:**")
                            for t in thought.get("tool_executions", []):
                                status_icon = "✅" if t.get("success") else "❌"
                                st.markdown(f"{status_icon} **Tool:** `{t.get('tool')}`")
                                if t.get("output"):
                                    st.code(str(t.get("output")), language="text")
                except Exception:
                    pass

    # Chat Input
    user_input = st.chat_input("Enter your command or question for AGENTX...")

    active_prompt = quick_prompt if quick_prompt else user_input

    if active_prompt:
        # Display user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(active_prompt)

        # Agent processing with realistic spinner
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("AGENTX is analyzing intent, formulating plan, and selecting tools..."):
                agent_res = agent.run_agent_workflow(active_prompt)

            st.markdown(agent_res.response_text)

            # Show reasoning trace
            with st.expander("🧠 View Agent Reasoning & Tool Trace", expanded=True):
                st.markdown(f"**Identified Intent:** `{agent_res.intent}`")
                st.markdown(f"**Agent Reasoning:** *{agent_res.reasoning}*")
                if agent_res.plan:
                    st.markdown("**Execution Plan:**")
                    for s in agent_res.plan:
                        st.markdown(f"- {s}")
                if agent_res.tool_executions:
                    st.markdown("**Tools Executed:**")
                    for t in agent_res.tool_executions:
                        status_icon = "✅" if t.get("success") else "❌"
                        st.markdown(f"{status_icon} **Tool:** `{t.get('tool')}`")
                        if t.get("output"):
                            st.code(str(t.get("output")), language="text")

        st.rerun()

