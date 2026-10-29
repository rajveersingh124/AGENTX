"""
Daily Planner Page for AGENTX.
Provides AI-assisted daily timetable generation, time-blocking,
fatigue-aware scheduling, and custom timetable adjustments.
"""

import streamlit as st
from datetime import date
from modules import planner

def render():
    st.markdown("## 🗓️ AI Daily Planner")
    st.caption("Organize your day with structured time-blocks generated dynamically based on task priority.")

    # 1. Date Selector and Generation Controls
    top_col1, top_col2, top_col3 = st.columns([1.5, 1.5, 1])

    with top_col1:
        selected_date = st.date_input("Select Date", value=date.today())
        date_str = selected_date.isoformat()

    with top_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("✨ Auto-Generate AI Schedule", use_container_width=True):
            with st.spinner("AI organizing tasks into optimal energy blocks..."):
                planner.generate_ai_schedule(date_str)
            st.success("Daily timetable successfully synthesized!")
            st.rerun()

    with top_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Schedule", use_container_width=True):
            planner.clear_day(date_str)
            st.toast("Schedule cleared for selected date.")
            st.rerun()

    # 2. Add Custom Time Block
    with st.expander("➕ Add Custom Time Slot", expanded=False):
        with st.form("custom_slot_form", clear_on_submit=True):
            col_s1, col_s2 = st.columns([1, 2])
            with col_s1:
                slot_time = st.text_input("Time Slot", placeholder="e.g. 03:00 - 04:30 PM")
            with col_s2:
                slot_title = st.text_input("Session Objective / Title", placeholder="e.g. Deep Focus: Lab Experiment")

            col_s3, col_s4 = st.columns(2)
            with col_s3:
                slot_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
            with col_s4:
                slot_status = st.selectbox("Status", ["planned", "in_progress", "completed"])

            if st.form_submit_button("Add to Timetable", use_container_width=True):
                if slot_time and slot_title:
                    planner.add_schedule_slot(date_str, slot_time, slot_title, slot_priority, slot_status)
                    st.success("Time block added.")
                    st.rerun()
                else:
                    st.error("Time slot and title are required.")

    st.markdown("<hr style='margin: 16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # 3. Schedule View
    schedule = planner.get_schedule(date_str)

    st.markdown(f"### 📋 Timetable for {selected_date.strftime('%A, %B %d, %Y')}")

    if not schedule:
        st.info("No time blocks scheduled for this date. Click 'Auto-Generate AI Schedule' to let AGENTX schedule your pending tasks.")
        return

    for item in schedule:
        status = item["status"]
        p_badge = {
            "High": '<span class="badge badge-high">High Priority</span>',
            "Medium": '<span class="badge badge-medium">Medium</span>',
            "Low": '<span class="badge badge-low">Low</span>'
        }.get(item["priority"], "")

        status_text = status.replace('_', ' ').capitalize()
        status_color = "#52c41a" if status == "completed" else ("#faad14" if status == "in_progress" else "#00d2ff")

        with st.container():
            st.markdown(f"""
            <div class="schedule-card" style="border-left: 4px solid {status_color};">
                <div>
                    <span class="schedule-time">{item['time_slot']}</span> &nbsp; {p_badge}
                    <div style="font-size: 16px; font-weight: 600; color: #f0f6fc; margin-top: 5px;">
                        {item['title']}
                    </div>
                </div>
                <div style="font-size: 13px; font-weight: 600; color: {status_color};">
                    ● {status_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Slot management row
            b1, b2, b3, b4 = st.columns([1, 1, 1, 3])
            with b1:
                if status != "in_progress":
                    if st.button("⏳ In Progress", key=f"prog_{item['id']}"):
                        planner.update_slot_status(item['id'], "in_progress")
                        st.rerun()
            with b2:
                if status != "completed":
                    if st.button("✅ Complete", key=f"comp_{item['id']}"):
                        planner.update_slot_status(item['id'], "completed")
                        st.rerun()
            with b3:
                if status != "planned":
                    if st.button("↩️ Reset", key=f"rst_{item['id']}"):
                        planner.update_slot_status(item['id'], "planned")
                        st.rerun()
            with b4:
                if st.button("🗑️ Remove", key=f"del_slot_{item['id']}"):
                    planner.delete_slot(item['id'])
                    st.rerun()

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

