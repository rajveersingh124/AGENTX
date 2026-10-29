"""
Task Manager Page for AGENTX.
Supports natural language task extraction, manual creation, status toggles,
priority categorization, search, and editing.
"""

import streamlit as st
from datetime import date
from modules import task_manager

def render():
    st.markdown("## 📋 Smart Task Manager")
    st.caption("Manage, extract, and prioritize tasks using intelligent natural language processing.")

    # 1. Natural Language Quick Add Bar
    st.markdown("##### ⚡ Quick Add with Natural Language")
    nl_col1, nl_col2 = st.columns([4, 1])
    with nl_col1:
        nl_input = st.text_input(
            "Quick Task Input",
            placeholder="e.g., 'Submit Machine Learning lab report by tomorrow 4 PM with High priority'",
            label_visibility="collapsed"
        )
    with nl_col2:
        if st.button("✨ AI Extract & Add", use_container_width=True):
            if nl_input.strip():
                with st.spinner("AI parsing task details..."):
                    created = task_manager.create_task_from_nl(nl_input)
                st.success(f"Added task #{created['id']}: '{created['title']}' [{created['priority']}]")
                st.rerun()
            else:
                st.warning("Please type a task description first.")

    # 2. Manual Task Add Accordion
    with st.expander("➕ Manual Task Creation", expanded=False):
        with st.form("manual_task_form", clear_on_submit=True):
            m_title = st.text_input("Task Title *", placeholder="Enter clear task objective")
            m_desc = st.text_area("Description (Optional)", placeholder="Add context or sub-steps")
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                m_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
            with f_col2:
                m_category = st.selectbox("Category", ["Work", "Study", "Personal", "Health", "Finance", "Other"], index=0)
            with f_col3:
                m_due = st.date_input("Due Date", value=date.today())

            submitted = st.form_submit_button("Save Task", use_container_width=True)
            if submitted:
                if m_title.strip():
                    task_manager.create_manual_task(
                        title=m_title,
                        description=m_desc,
                        priority=m_priority,
                        due_date=m_due.isoformat(),
                        category=m_category
                    )
                    st.success("Task created successfully!")
                    st.rerun()
                else:
                    st.error("Title is required.")

    st.markdown("<hr style='margin: 16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # 3. Filters & Search Bar
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 1])
    with filter_col1:
        search_query = st.text_input("🔍 Search Tasks", placeholder="Search by title or description...")
    with filter_col2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])
    with filter_col3:
        priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    with filter_col4:
        cat_filter = st.selectbox("Category", ["All", "Work", "Study", "Personal", "Health", "Finance", "Other"])

    # 4. Task List Fetch & Display
    tasks = task_manager.get_tasks(
        status=status_filter if status_filter != "All" else None,
        priority=priority_filter if priority_filter != "All" else None,
        category=cat_filter if cat_filter != "All" else None,
        search=search_query if search_query.strip() else None
    )

    st.markdown(f"**Showing {len(tasks)} Tasks**")

    if not tasks:
        st.info("No tasks found matching current filters.")
        return

    # Render each task card
    for task in tasks:
        is_done = (task["status"] == "completed")
        p_class = {
            "High": "task-card-high",
            "Medium": "task-card-medium",
            "Low": "task-card-low"
        }.get(task["priority"], "")

        card_class = f"task-card {p_class}" + (" task-card-completed" if is_done else "")

        badge_p = {
            "High": '<span class="badge badge-high">High</span>',
            "Medium": '<span class="badge badge-medium">Medium</span>',
            "Low": '<span class="badge badge-low">Low</span>'
        }.get(task["priority"], "")

        badge_c = f'<span class="badge badge-category">{task["category"]}</span>'

        with st.container():
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="font-size: 15px; font-weight: 600; color: #f0f6fc;">
                            {"[COMPLETED] " if is_done else ""}{task['title']}
                        </span>
                        <div style="margin-top: 6px;">
                            {badge_p} &nbsp; {badge_c} &nbsp; 
                            <span style="font-size: 12px; color: #8b949e;">Due: {task['due_date']}</span>
                        </div>
                        {f'<div style="font-size: 13px; color: #c9d1d9; margin-top: 6px;">{task["description"]}</div>' if task.get("description") else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons row under each card
            btn_col1, btn_col2, btn_col3, _ = st.columns([1.2, 1, 1, 4])
            with btn_col1:
                status_btn_label = "↩️ Reopen" if is_done else "✅ Mark Done"
                if st.button(status_btn_label, key=f"toggle_{task['id']}"):
                    task_manager.toggle_status(task['id'])
                    st.rerun()

            with btn_col2:
                with st.popover("✏️ Edit"):
                    new_title = st.text_input("Title", value=task["title"], key=f"edit_title_{task['id']}")
                    new_desc = st.text_area("Description", value=task.get("description") or "", key=f"edit_desc_{task['id']}")
                    new_p = st.selectbox("Priority", ["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(task["priority"]), key=f"edit_p_{task['id']}")
                    new_c = st.selectbox("Category", ["Work", "Study", "Personal", "Health", "Finance", "Other"], index=["Work", "Study", "Personal", "Health", "Finance", "Other"].index(task.get("category", "Work")), key=f"edit_c_{task['id']}")
                    if st.button("Save Changes", key=f"save_edit_{task['id']}"):
                        task_manager.update_task(task['id'], title=new_title, description=new_desc, priority=new_p, category=new_c)
                        st.toast("Task updated!")
                        st.rerun()

            with btn_col3:
                if st.button("🗑️ Delete", key=f"del_{task['id']}"):
                    task_manager.delete_task(task['id'])
                    st.toast("Task deleted.")
                    st.rerun()

            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

