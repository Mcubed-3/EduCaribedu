from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()

ACTIVITY_LABELS = {
    "mixed_quiz": "Mixed Quiz",
    "mcq": "Multiple Choice Quiz",
    "short_answer": "Short Answer Questions",
    "essay": "Essay Questions",
    "math_problem_solving": "Math Problem-Solving Worksheet",
    "case_study": "Case Study Worksheet",
    "exit_ticket": "Exit Ticket",
    "homework_sheet": "Homework Sheet",
}


def _extract_lesson_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    lesson_payload = payload.get("lesson_payload")

    if lesson_payload and isinstance(lesson_payload, dict):
        lesson = lesson_payload.get("lesson", {})

        return {
            "curriculum": lesson.get("curriculum", ""),
            "subject": lesson.get("subject", ""),
            "grade_level": lesson.get("grade_level", ""),
            "topic": lesson.get("topic", ""),
            "objectives": lesson.get("objectives", []),
            "sections": lesson.get("sections", {}),
        }

    return {
        "curriculum": payload.get("curriculum", ""),
        "subject": payload.get("subject", ""),
        "grade_level": payload.get("grade_level", ""),
        "topic": payload.get("topic", ""),
        "objectives": [],
        "sections": {},
    }


PROMPT_TEMPLATE = """
You are generating a classroom activity STRICTLY aligned to the lesson provided.

CRITICAL RULES:
- ONLY generate content related to the lesson topic
- DO NOT include unrelated subjects
- ALL questions must directly match the lesson content
- Use the objectives and lesson sections to guide the activity
- If include_mark_scheme is false, DO NOT return any mark scheme
- DO NOT return teacher notes
- DO NOT include a teacher notes section in any form

Return ONLY valid JSON:

{
  "title": "string",
  "student_instructions": ["string"],
  "worksheet_items": ["string"],
  "answer_key": ["string"]
}

If include_mark_scheme is true, you may also include:
{
  "mark_scheme": ["string"]
}

Lesson Details:
Subject: {subject}
Topic: {topic}
Grade: {grade_level}
Curriculum: {curriculum}

Objectives:
{objectives}

Lesson Sections:
{sections}

Activity Type: {activity_type}
Number of items: {count}
Include answer key: {include_answer_key}
Include mark scheme: {include_mark_scheme}

Make it:
- Relevant to Caribbean context where possible
- Appropriate for the grade level
- Practical and classroom-ready
""".strip()


def _to_text(data: Dict[str, Any], include_mark_scheme: bool) -> str:
    lines: List[str] = []

    lines.append(data.get("title", "Activity"))
    lines.append("")

    if data.get("student_instructions"):
        lines.append("Student Instructions:")
        for i in data["student_instructions"]:
          lines.append(f"- {i}")
        lines.append("")

    if data.get("worksheet_items"):
        lines.append("Activity:")
        for item in data["worksheet_items"]:
            lines.append(str(item))
        lines.append("")

    if data.get("answer_key"):
        lines.append("Answer Key:")
        for i in data["answer_key"]:
            lines.append(f"- {i}")
        lines.append("")

    if include_mark_scheme and data.get("mark_scheme"):
        lines.append("Mark Scheme:")
        for i in data["mark_scheme"]:
            lines.append(f"- {i}")

    return "\n".join(lines).strip()


def generate_activity(payload: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _extract_lesson_context(payload)

    activity_type = payload["activity_type"]
    count = payload.get("item_count", 8)
    include_answer_key = bool(payload.get("include_answer_key", True))
    include_mark_scheme = bool(payload.get("include_mark_scheme", False))

    title = f"{ACTIVITY_LABELS.get(activity_type, 'Activity')} - {ctx['topic']}"

    if not OPENAI_API_KEY:
        return {
            "title": title,
            "activity_type": activity_type,
            "content": f"Fallback activity for {ctx['topic']}",
            "lesson_snippet": "",
            "raw": {},
        }

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = PROMPT_TEMPLATE.format(
        subject=ctx["subject"],
        topic=ctx["topic"],
        grade_level=ctx["grade_level"],
        curriculum=ctx["curriculum"],
        objectives="\n".join(f"- {o}" for o in ctx["objectives"]),
        sections=json.dumps(ctx["sections"], indent=2),
        activity_type=ACTIVITY_LABELS.get(activity_type, activity_type),
        count=count,
        include_answer_key="yes" if include_answer_key else "no",
        include_mark_scheme="yes" if include_mark_scheme else "no",
    )

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
    )

    raw_text = getattr(response, "output_text", "").strip()

    try:
        data = json.loads(raw_text)
    except Exception:
        data = {
            "title": title,
            "student_instructions": ["Complete the activity below."],
            "worksheet_items": [raw_text],
            "answer_key": [],
        }

    data.pop("teacher_notes", None)

    if not include_mark_scheme and "mark_scheme" in data:
        data.pop("mark_scheme", None)

    return {
        "title": data.get("title", title),
        "activity_type": activity_type,
        "content": _to_text(data, include_mark_scheme=include_mark_scheme),
        "lesson_snippet": "",
        "raw": data,
    }