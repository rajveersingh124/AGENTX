"""
Database module for AGENTX.
Provides persistent storage using SQLite for tasks, notes, daily schedules,
documents, conversation memory, and system activity logs.
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Create and return a database connection with dictionary row access."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize database tables if they do not exist, and seed sample data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'Medium',
        due_date TEXT,
        category TEXT DEFAULT 'Work',
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )
    """)

    # Notes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        summary TEXT,
        key_points TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Schedules Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        title TEXT NOT NULL,
        task_id INTEGER,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'planned',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
    )
    """)

    # Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        content TEXT NOT NULL,
        summary TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Chat History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT DEFAULT 'default',
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        intent TEXT,
        agent_thought TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Activity Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        description TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Check if empty; if so, populate sample demo data
    cursor.execute("SELECT COUNT(*) as count FROM tasks")
    row = cursor.fetchone()
    if row and row["count"] == 0:
        seed_demo_data(conn)

    conn.close()

def seed_demo_data(conn: Optional[sqlite3.Connection] = None) -> None:
    """Populate realistic sample data for presentation and instant exploration."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    cursor = conn.cursor()
    today_str = date.today().isoformat()

    # Sample Tasks
    sample_tasks = [
        ("Prepare AI Project Presentation Slides", "Finalize slides for AGENTX architecture, agent workflow, and live demo.", "High", today_str, "Study", "pending"),
        ("Review Literature on Autonomous AI Agents", "Gather key papers on LLM tool use, ReAct framework, and memory structures.", "Medium", today_str, "Study", "completed"),
        ("Conduct AGENTX End-to-End Test Suite", "Verify task manager, daily planner, document QA, and Groq API connectivity.", "High", today_str, "Work", "pending"),
        ("Draft Executive Summary for Document Assistant", "Complete testing on lecture notes PDF analysis and question answering.", "Low", today_str, "Work", "pending"),
        ("Daily Evening Team Standup Sync", "Review project milestones, demo checklist, and presentation roles.", "Medium", today_str, "Personal", "pending"),
    ]
    for task in sample_tasks:
        cursor.execute("""
            INSERT INTO tasks (title, description, priority, due_date, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, task)

    # Sample Notes
    sample_notes = [
        (
            "Agentic AI Architecture Essentials",
            "An AI Agent is an autonomous entity that perceives its environment, makes decisions, and takes actions through tools to achieve defined goals. Unlike simple chatbots that produce one-shot text, agents incorporate planning, reflection, and external tool execution (such as database queries, schedule organizers, and document search). AGENTX follows a modular ReAct-inspired workflow with explicit intent routing.",
            "AI Agents differ from regular chatbots by employing tool execution, memory, and multi-step planning. AGENTX implements modular ReAct-inspired intent routing.",
            json.dumps(["Autonomous goal pursuit", "ReAct loop: Perception -> Planning -> Tool Execution", "Integrated SQLite persistent memory"]),
            "AI, Architecture, College Project"
        ),
        (
            "Semester Final Project Milestones",
            "Milestone 1: Environment setup and Groq LLM integration. Milestone 2: Relational database schema and persistence layer. Milestone 3: Agent reasoning engine and tool dispatcher. Milestone 4: Streamlit UI/UX design with responsive dark theme. Milestone 5: Presentation rehearsal and demo scenario prep.",
            "Structured milestones spanning backend setup, database design, agent reasoning, and frontend polish for the final presentation.",
            json.dumps(["Milestone 1: LLM Setup", "Milestone 2: SQLite Schema", "Milestone 3: Agent Reasoning", "Milestone 4: Modern UI", "Milestone 5: Presentation Rehearsal"]),
            "Milestones, Presentation, Planning"
        )
    ]
    for note in sample_notes:
        cursor.execute("""
            INSERT INTO notes (title, content, summary, key_points, tags)
            VALUES (?, ?, ?, ?, ?)
        """, note)

    # Sample Today's Schedule
    sample_schedules = [
        (today_str, "09:00 - 10:30 AM", "Morning Focus: Review AGENTX Architecture", "High", "completed"),
        (today_str, "11:00 - 12:30 PM", "Core Dev: Test Agent Intent Routing & Groq Tools", "High", "in_progress"),
        (today_str, "02:00 - 03:30 PM", "Deep Work: Finalize Presentation Slides & UI", "High", "planned"),
        (today_str, "04:30 - 05:30 PM", "Team Review: Dry run live demo scenarios", "Medium", "planned"),
        (today_str, "06:00 - 06:30 PM", "Evening Wrap-up & Daily Reflection", "Low", "planned"),
    ]
    for sched in sample_schedules:
        cursor.execute("""
            INSERT INTO schedules (date, time_slot, title, priority, status)
            VALUES (?, ?, ?, ?, ?)
        """, sched)

    # Sample Document
    sample_doc_content = """# AGENTX Project Overview & System Specification
AGENTX is a cutting-edge AI Personal Assistant designed for modern academic and personal workflows.
It combines Large Language Model reasoning with modular deterministic tools:
1. Smart Task Manager: Natural language task extraction and priority sorting.
2. AI Daily Planner: Automated timetable generation with fatigue prevention.
3. Smart Notes Manager: AI-powered note synthesis and key point extraction.
4. Document Assistant: Context-aware Q&A and instant summarization.
5. Autonomous Agent Workflow: Intent classification, step-by-step planning, tool dispatching, and execution.
All data is stored securely in an SQLite database, ensuring privacy and offline accessibility."""

    cursor.execute("""
        INSERT INTO documents (filename, file_type, content, summary)
        VALUES (?, ?, ?, ?)
    """, (
        "AGENTX_System_Specification.txt",
        "txt",
        sample_doc_content,
        "System specification detailing AGENTX architecture, modular tools, SQLite storage, and Agentic workflow."
    ))

    # Initial Activity Logs
    cursor.execute("""
        INSERT INTO activity_log (action_type, description)
        VALUES ('system_init', 'AGENTX initialized with sample demo dataset.')
    """)
    cursor.execute("""
        INSERT INTO activity_log (action_type, description)
        VALUES ('task_created', 'Created demo task: Prepare AI Project Presentation Slides')
    """)
    cursor.execute("""
        INSERT INTO activity_log (action_type, description)
        VALUES ('schedule_generated', 'Generated AI daily timetable for current date.')
    """)

    conn.commit()
    if close_after:
        conn.close()

# ----------------- Task Operations -----------------

def add_task(title: str, description: str = "", priority: str = "Medium",
             due_date: Optional[str] = None, category: str = "Work") -> int:
    """Add a new task to SQLite and log the activity."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, description, priority, due_date, category, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    """, (title.strip(), description.strip(), priority, due_date, category))
    task_id = cursor.lastrowid
    conn.commit()

    log_activity("task_created", f"Created task: '{title}' [{priority} Priority]")
    conn.close()
    return task_id

