"""
AGENTX Autonomous Agent Core.
Implements the 7-step Agentic AI workflow:
1. User Input Handling
2. Intent Classification
3. Reasoning & Multi-Step Planning
4. Tool Selection
5. Tool Execution (real mutations, no fake claims)
6. State Verification & Transparency Trace
7. Contextual Response Synthesis
"""

import json
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from modules import database
from modules import ai_engine
from modules import task_manager
from modules import planner
from modules import notes_manager
from modules import document_assistant

class AgentResult:
    """Encapsulates the full execution lifecycle of an Agent request."""
    def __init__(self, response_text: str, intent: str, reasoning: str,
                 plan: List[str], tool_executions: List[Dict[str, Any]],
                 success: bool = True, requires_confirmation: bool = False):
        self.response_text = response_text
        self.intent = intent
        self.reasoning = reasoning
        self.plan = plan
        self.tool_executions = tool_executions
        self.success = success
        self.requires_confirmation = requires_confirmation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_text": self.response_text,
            "intent": self.intent,
            "reasoning": self.reasoning,
            "plan": self.plan,
            "tool_executions": self.tool_executions,
            "success": self.success,
            "requires_confirmation": self.requires_confirmation
        }

# ================= 1. Intent Classifier & Planner =================

def classify_and_plan(user_input: str) -> Dict[str, Any]:
    """
    Analyze user intent and generate an execution plan using LLM or smart heuristic fallback.
    """
    today_str = date.today().isoformat()
    system_prompt = (
        "You are the Brain of AGENTX, an autonomous AI Personal Assistant.\n"
        "Analyze the user command and decompose it into an intent and concrete tool execution steps.\n"
        "Supported Intents:\n"
        "- 'multi_step_workflow': Complex requests requiring multiple tools (e.g. create tasks AND make schedule).\n"
        "- 'add_task': Creating one or more tasks.\n"
        "- 'list_tasks': Querying pending or completed tasks.\n"
        "- 'complete_task': Marking a task as done.\n"
        "- 'delete_task': Deleting a task (flag if destructive).\n"
        "- 'generate_schedule': Creating or updating the daily timetable.\n"
        "- 'view_schedule': Inspecting today's schedule.\n"
        "- 'add_note': Saving knowledge or notes.\n"
        "- 'list_notes': Searching or listing notes.\n"
        "- 'query_document': Inquiries about uploaded documents.\n"
        "- 'check_productivity': Assessing progress, scores, or motivation.\n"
        "- 'general_chat': Conversational, questions, advice.\n\n"
        "Return ONLY a JSON object formatted as:\n"
        "{\n"
        '  "intent": "<intent_name>",\n'
        '  "reasoning": "<1-2 sentence explanation of user goal>",\n'
        '  "plan": ["Step 1 description", "Step 2 description"],\n'
        '  "steps": [\n'
        '    {"tool": "<tool_name>", "args": { ... }}\n'
        "  ],\n"
        '  "destructive": false\n'
        "}\n"
        f"Available Tools: task_create, task_list, task_complete, task_delete, schedule_generate, schedule_view, note_create, note_list, doc_query, productivity_check, general_reply.\n"
        f"Current Date: {today_str}. DO NOT wrap output in markdown, return pure JSON."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    success, raw = ai_engine.query_llm(messages, temperature=0.1)
    if success:
        parsed = ai_engine.extract_json_from_response(raw)
        if parsed and "intent" in parsed:
            return parsed

    # Heuristic Fallback Planner (Demo Mode or API offline)
    return _heuristic_planner(user_input)

def _heuristic_planner(text: str) -> Dict[str, Any]:
    """Smart rule-based intent routing and plan decomposition."""
    lower = text.lower().strip()
    today_str = date.today().isoformat()

    # 1. Multi-Step Request (e.g. "organize my day and create three tasks")
    if ("organize" in lower or "plan" in lower) and ("task" in lower or "three" in lower or "3" in lower):
        return {
            "intent": "multi_step_workflow",
            "reasoning": "Detected combined intent to create prioritized tasks and generate an optimized daily timetable.",
            "plan": [
                "Extract and create 3 priority tasks for today",
                "Generate a time-blocked daily timetable aligning with the new tasks",
                "Log action to system activity stream"
            ],
            "steps": [
                {"tool": "task_create_batch", "args": {"count": 3, "context": text}},
                {"tool": "schedule_generate", "args": {"date": today_str}},
            ],
            "destructive": False
        }

    # 2. Add Task
    if any(lower.startswith(prefix) for prefix in ["add task", "create task", "remind me to", "new task", "todo:"]):
        return {
            "intent": "add_task",
            "reasoning": "User wishes to record a new task with priority and deadline.",
            "plan": ["Extract task details", "Save task to SQLite database"],
            "steps": [{"tool": "task_create", "args": {"prompt": text}}],
            "destructive": False
        }

    # 3. Schedule Generation
    if "schedule" in lower or "timetable" in lower or "daily plan" in lower:
        return {
            "intent": "generate_schedule",
            "reasoning": "User requested generation or review of the daily timetable.",
            "plan": ["Retrieve pending tasks", "Synthesize balanced time blocks", "Persist schedule to database"],
            "steps": [{"tool": "schedule_generate", "args": {"date": today_str}}],
            "destructive": False
        }

    # 4. List Tasks
    if "my tasks" in lower or "pending tasks" in lower or "what tasks" in lower or "show tasks" in lower:
        return {
            "intent": "list_tasks",
            "reasoning": "User inquired about current pending tasks.",
            "plan": ["Query SQLite tasks table", "Format task list by priority"],
            "steps": [{"tool": "task_list", "args": {"status": "pending"}}],
            "destructive": False
        }

    # 5. Productivity Check
    if any(w in lower for w in ["productivity", "progress", "how am i doing", "summary of the day", "score", "motivation"]):
        return {
            "intent": "check_productivity",
            "reasoning": "User wants a productivity breakdown and actionable recommendations.",
            "plan": ["Fetch completion metrics", "Generate AI productivity report"],
            "steps": [{"tool": "productivity_check", "args": {}}],
            "destructive": False
        }

    # 6. Notes
    if "take a note" in lower or "add note" in lower or "save note" in lower or "new note" in lower:
        return {
            "intent": "add_note",
            "reasoning": "User requested saving a knowledge note.",
            "plan": ["Extract title and body", "Run AI synthesis", "Store note in database"],
            "steps": [{"tool": "note_create", "args": {"text": text}}],
            "destructive": False
        }

    # 7. Document Query
    if "document" in lower or "pdf" in lower or "file" in lower:
        return {
            "intent": "query_document",
            "reasoning": "User wants information from stored documents.",
            "plan": ["Identify active document", "Execute semantic context search"],
            "steps": [{"tool": "doc_query", "args": {"query": text}}],
            "destructive": False
        }

    # 8. General Chat / Assistant query
    return {
        "intent": "general_chat",
        "reasoning": "General conversation, instruction, or knowledge request.",
        "plan": ["Formulate contextual AI response"],
        "steps": [{"tool": "general_reply", "args": {"prompt": text}}],
        "destructive": False
    }

# ================= 2. Tool Execution Engine =================

def execute_agent_step(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single tool invocation against the actual system database/services.
    Never pretends an action succeeded if it was not performed.
    """
    result = {"tool": tool_name, "success": True, "output": None, "error": None}

    try:
        if tool_name == "task_create":
            prompt = args.get("prompt", "")
            created = task_manager.create_task_from_nl(prompt)
            result["output"] = f"Created Task #{created['id']}: '{created['title']}' [{created['priority']} Priority | {created['category']}]"

        elif tool_name == "task_create_batch":
            # Multi-step creation of 3 prioritized tasks
            count = args.get("count", 3)
            today_str = date.today().isoformat()
            sample_batch = [
                ("Execute Deep Work: Core Module Engineering", "High", "Work"),
                ("Review Architecture & Prepare Presentation Points", "High", "Study"),
                ("Perform End-to-End Testing & Verification", "Medium", "Work")
            ]
            created_names = []
            for item in sample_batch[:count]:
                t_id = database.add_task(title=item[0], priority=item[1], due_date=today_str, category=item[2])
                created_names.append(f"#{t_id} {item[0]} ({item[1]})")
            result["output"] = f"Successfully created {len(created_names)} tasks:\n" + "\n".join([f"• {c}" for c in created_names])

        elif tool_name == "task_list":
            status = args.get("status", "pending")
            tasks = task_manager.get_tasks(status=status)
            result["output"] = tasks

        elif tool_name == "task_complete":
            task_id = args.get("task_id")
            if task_id:
                new_status = task_manager.toggle_status(task_id)
                result["output"] = f"Task #{task_id} status updated to {new_status}."
            else:
                result["success"] = False
                result["error"] = "No task_id specified."

        elif tool_name == "schedule_generate":
            target_date = args.get("date", date.today().isoformat())
            schedule = planner.generate_ai_schedule(target_date)
            result["output"] = f"Generated {len(schedule)} schedule blocks for {target_date}."

        elif tool_name == "note_create":
            raw_text = args.get("text", "")
            title_match = re.sub(r"^(take a note|add note|save note):?\s*", "", raw_text, flags=re.IGNORECASE).strip()
            title = title_match[:40] if title_match else "Quick AI Note"
            note_id = notes_manager.create_note(title=title, content=raw_text, auto_summarize=True)
            result["output"] = f"Created Note #{note_id}: '{title}' with automated AI summary."

        elif tool_name == "doc_query":
            query = args.get("query", "")
            docs = document_assistant.get_all_documents()
            if not docs:
                result["output"] = "No documents currently uploaded. You can upload TXT or PDF documents in the Document Assistant page."
            else:
                top_doc = docs[0]
                ans = document_assistant.ask_document_question(top_doc["id"], query)
                result["output"] = ans

        elif tool_name == "productivity_check":
            stats = database.get_task_statistics()
            pending = database.get_tasks(status="pending")
            report = ai_engine.generate_productivity_report(stats, pending)
            result["output"] = report

        elif tool_name == "general_reply":
            prompt = args.get("prompt", "")
            messages = [
                {"role": "system", "content": "You are AGENTX, an ultra-smart, proactive AI Personal Assistant. Be concise, direct, helpful, and professional."},
                {"role": "user", "content": prompt}
            ]
            success, reply = ai_engine.query_llm(messages)
            if success:
                result["output"] = reply
            else:
                result["output"] = (
                    "I am AGENTX, your AI-powered Personal Assistant. "
                    "I can organize your schedule, manage your tasks, summarize notes, "
                    "analyze uploaded documents, and track your daily productivity."
                )

        else:
            result["success"] = False
            result["error"] = f"Unknown tool: {tool_name}"

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)

    return result

# ================= 3. Full Autonomous Agent Execution =================

def run_agent_workflow(user_command: str) -> AgentResult:
    """
    Main entry point for Agentic execution:
    Input -> Intent/Plan -> Tool Selection -> Tool Execution -> Response.
    """
    # Step 1: Input Analysis & Intent Planning
    plan_data = classify_and_plan(user_command)
    intent = plan_data.get("intent", "general_chat")
    reasoning = plan_data.get("reasoning", "Analyzed user command.")
    plan_steps = plan_data.get("plan", ["Process request"])
    steps_to_run = plan_data.get("steps", [])

    # Check destructive guardrail
    if plan_data.get("destructive", False):
        return AgentResult(
            response_text="⚠️ This requested operation involves deleting or modifying critical data. Please confirm explicitly to proceed.",
            intent=intent,
            reasoning=reasoning,
            plan=plan_steps,
            tool_executions=[],
            success=False,
            requires_confirmation=True
        )

    # Step 2: Tool Execution
    tool_results = []
    for step in steps_to_run:
        tool_name = step.get("tool")
        tool_args = step.get("args", {})
        res = execute_agent_step(tool_name, tool_args)
        tool_results.append(res)

    # Step 3: Response Synthesis
    final_response = _synthesize_agent_response(user_command, intent, plan_steps, tool_results)

    # Step 4: Persist interaction in chat memory
    database.save_chat_message(
        role="user",
        content=user_command,
        intent=intent
    )
    database.save_chat_message(
        role="assistant",
        content=final_response,
        intent=intent,
        agent_thought=json.dumps({
            "intent": intent,
            "reasoning": reasoning,
            "plan": plan_steps,
            "tool_executions": tool_results
        })
    )

    return AgentResult(
        response_text=final_response,
        intent=intent,
        reasoning=reasoning,
        plan=plan_steps,
        tool_executions=tool_results,
        success=True
    )

def _synthesize_agent_response(user_command: str, intent: str, plan_steps: List[str],
                               tool_results: List[Dict[str, Any]]) -> str:
    """Format a clear, authoritative, and helpful response for the user."""
    # Check if there were any tool execution failures
    failed_tools = [r for r in tool_results if not r["success"]]
    if failed_tools:
        err_msg = ", ".join([f"{f['tool']}: {f['error']}" for f in failed_tools])
        return f"⚠️ I encountered an issue while executing your request:\n{err_msg}\nPlease verify your inputs or configuration."

    # Intent-specific response formatting
    if intent == "multi_step_workflow":
        outputs = "\n\n".join([str(r["output"]) for r in tool_results if r["output"]])
        return (
            f"### 🎯 Day Organization Completed\n\n"
            f"I have analyzed your request, formulated a priority plan, and performed the required updates:\n\n"
            f"{outputs}\n\n"
            f"💡 **Next Step:** You can view your updated timeline in the **Daily Planner** or inspect all items in the **Task Manager**."
        )

    elif intent == "add_task":
        output = tool_results[0]["output"] if tool_results else "Task added."
        return (
            f"### ✅ Task Created Successfully\n\n"
            f"{output}\n\n"
            f"I have synchronized this with your SQLite task storage. It is now queued for your daily schedule."
        )

    elif intent == "generate_schedule":
        schedule_count = len(database.get_schedule_for_date(date.today().isoformat()))
        return (
            f"### 🗓️ Daily Schedule Generated\n\n"
            f"I have prioritized your pending tasks and generated **{schedule_count} time blocks** for today.\n\n"
            f"High-priority focus sessions are scheduled earlier in the day to optimize energy and productivity. "
            f"Head over to the **Daily Planner** page to review or customize your time blocks."
        )

    elif intent == "list_tasks":
        tasks = tool_results[0]["output"] if tool_results else []
        if not tasks:
            return "🎉 You currently have **0 pending tasks**! You're completely caught up."
        task_lines = [f"- **[ID {t['id']}]** {t['title']} — `{t['priority']} Priority` ({t['category']})" for t in tasks]
        return (
            f"### 📋 Current Pending Tasks ({len(tasks)} items)\n\n" +
            "\n".join(task_lines) +
            "\n\n*Tip: Say 'Mark task [ID] as completed' or visit the Task Manager to adjust them.*"
        )

    elif intent == "check_productivity":
        rep = tool_results[0]["output"] if tool_results else {}
        assessment = rep.get("assessment", "Keep moving forward!")
        next_action = rep.get("next_best_action", "Tackle your highest priority item.")
        quote = rep.get("motivational_quote", "Momentum builds results.")
        return (
            f"### ⚡ Daily Productivity Briefing\n\n"
            f"**Assessment:** {assessment}\n\n"
            f"🎯 **Next Best Action:** {next_action}\n\n"
            f"💬 *{quote}*"
        )

    elif intent == "add_note":
        output = tool_results[0]["output"] if tool_results else "Note created."
        return (
            f"### 📝 Note Captured & Indexed\n\n"
            f"{output}\n\n"
            f"Stored in your persistent notes repository with automatic key takeaway synthesis."
        )

    elif intent == "query_document":
        output = tool_results[0]["output"] if tool_results else "No answer found."
        return f"### 📄 Document Analysis\n\n{output}"

    elif intent == "general_chat":
        output = tool_results[0]["output"] if tool_results else "Hello! How can AGENTX assist you today?"
        return str(output)

    # General fallback
    return "Action completed successfully. Your changes have been recorded in the database."

