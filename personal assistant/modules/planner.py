"""
AI Daily Planner module for AGENTX.
Generates structured time-blocked schedules, organizes daily activities by priority,
and allows user timetable adjustments.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from modules import database
from modules import ai_engine

def generate_ai_schedule(target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate an optimized daily schedule from currently pending tasks
    and store it in the database.
    """
    if not target_date:
        target_date = date.today().isoformat()

    # Get pending tasks
    pending_tasks = database.get_tasks(status="pending")

    # Generate timetable through AI Engine
    time_blocks = ai_engine.generate_schedule_from_tasks(pending_tasks, target_date)

    # Clear existing schedule for this date to avoid duplicate clutter
    database.clear_schedule_for_date(target_date)

    # Persist the newly generated schedule
    for block in time_blocks:
        database.add_schedule_item(
            date_str=target_date,
            time_slot=block.get("time_slot", "09:00 AM"),
            title=block.get("title", "Focus Session"),
            task_id=block.get("task_id"),
            priority=block.get("priority", "Medium"),
            status="planned"
        )

    database.log_activity("schedule_generated", f"Generated AI timetable with {len(time_blocks)} blocks for {target_date}.")
    return database.get_schedule_for_date(target_date)

def get_schedule(target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch timetable for given date."""
    if not target_date:
        target_date = date.today().isoformat()
    return database.get_schedule_for_date(target_date)

def add_schedule_slot(date_str: str, time_slot: str, title: str,
                      priority: str = "Medium", status: str = "planned") -> int:
    """Manually add an item to the timetable."""
    return database.add_schedule_item(
        date_str=date_str,
        time_slot=time_slot,
        title=title,
        priority=priority,
        status=status
    )

def update_slot_status(slot_id: int, new_status: str) -> bool:
    """Update status of a schedule slot (planned, in_progress, completed)."""
    return database.update_schedule_item(slot_id, status=new_status)

def delete_slot(slot_id: int) -> bool:
    """Delete a schedule item."""
    return database.delete_schedule_item(slot_id)

def clear_day(date_str: str) -> bool:
    """Clear all items for a day."""
    return database.clear_schedule_for_date(date_str)