def get_tasks(status: Optional[str] = None, priority: Optional[str] = None,
              category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve tasks with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status and status != "All":
        query += " AND status = ?"
        params.append(status.lower())
    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END, id DESC"

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_task_by_id(task_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single task by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_task(task_id: int, **kwargs) -> bool:
    """Update fields of an existing task."""
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    params = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        params.append(v)
    if not fields:
        conn.close()
        return False

    params.append(task_id)
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return True

def toggle_task_status(task_id: int) -> str:
    """Toggle a task between pending and completed."""
    task = get_task_by_id(task_id)
    if not task:
        return "not_found"

    new_status = "completed" if task["status"] == "pending" else "pending"
    completed_at = datetime.now().isoformat() if new_status == "completed" else None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?
    """, (new_status, completed_at, task_id))
    conn.commit()
    conn.close()

    log_activity(
        "task_completed" if new_status == "completed" else "task_reopened",
        f"Marked task '{task['title']}' as {new_status}."
    )
    return new_status

def delete_task(task_id: int) -> bool:
    """Delete a task by ID."""
    task = get_task_by_id(task_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    if task:
        log_activity("task_deleted", f"Deleted task: '{task['title']}'")
    return True

def get_task_statistics() -> Dict[str, Any]:
    """Calculate overall task metrics for the dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM tasks")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as completed FROM tasks WHERE status = 'completed'")
    completed = cursor.fetchone()["completed"]

    cursor.execute("SELECT COUNT(*) as pending FROM tasks WHERE status = 'pending'")
    pending = cursor.fetchone()["pending"]

    cursor.execute("SELECT COUNT(*) as high_priority FROM tasks WHERE status = 'pending' AND priority = 'High'")
    high_priority = cursor.fetchone()["high_priority"]

    conn.close()

    rate = int(round((completed / total * 100))) if total > 0 else 0
    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "high_priority": high_priority,
        "completion_rate": rate
    }

# ----------------- Note Operations -----------------

