"""
Notes Manager Page for AGENTX.
Provides note creation, categorization, search, and AI-powered
summarization with key point extraction.
"""

import streamlit as st
from modules import notes_manager

def render():
    st.markdown("## 📝 Smart Notes Manager")
    st.caption("Capture ideas, research, and meeting notes with automated AI summarization and key takeaways.")

    # 1. Create New Note Form
    with st.expander("➕ Create New Note", expanded=False):
        with st.form("create_note_form", clear_on_submit=True):
            n_title = st.text_input("Note Title *", placeholder="e.g. LLM Memory & Tool Calling Architecture")
            n_tags = st.text_input("Tags (comma-separated)", placeholder="e.g. AI, Research, Groq")
            n_content = st.text_area("Note Content *", height=150, placeholder="Type or paste your detailed notes here...")
            auto_ai = st.checkbox("Generate AI Summary & Key Takeaways automatically upon saving", value=True)

            if st.form_submit_button("Save Note", use_container_width=True):
                if n_title.strip() and n_content.strip():
                    with st.spinner("Saving note and processing AI synthesis..."):
                        notes_manager.create_note(
                            title=n_title,
                            content=n_content,
                            tags=n_tags,
                            auto_summarize=auto_ai
                        )
                    st.success("Note saved successfully!")
                    st.rerun()
                else:
                    st.error("Title and content are required.")

    st.markdown("<hr style='margin: 16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # 2. Search Bar
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("🔍 Search Notes", placeholder="Search by title, content, or tags...")
    with search_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Reset Search", use_container_width=True):
            search_query = ""
            st.rerun()

    # 3. Notes Display
    notes = notes_manager.get_all_notes(search=search_query if search_query.strip() else None)

    st.markdown(f"**Saved Notes ({len(notes)})**")

    if not notes:
        st.info("No notes found. Create your first note above.")
        return

    for note in notes:
        with st.container():
            tags_html = ""
            if note.get("tags"):
                tags_list = [t.strip() for t in note["tags"].split(",") if t.strip()]
                tags_html = " ".join([f'<span class="badge badge-category">{t}</span>' for t in tags_list])

            st.markdown(f"""
            <div class="note-card">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div style="font-size: 18px; font-weight: 700; color: #f0f6fc;">
                        {note['title']}
                    </div>
                    <div style="font-size: 12px; color: #8b949e;">
                        {note['created_at'][:16] if note.get('created_at') else ''}
                    </div>
                </div>
                <div style="margin-top: 6px; margin-bottom: 10px;">
                    {tags_html}
                </div>
                <div style="color: #c9d1d9; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">
                    {note['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Display AI Summary & Key Points if available
            if note.get("summary"):
                st.markdown(f"""
                <div class="note-summary">
                    <b>🤖 AI Executive Summary:</b><br>{note['summary']}
                </div>
                """, unsafe_allow_html=True)

            if note.get("parsed_key_points"):
                with st.expander("📌 Key Extracted Takeaways", expanded=False):
                    for pt in note["parsed_key_points"]:
                        st.markdown(f"- {pt}")

            # Actions Row
            n_col1, n_col2, n_col3, _ = st.columns([1.5, 1, 1, 3])
            with n_col1:
                if st.button("✨ (Re)Synthesize with AI", key=f"synth_{note['id']}"):
                    with st.spinner("AI analyzing note and extracting key takeaways..."):
                        notes_manager.synthesize_note(note['id'])
                    st.toast("AI summary generated!")
                    st.rerun()

            with n_col2:
                with st.popover("✏️ Edit"):
                    e_title = st.text_input("Title", value=note["title"], key=f"e_title_{note['id']}")
                    e_tags = st.text_input("Tags", value=note.get("tags") or "", key=f"e_tags_{note['id']}")
                    e_body = st.text_area("Content", value=note["content"], height=120, key=f"e_body_{note['id']}")
                    if st.button("Update Note", key=f"save_e_{note['id']}"):
                        notes_manager.update_note_content(note['id'], e_title, e_body, e_tags)
                        st.toast("Note updated.")
                        st.rerun()

            with n_col3:
                if st.button("🗑️ Delete", key=f"del_note_{note['id']}"):
                    notes_manager.delete_note(note['id'])
                    st.toast("Note deleted.")
                    st.rerun()

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

