"""
Notes Manager module for AGENTX.
Supports note creation, storage, search, tags, AI summarization,
and key takeaway extraction.
"""

import json
from typing import Any, Dict, List, Optional
from modules import database
from modules import ai_engine

def create_note(title: str, content: str, tags: str = "", auto_summarize: bool = False) -> int:
    """
    Create a new note. If auto_summarize is True, runs AI synthesis
    to produce summary and key points automatically.
    """
    summary = ""
    key_points_json = ""

    if auto_summarize and content.strip():
        synthesis = ai_engine.summarize_text_content(title, content)
        summary = synthesis.get("summary", "")
        key_points_json = json.dumps(synthesis.get("key_points", []))

    return database.add_note(
        title=title,
        content=content,
        summary=summary,
        key_points=key_points_json,
        tags=tags
    )

def synthesize_note(note_id: int) -> Dict[str, Any]:
    """
    Run AI summarization on an existing note and persist the results.
    """
    note = database.get_note_by_id(note_id)
    if not note:
        return {"success": False, "error": "Note not found"}

    synthesis = ai_engine.summarize_text_content(note["title"], note["content"])
    summary = synthesis.get("summary", "")
    key_points = json.dumps(synthesis.get("key_points", []))

    database.update_note(note_id, summary=summary, key_points=key_points)
    database.log_activity("note_summarized", f"AI synthesized note: '{note['title']}'")

    return {
        "success": True,
        "summary": summary,
        "key_points": synthesis.get("key_points", [])
    }

def get_all_notes(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve notes with search support."""
    notes = database.get_notes(search=search)
    # Parse key points JSON safely
    for n in notes:
        try:
            n["parsed_key_points"] = json.loads(n["key_points"]) if n.get("key_points") else []
        except Exception:
            n["parsed_key_points"] = []
    return notes

def update_note_content(note_id: int, title: str, content: str, tags: str) -> bool:
    """Update title, content, or tags of a note."""
    return database.update_note(note_id, title=title, content=content, tags=tags)

def delete_note(note_id: int) -> bool:
    """Delete a note."""
    return database.delete_note(note_id)

