"""
AI Document Assistant module for AGENTX.
Processes uploaded TXT and PDF documents, extracts text content,
generates executive summaries, and provides context-aware Question & Answering.
"""

import io
from typing import Any, Dict, List, Optional
import pypdf
from modules import database
from modules import ai_engine

def extract_text_from_upload(uploaded_file) -> tuple[bool, str]:
    """
    Extract text content from uploaded file (TXT or PDF).
    Returns (success: bool, text_or_error: str).
    """
    if uploaded_file is None:
        return False, "No file provided."

    fname = uploaded_file.name.lower()
    try:
        if fname.endswith(".txt"):
            raw_bytes = uploaded_file.read()
            # Try UTF-8, fallback to latin-1
            try:
                text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = raw_bytes.decode("latin-1", errors="replace")
            return True, text

        elif fname.endswith(".pdf"):
            reader = pypdf.PdfReader(uploaded_file)
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(f"--- Page {i+1} ---\n{page_text}")
            full_text = "\n\n".join(extracted_pages)
            if not full_text.strip():
                return False, "Could not extract readable text from PDF (it might be scanned/image-only)."
            return True, full_text

        else:
            return False, f"Unsupported file type. Please upload a .txt or .pdf file."

    except Exception as e:
        return False, f"Failed to process document: {str(e)}"

def process_and_save_document(filename: str, file_type: str, content: str) -> Dict[str, Any]:
    """
    Synthesize an executive summary using AI and save document to SQLite.
    """
    summary_obj = ai_engine.summarize_text_content(filename, content[:4000])
    summary = summary_obj.get("summary", "Document analyzed and saved.")

    doc_id = database.add_document(
        filename=filename,
        file_type=file_type,
        content=content,
        summary=summary
    )

    return {
        "id": doc_id,
        "filename": filename,
        "summary": summary,
        "char_count": len(content)
    }

def ask_document_question(doc_id: int, question: str) -> str:
    """
    Answer a user query with context from a specific document.
    """
    doc = database.get_document_by_id(doc_id)
    if not doc:
        return "Error: Document not found in database."

    return ai_engine.answer_document_question(
        doc_name=doc["filename"],
        doc_content=doc["content"],
        question=question
    )

def get_all_documents() -> List[Dict[str, Any]]:
    """Fetch metadata of all uploaded documents."""
    return database.get_documents()

def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full document text by ID."""
    return database.get_document_by_id(doc_id)

def delete_document(doc_id: int) -> bool:
    """Delete a document."""
    return database.delete_document(doc_id)