def add_note(title: str, content: str, summary: str = "",
             key_points: str = "", tags: str = "") -> int:
    """Create a new note."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notes (title, content, summary, key_points, tags)
        VALUES (?, ?, ?, ?, ?)
    """, (title.strip(), content.strip(), summary, key_points, tags))
    note_id = cursor.lastrowid
    conn.commit()

    log_activity("note_created", f"Created note: '{title}'")
    conn.close()
    return note_id

def get_notes(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all notes, optionally filtered by search query."""
    conn = get_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM notes
            WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
            ORDER BY id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM notes ORDER BY id DESC")

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_note_by_id(note_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve note by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_note(note_id: int, **kwargs) -> bool:
    """Update fields of an existing note."""
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    params = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        params.append(v)
    if not fields:
        conn.close()
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(note_id)
    query = f"UPDATE notes SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return True

def delete_note(note_id: int) -> bool:
    """Delete note by ID."""
    note = get_note_by_id(note_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

    if note:
        log_activity("note_deleted", f"Deleted note: '{note['title']}'")
    return True

# ----------------- Schedule Operations -----------------

def add_schedule_item(date_str: str, time_slot: str, title: str,
                      task_id: Optional[int] = None, priority: str = "Medium",
                      status: str = "planned") -> int:
    """Add a schedule entry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO schedules (date, time_slot, title, task_id, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, time_slot, title, task_id, priority, status))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id

def get_schedule_for_date(date_str: str) -> List[Dict[str, Any]]:
    """Fetch timetable for a given date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM schedules WHERE date = ? ORDER BY id ASC
    """, (date_str,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_schedule_item(item_id: int, **kwargs) -> bool:
    """Update a schedule item."""
    conn = get_connection()
    cursor = conn.cursor()
    fields = [f"{k} = ?" for k in kwargs.keys()]
    params = list(kwargs.values()) + [item_id]
    cursor.execute(f"UPDATE schedules SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return True

def delete_schedule_item(item_id: int) -> bool:
    """Delete a schedule item."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return True

def clear_schedule_for_date(date_str: str) -> bool:
    """Clear all schedule items for a given date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE date = ?", (date_str,))
    conn.commit()
    conn.close()
    return True

# ----------------- Document Operations -----------------

def add_document(filename: str, file_type: str, content: str, summary: str = "") -> int:
    """Save an uploaded document to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documents (filename, file_type, content, summary)
        VALUES (?, ?, ?, ?)
    """, (filename, file_type, content, summary))
    doc_id = cursor.lastrowid
    conn.commit()

    log_activity("document_uploaded", f"Uploaded document: '{filename}'")
    conn.close()
    return doc_id

def get_documents() -> List[Dict[str, Any]]:
    """Get all stored documents."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, file_type, summary, uploaded_at, length(content) as char_count FROM documents ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    """Fetch full document content by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_document(doc_id: int) -> bool:
    """Delete a document by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    log_activity("document_deleted", f"Deleted document ID: {doc_id}")
    return True

# ----------------- Chat History -----------------

def save_chat_message(role: str, content: str, session_id: str = "default",
                      intent: str = "", agent_thought: str = "") -> int:
    """Save a chat message with agent thought trace."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, role, content, intent, agent_thought)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, role, content, intent, agent_thought))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def get_chat_history(session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch chat history for a session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM chat_history WHERE session_id = ? ORDER BY id ASC LIMIT ?
    """, (session_id, limit))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def clear_chat_history(session_id: str = "default") -> bool:
    """Clear chat messages."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    return True

# ----------------- Activity Log -----------------

def log_activity(action_type: str, description: str) -> int:
    """Log an application activity."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO activity_log (action_type, description)
        VALUES (?, ?)
    """, (action_type, description))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id

def get_recent_activities(limit: int = 8) -> List[Dict[str, Any]]:
    """Retrieve recent system activities."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM activity_log ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# ----------------- Database Reset -----------------

def reset_database() -> None:
    """Completely reset database and restore clean sample demo dataset."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS tasks")
    cursor.execute("DROP TABLE IF EXISTS notes")
    cursor.execute("DROP TABLE IF EXISTS schedules")
    cursor.execute("DROP TABLE IF EXISTS documents")
    cursor.execute("DROP TABLE IF EXISTS chat_history")
    cursor.execute("DROP TABLE IF EXISTS activity_log")
    conn.commit()
    conn.close()
    init_db()

