"""
Task Manager module for AGENTX.
Handles task creation, editing, natural language extraction, filtering, and metrics.
"""

from typing import Any, Dict, List, Optional
from datetime import date
from modules import database
from modules import ai_engine

def create_task_from_nl(user_prompt: str) -> Dict[str, Any]:
    """
    Parse a user prompt using AI and add the extracted task into SQLite.
    Returns the created task record.
    """
    extracted = ai_engine.extract_task_from_natural_language(user_prompt)
    title = extracted.get("title", user_prompt)
    desc = extracted.get("description", "")
    priority = extracted.get("priority", "Medium")
    due_date = extracted.get("due_date", date.today().isoformat())
    category = extracted.get("category", "Work")

    task_id = database.add_task(
        title=title,
        description=desc,
        priority=priority,
        due_date=due_date,
        category=category
    )

    return database.get_task_by_id(task_id) or {
        "id": task_id,
        "title": title,
        "priority": priority,
        "due_date": due_date,
        "category": category,
        "status": "pending"
    }

def create_manual_task(title: str, description: str = "", priority: str = "Medium",
                       due_date: Optional[str] = None, category: str = "Work") -> int:
    """Create a task with explicitly provided parameters."""
    if not due_date:
        due_date = date.today().isoformat()
    return database.add_task(title, description, priority, due_date, category)

def get_tasks(status: Optional[str] = None, priority: Optional[str] = None,
              category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve filtered tasks."""
    return database.get_tasks(status=status, priority=priority, category=category, search=search)

def toggle_status(task_id: int) -> str:
    """Toggle a task between pending and completed."""
    return database.toggle_task_status(task_id)

def delete_task(task_id: int) -> bool:
    """Delete a task."""
    return database.delete_task(task_id)

def update_task(task_id: int, **kwargs) -> bool:
    """Update task fields."""
    return database.update_task(task_id, **kwargs)

def get_metrics() -> Dict[str, Any]:
    """Fetch task completion statistics."""
    return database.get_task_statistics()

