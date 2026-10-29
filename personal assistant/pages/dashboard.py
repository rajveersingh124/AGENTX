"""
Dashboard Page for AGENTX.
Displays high-level productivity metrics, today's schedule, priority focus items,
and recent activity history.
"""

import streamlit as st
from datetime import datetime, date
import config
from modules import database
from modules import planner
from modules import ai_engine

def render():
    now = datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good Morning"
    elif hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    today_str = date.today().isoformat()
    formatted_date = now.strftime("%A, %B %d, %Y")

    is_demo = config.is_demo_mode()
    status_pill = (
        f'<span class="status-pill-demo">⚡ Demo Mode (No API Key)</span>'
        if is_demo else
        f'<span class="status-pill-live">🟢 Groq Connected ({config.get_model()})</span>'
    )

    # 1. Hero Banner
    st.markdown(f"""
    <div class="agentx-hero">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="agentx-hero-title">{greeting}, welcome to AGENTX</div>
                <div class="agentx-hero-subtitle">
                    Autonomous AI Personal Assistant & Productivity Orchestrator &bull; <b>{formatted_date}</b>
                </div>
            </div>
            <div>
                {status_pill}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Metric Cards
    stats = database.get_task_statistics()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Tasks</div>
            <div class="metric-value">{stats['total']} <span class="metric-sub">records</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Pending Tasks</div>
            <div class="metric-value">{stats['pending']} <span class="metric-sub" style="color: #faad14;">actionable</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Completed</div>
            <div class="metric-value">{stats['completed']} <span class="metric-sub" style="color: #52c41a;">done</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Productivity Rate</div>
            <div class="metric-value">{stats['completion_rate']}% <span class="metric-sub" style="color: #00d2ff;">efficiency</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 3. Quick Action Bar
    q_col1, q_col2, q_col3 = st.columns([1, 1, 1])
    with q_col1:
        if st.button("🗓️ Auto-Generate AI Schedule", use_container_width=True):
            planner.generate_ai_schedule(today_str)
            st.toast("Generated AI Daily Timetable!", icon="🗓️")
            st.rerun()

    with q_col2:
        if st.button("⚡ Ask AI Assistant", use_container_width=True):
            st.session_state["nav_selection"] = "AI Assistant"
            st.rerun()

    with q_col3:
        if st.button("➕ Open Task Manager", use_container_width=True):
            st.session_state["nav_selection"] = "Task Manager"
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 4. Two-Column Dashboard Content
    left_col, right_col = st.columns([1.6, 1.2])

    with left_col:
        st.markdown("### 📅 Today's Schedule")
        schedule = planner.get_schedule(today_str)

        if not schedule:
            st.info("No schedule items for today. Click **Auto-Generate AI Schedule** above to construct your timetable.")
        else:
            for item in schedule:
                p_badge = {
                    "High": '<span class="badge badge-high">High</span>',
                    "Medium": '<span class="badge badge-medium">Medium</span>',
                    "Low": '<span class="badge badge-low">Low</span>'
                }.get(item["priority"], "")

                status_color = "#52c41a" if item["status"] == "completed" else ("#faad14" if item["status"] == "in_progress" else "#00d2ff")
                status_icon = "✅" if item["status"] == "completed" else ("⏳" if item["status"] == "in_progress" else "📌")

                card_html = f"""
                <div class="schedule-card">
                    <div style="flex-grow: 1;">
                        <span class="schedule-time">{item['time_slot']}</span> &nbsp; {p_badge}
                        <div style="font-weight: 600; color: #f0f6fc; margin-top: 4px;">{item['title']}</div>
                    </div>
                    <div style="color: {status_color}; font-size: 13px; font-weight: 600;">
                        {status_icon} {item['status'].replace('_', ' ').capitalize()}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

    with right_col:
        st.markdown("### 🎯 Priority Focus")
        pending_high = database.get_tasks(status="pending", priority="High")

        if not pending_high:
            st.success("No pending high-priority tasks. Excellent job staying ahead!")
        else:
            for t in pending_high[:4]:
                st.markdown(f"""
                <div class="task-card task-card-high" style="padding: 10px 14px; margin-bottom: 8px;">
                    <div style="font-weight: 600; color: #f0f6fc; font-size: 14px;">{t['title']}</div>
                    <div style="font-size: 12px; color: #8b949e; margin-top: 4px;">Category: {t['category']} &bull; Due: {t['due_date']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("### 📜 Recent Activity")
        activities = database.get_recent_activities(limit=5)
        if activities:
            for act in activities:
                time_str = act["timestamp"][:16] if act.get("timestamp") else ""
                st.markdown(f"""
                <div class="activity-item">
                    <span>{act['description']}</span>
                    <span class="activity-time">{time_str}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No recent activities logged.")

