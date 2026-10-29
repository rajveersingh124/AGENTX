"""
Document Assistant Page for AGENTX.
Uploads TXT and PDF files, extracts content with PyPDF, generates executive summaries,
and enables context-aware Question & Answering over document contents.
"""

import streamlit as st
from modules import document_assistant

def render():
    st.markdown("## 📄 AI Document Assistant")
    st.caption("Upload documents, extract summaries, and engage in question & answering over your materials.")

    # 1. File Upload Section
    with st.expander("📤 Upload New Document (TXT or PDF)", expanded=False):
        uploaded_file = st.file_uploader("Select a file", type=["txt", "pdf"])
        if uploaded_file is not None:
            st.write(f"**Filename:** `{uploaded_file.name}` ({round(uploaded_file.size / 1024, 1)} KB)")
            if st.button("Process & Analyze Document", use_container_width=True):
                with st.spinner("Extracting text and generating AI summary..."):
                    success, text_or_err = document_assistant.extract_text_from_upload(uploaded_file)
                    if not success:
                        st.error(text_or_err)
                    else:
                        ext = "pdf" if uploaded_file.name.lower().endswith(".pdf") else "txt"
                        res = document_assistant.process_and_save_document(
                            filename=uploaded_file.name,
                            file_type=ext,
                            content=text_or_err
                        )
                        st.success(f"Successfully processed '{uploaded_file.name}' ({res['char_count']} characters extracted).")
                        st.rerun()

    st.markdown("<hr style='margin: 16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # 2. Existing Documents
    docs = document_assistant.get_all_documents()

    if not docs:
        st.info("No documents uploaded yet. Upload a TXT or PDF document above to get started.")
        return

    # Document Selection Box
    doc_options = {d["id"]: f"{d['filename']} ({d['file_type'].upper()} - {d['char_count']} chars)" for d in docs}
    selected_doc_id = st.selectbox(
        "Select Document to Query:",
        options=list(doc_options.keys()),
        format_func=lambda x: doc_options[x]
    )

    active_doc = document_assistant.get_document_by_id(selected_doc_id)

    if active_doc:
        doc_col1, doc_col2 = st.columns([2, 1])

        with doc_col1:
            st.markdown(f"### 📑 {active_doc['filename']}")
            st.caption(f"Uploaded: {active_doc['uploaded_at'][:16] if active_doc.get('uploaded_at') else ''}")

            # Summary Box
            if active_doc.get("summary"):
                st.markdown(f"""
                <div class="note-summary" style="margin-top: 4px;">
                    <b>🤖 Executive Summary:</b><br>{active_doc['summary']}
                </div>
                """, unsafe_allow_html=True)

        with doc_col2:
            st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
            with st.expander("🔍 View Raw Extracted Text", expanded=False):
                st.text_area("Extracted Content", value=active_doc["content"][:3000] + ("..." if len(active_doc["content"]) > 3000 else ""), height=200, disabled=True)

            if st.button("🗑️ Delete Document", use_container_width=True):
                document_assistant.delete_document(active_doc["id"])
                st.toast("Document deleted.")
                st.rerun()

        st.markdown("<hr style='margin: 16px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

        # 3. Document Q&A Section
        st.markdown("### 💬 Ask Questions About This Document")
        st.caption("Ask specific questions, verify facts, or request summaries of particular sections.")

        q_input = st.text_input("Your Question:", placeholder="e.g. What are the core architectural components mentioned in this document?")

        if st.button("Search & Answer", use_container_width=True):
            if q_input.strip():
                with st.spinner("Analyzing document context and synthesizing response..."):
                    answer = document_assistant.ask_document_question(active_doc["id"], q_input)

                st.markdown("#### 🤖 AGENTX Response:")
                st.markdown(answer)
            else:
                st.warning("Please type a question first.")

