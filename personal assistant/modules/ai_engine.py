"""
AI Engine module for AGENTX.
Manages LLM client interactions with Groq (OpenAI-compatible), prompt engineering,
structured JSON response parsing, and graceful Demo Mode fallback.
"""

import json
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from openai import OpenAI
import config

def get_client() -> Optional[OpenAI]:
    """Instantiate an OpenAI client configured for Groq API."""
    api_key = config.get_api_key()
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url=config.get_base_url(),
        timeout=25.0
    )

def query_llm(messages: List[Dict[str, str]], temperature: float = 0.4,
              max_tokens: int = 1500) -> tuple[bool, str]:
    """
    Execute a chat completion with the configured LLM.
    Returns (success: bool, content_or_error: str).
    """
    client = get_client()
    if not client:
        return False, "DEMO_MODE_ACTIVE"

    model = config.get_model()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        content = response.choices[0].message.content
        return True, content or ""
    except Exception as exc:
        return False, f"API Error: {str(exc)}"

def extract_json_from_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Robustly extract and parse a JSON block from LLM output."""
    try:
        # Direct parse attempt
        return json.loads(raw_text.strip())
    except Exception:
        pass

    # Markdown fence extraction ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass

    # Find first '{' and last '}'
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw_text[start:end+1])
        except Exception:
            pass

    # Find first '[' and last ']' for list returns
    start = raw_text.find("[")
    end = raw_text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(raw_text[start:end+1])
            return {"items": parsed}
        except Exception:
            pass

    return None

# ================= Specialized Capabilities =================

def extract_task_from_natural_language(text: str) -> Dict[str, Any]:
    """
    Extract structured task fields (title, priority, due_date, category)
    from natural language user input.
    """
    system_prompt = (
        "You are an AI Task Extraction Specialist. Extract task details from user text.\n"
        "Return ONLY a JSON object with keys:\n"
        "- title (string, clear action-oriented title)\n"
        "- description (string, optional details or empty)\n"
        "- priority (string: 'High', 'Medium', or 'Low')\n"
        "- due_date (string in YYYY-MM-DD format, or 'today', or null)\n"
        "- category (string: 'Work', 'Study', 'Personal', 'Health', 'Finance', 'Other')\n"
        "Never add markdown formatting or explanation outside JSON."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Extract task details from: '{text}'"}
    ]

    success, result = query_llm(messages, temperature=0.1)

    if success:
        parsed = extract_json_from_response(result)
        if parsed and "title" in parsed:
            # Normalize due date if "today"
            if parsed.get("due_date") == "today":
                parsed["due_date"] = date.today().isoformat()
            if parsed.get("priority") not in ["High", "Medium", "Low"]:
                parsed["priority"] = "Medium"
            return parsed

    # Heuristic fallback for Demo Mode or API failure
    return _demo_extract_task(text)

def _demo_extract_task(text: str) -> Dict[str, Any]:
    """Smart heuristic task parser for offline / Demo Mode."""
    clean = text.lower()
    priority = "Medium"
    if any(w in clean for w in ["urgent", "high", "asap", "critical", "important"]):
        priority = "High"
    elif any(w in clean for w in ["low", "minor", "someday", "later"]):
        priority = "Low"

    category = "Work"
    if any(w in clean for w in ["study", "exam", "assignment", "homework", "lecture", "college"]):
        category = "Study"
    elif any(w in clean for w in ["gym", "workout", "doctor", "health", "meditation"]):
        category = "Health"
    elif any(w in clean for w in ["buy", "bill", "pay", "money", "finance", "bank"]):
        category = "Finance"
    elif any(w in clean for w in ["family", "call", "friend", "groceries", "home"]):
        category = "Personal"

    # Remove triggers like "add task:", "create task:", "remind me to"
    title = re.sub(r"^(please\s+)?(add\s+task|create\s+task|remind\s+me\s+to|todo:?)\s*", "", text, flags=re.IGNORECASE).strip()
    if not title:
        title = text.strip()

    return {
        "title": title.capitalize(),
        "description": "Created via natural language command",
        "priority": priority,
        "due_date": date.today().isoformat(),
        "category": category
    }

def generate_schedule_from_tasks(tasks: List[Dict[str, Any]], target_date: str) -> List[Dict[str, Any]]:
    """
    Generate an intelligent, time-blocked daily schedule from pending tasks.
    Prioritizes high-priority items and prevents cognitive fatigue.
    """
    if not tasks:
        # Default smart schedule template
        return [
            {"time_slot": "09:00 - 10:30 AM", "title": "Deep Work: Top Priority Focus", "priority": "High"},
            {"time_slot": "11:00 - 12:30 PM", "title": "Project Execution & Research", "priority": "Medium"},
            {"time_slot": "02:00 - 03:30 PM", "title": "Collaborative Tasks & Syncs", "priority": "Medium"},
            {"time_slot": "04:30 - 05:30 PM", "title": "Administrative Work & Planning", "priority": "Low"},
        ]

    tasks_summary = "\n".join([f"- ID {t['id']}: {t['title']} (Priority: {t['priority']}, Cat: {t['category']})" for t in tasks])

    system_prompt = (
        "You are an AI Daily Productivity Planner. Create a realistic, high-impact daily timetable.\n"
        "Allocate pending tasks into logical 60-90 minute time blocks starting from 09:00 AM.\n"
        "Reserve earlier blocks for High priority tasks.\n"
        "Return ONLY a JSON array of objects with keys:\n"
        "- time_slot (e.g. '09:00 - 10:30 AM')\n"
        "- title (concise block name incorporating task title)\n"
        "- task_id (integer ID or null)\n"
        "- priority ('High', 'Medium', or 'Low')\n"
        "Do not include any other markdown text."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Target Date: {target_date}\nPending Tasks:\n{tasks_summary}"}
    ]

    success, result = query_llm(messages, temperature=0.3)
    if success:
        parsed = extract_json_from_response(result)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "items" in parsed and isinstance(parsed["items"], list):
            return parsed["items"]

    # Demo Mode Fallback: Heuristically build schedule
    slots = ["09:00 - 10:30 AM", "11:00 - 12:30 PM", "02:00 - 03:30 PM", "04:00 - 05:00 PM", "05:30 - 06:30 PM"]
    schedule = []
    # Sort tasks: High first, then Medium, then Low
    sorted_tasks = sorted(tasks, key=lambda t: 0 if t["priority"]=="High" else (1 if t["priority"]=="Medium" else 2))
    for i, t in enumerate(sorted_tasks[:len(slots)]):
        schedule.append({
            "time_slot": slots[i],
            "title": f"Focus: {t['title']}",
            "task_id": t["id"],
            "priority": t["priority"]
        })
    return schedule

def summarize_text_content(title: str, text: str) -> Dict[str, Any]:
    """
    Summarize a note or text document and extract 3-5 key takeaway points.
    """
    system_prompt = (
        "You are an Executive AI Synthesizer. Summarize the provided text clearly and extract key points.\n"
        "Return ONLY a JSON object with:\n"
        "- summary (2-3 sentences concise summary)\n"
        "- key_points (list of 3-5 actionable bullet points as strings)\n"
        "No outside commentary."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Title: {title}\nText Content:\n{text[:4000]}"}
    ]

    success, result = query_llm(messages, temperature=0.3)
    if success:
        parsed = extract_json_from_response(result)
        if parsed and "summary" in parsed and "key_points" in parsed:
            return parsed

    # Demo fallback
    words = text.split()
    first_chunk = " ".join(words[:45])
    return {
        "summary": f"{title}: {first_chunk}... (Synthesized in Demo Mode)",
        "key_points": [
            "Core concept outlined in the primary section.",
            "Actionable insights regarding methodology and structure.",
            "Key recommendations for subsequent execution."
        ]
    }

def answer_document_question(doc_name: str, doc_content: str, question: str) -> str:
    """
    Answer a user question based on document content.
    """
    system_prompt = (
        f"You are the AGENTX Document Assistant analyzing '{doc_name}'.\n"
        "Answer the user's question accurately based STRICTLY on the document context below.\n"
        "If the document doesn't contain the answer, state that honestly.\n"
        "Be concise, clear, and highlight relevant citations or facts."
    )

    # Context window management
    context = doc_content[:6000]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Document Context:\n{context}\n\nQuestion: {question}"}
    ]

    success, result = query_llm(messages, temperature=0.2)
    if success:
        return result

    # Demo fallback
    return (
        f"*(Demo Mode Response)* Based on '{doc_name}', the document highlights key architectural principles "
        f"and structured workflows relevant to your question: '{question}'.\n\n"
        f"Key excerpt: {doc_content[:180]}..."
    )

def generate_productivity_report(stats: Dict[str, Any], pending_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate an insightful daily productivity assessment, next best action, and motivational boost.
    """
    total = stats.get("total", 0)
    completed = stats.get("completed", 0)
    rate = stats.get("completion_rate", 0)
    high_count = stats.get("high_priority", 0)

    task_sample = ", ".join([t["title"] for t in pending_tasks[:3]]) if pending_tasks else "None"

    system_prompt = (
        "You are an elite AI Productivity Coach. Analyze the user's progress.\n"
        "Return ONLY a JSON object with:\n"
        "- assessment (2 sentences analyzing current momentum and completion rate)\n"
        "- next_best_action (1 concrete recommended immediate step)\n"
        "- motivational_quote (inspiring, high-performance quote)\n"
        "No additional text."
    )

    user_msg = (
        f"User Statistics: Total Tasks={total}, Completed={completed}, Completion Rate={rate}%.\n"
        f"High Priority Pending={high_count}.\n"
        f"Top Pending Tasks: {task_sample}."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]

    success, result = query_llm(messages, temperature=0.5)
    if success:
        parsed = extract_json_from_response(result)
        if parsed and "assessment" in parsed:
            return parsed

    # Demo Fallback
    if rate >= 70:
        tone = "Outstanding momentum! You have conquered the majority of your milestones."
        action = "Review upcoming schedules and celebrate your wins."
    elif rate >= 40:
        tone = f"Steady progress at {rate}%. High-impact focus will push you across the finish line."
        action = f"Tackle the highest priority task: '{pending_tasks[0]['title']}'" if pending_tasks else "Keep planning."
    else:
        tone = "The day is still yours to win. Focus on one critical task at a time."
        action = f"Begin a 25-minute Pomodoro block on: '{pending_tasks[0]['title']}'" if pending_tasks else "Create your top 3 tasks."

    return {
        "assessment": tone,
        "next_best_action": action,
        "motivational_quote": "“Focus is a muscle. The more you eliminate distractions, the stronger your momentum becomes.”"
    }

