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
            "difficulty": lesson.get("difficulty", ""),
            "objectives": lesson.get("objectives", []),
            "sections": lesson.get("sections", {}),
            "mode": "lesson",
        }

    return {
        "curriculum": payload.get("curriculum", ""),
        "subject": payload.get("subject", ""),
        "grade_level": payload.get("grade_level", ""),
        "topic": payload.get("topic", ""),
        "difficulty": payload.get("difficulty", ""),
        "objectives": [],
        "sections": {},
        "mode": "standalone",
    }


PROMPT_TEMPLATE = r"""
You are generating a classroom activity STRICTLY aligned to the teaching context provided.

CRITICAL RULES:
- ONLY generate content related to the subject and topic provided
- DO NOT include unrelated subjects
- If lesson objectives and lesson sections are provided, use them directly
- If no lesson is provided, generate an original standalone activity aligned to the curriculum, subject, grade level, difficulty, and topic
- If include_mark_scheme is false, DO NOT return any mark scheme
- DO NOT return teacher notes
- DO NOT include a teacher notes section in any form
- For ALL mathematics, use LaTeX delimiters
- Inline maths must use \( ... \)
- Display maths must use \[ ... \]
- Fractions must use \frac{a}{b}
- Powers must use x^2 or x^{10}
- Square roots must use \sqrt{x}

Return ONLY valid JSON:

{{
  "title": "string",
  "student_instructions": ["string"],
  "worksheet_items": ["string"],
  "answer_key": ["string"]
}}

If include_mark_scheme is true, you may also include:
{{
  "mark_scheme": ["string"]
}}

Activity Context:
Mode: {mode}
Curriculum: {curriculum}
Subject: {subject}
Grade: {grade_level}
Topic: {topic}
Difficulty: {difficulty}

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
- Original in wording
""".strip()


def _fallback_activity(ctx: Dict[str, Any], activity_type: str, count: int, include_answer_key: bool, include_mark_scheme: bool) -> Dict[str, Any]:
    topic = ctx.get("topic", "the topic")
    subject = ctx.get("subject", "the subject")
    grade_level = ctx.get("grade_level", "the selected grade")
    title = f"{ACTIVITY_LABELS.get(activity_type, 'Activity')} - {topic}"

    items = []
    answers = []
    mark_scheme = []

    if activity_type == "mcq":
        for i in range(1, count + 1):
            items.append(
                f"{i}. Multiple choice: Which statement best relates to {topic} in {subject} for {grade_level}?\n"
                f"   A. Unrelated idea\n"
                f"   B. Core idea about {topic}\n"
                f"   C. Incorrect detail\n"
                f"   D. Random option"
            )
            if include_answer_key:
                answers.append(f"{i}. B")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. 1 mark for selecting the correct option.")
    else:
        for i in range(1, count + 1):
            items.append(f"{i}. Write a short response about {topic} in {subject}.")
            if include_answer_key:
                answers.append(f"{i}. Accept a relevant answer connected to {topic}.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award 1 mark for a relevant and accurate response.")

    data = {
        "title": title,
        "student_instructions": [
            f"Complete this {ACTIVITY_LABELS.get(activity_type, 'activity').lower()} on {topic}.",
            "Write clearly and use full working where needed."
        ],
        "worksheet_items": items,
        "answer_key": answers if include_answer_key else [],
    }

    if include_mark_scheme:
        data["mark_scheme"] = mark_scheme

    return data


def _to_text(data: Dict[str, Any], include_mark_scheme: bool) -> str:
    lines: List[str] = []

    lines.append(data.get("title", "Activity"))
    lines.append("")

    if data.get("student_instructions"):
        lines.append("Student Instructions:")
        for item in data["student_instructions"]:
            lines.append(f"- {item}")
        lines.append("")

    if data.get("worksheet_items"):
        lines.append("Activity:")
        for item in data["worksheet_items"]:
            lines.append(str(item))
        lines.append("")

    if data.get("answer_key"):
        lines.append("Answer Key:")
        for item in data["answer_key"]:
            lines.append(f"- {item}")
        lines.append("")

    if include_mark_scheme and data.get("mark_scheme"):
        lines.append("Mark Scheme:")
        for item in data["mark_scheme"]:
            lines.append(f"- {item}")

    return "\n".join(lines).strip()


def generate_activity(payload: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _extract_lesson_context(payload)

    activity_type = payload["activity_type"]
    count = int(payload.get("item_count", 8))
    include_answer_key = bool(payload.get("include_answer_key", True))
    include_mark_scheme = bool(payload.get("include_mark_scheme", False))

    title = f"{ACTIVITY_LABELS.get(activity_type, 'Activity')} - {ctx.get('topic', '')}"

    if not OPENAI_API_KEY:
        data = _fallback_activity(ctx, activity_type, count, include_answer_key, include_mark_scheme)
        return {
            "title": data.get("title", title),
            "activity_type": activity_type,
            "content": _to_text(data, include_mark_scheme=include_mark_scheme),
            "lesson_snippet": "",
            "raw": data,
        }

    objectives_text = "- None provided"
    if ctx["objectives"]:
        first = ctx["objectives"][0]
        if isinstance(first, dict):
            objectives_text = "\n".join(f"- {obj.get('text', '')}" for obj in ctx["objectives"])
        else:
            objectives_text = "\n".join(f"- {obj}" for obj in ctx["objectives"])

    sections_text = json.dumps(ctx["sections"], indent=2) if ctx["sections"] else "{}"

    prompt = PROMPT_TEMPLATE.format(
        mode=ctx["mode"],
        curriculum=ctx["curriculum"],
        subject=ctx["subject"],
        grade_level=ctx["grade_level"],
        topic=ctx["topic"],
        difficulty=ctx["difficulty"] or payload.get("difficulty", "Intermediate"),
        objectives=objectives_text,
        sections=sections_text,
        activity_type=ACTIVITY_LABELS.get(activity_type, activity_type),
        count=count,
        include_answer_key="yes" if include_answer_key else "no",
        include_mark_scheme="yes" if include_mark_scheme else "no",
    )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
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
                "worksheet_items": [raw_text or f"Create an activity about {ctx.get('topic', 'the topic')}."],
                "answer_key": [],
            }

    except Exception:
        data = _fallback_activity(ctx, activity_type, count, include_answer_key, include_mark_scheme)

    data.pop("teacher_notes", None)

    if not include_mark_scheme:
        data.pop("mark_scheme", None)

    if not include_answer_key:
        data["answer_key"] = []

    return {
        "title": data.get("title", title),
        "activity_type": activity_type,
        "content": _to_text(data, include_mark_scheme=include_mark_scheme),
        "lesson_snippet": "",
        "raw": data,
    }