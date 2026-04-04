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
    "crossword": "Crossword Puzzle",
    "word_search": "Word Search Puzzle",
    "case_study": "Case Study Worksheet",
    "exit_ticket": "Exit Ticket",
    "homework_sheet": "Homework Sheet",
}


def _fallback_items(activity_type: str, topic: str, subject: str, count: int) -> List[str]:
    if activity_type == "mcq":
        return [
            f"{i}. Write a multiple-choice question about {topic} in {subject} with four options."
            for i in range(1, count + 1)
        ]
    if activity_type == "word_search":
        return [
            f"Target vocabulary for {topic}: key term {i}" for i in range(1, min(count, 10) + 1)
        ]
    if activity_type == "crossword":
        return [
            f"Clue {i}: vocabulary clue for {topic} in {subject}" for i in range(1, count + 1)
        ]
    return [f"{i}. Create a classroom-ready prompt about {topic} for {subject}." for i in range(1, count + 1)]


def _fallback_grid(words: List[str], width: int = 10) -> List[str]:
    rows = []
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i in range(max(8, min(12, len(words) + 2))):
        row = "".join(alphabet[(i * 3 + j) % len(alphabet)] for j in range(width))
        rows.append(row)
    return rows


PROMPT_TEMPLATE = """
Create a classroom-ready activity sheet as JSON.

Return ONLY valid JSON with this exact shape:
{{
  "title": "string",
  "student_instructions": ["string", "string"],
  "worksheet_items": ["string", "string"],
  "answer_key": ["string"],
  "mark_scheme": ["string"],
  "teacher_notes": ["string"],
  "table_headers": ["string"],
  "table_rows": [["string", "string"]],
  "puzzle_grid": ["ABCDEFGHIJ"],
  "word_bank": ["string"],
  "lesson_snippet": ["string", "string"]
}}

Rules:
- Activity type: {activity_type_label}
- Curriculum: {curriculum}
- Subject: {subject}
- Grade/Level: {grade_level}
- Topic: {topic}
- Difficulty: {difficulty}
- Number of items: {question_count}
- Duration: {duration_minutes} minutes
- Include answer key: {include_answer_key}
- Include mark scheme: {include_mark_scheme}
- Additional notes: {additional_notes}
- Use the lesson text for alignment when provided.
- If the activity is math_problem_solving, include meaningful table headers and rows when useful.
- If the activity is case_study, include a short scenario followed by questions.
- If the activity is crossword or word_search, include a word_bank and puzzle_grid.
- lesson_snippet should be a short embedded task that can be inserted into a lesson plan.
- Keep worksheet_items concise and printable.
- If a field is not needed, return an empty list.

Lesson text:
{lesson_text}
""".strip()


def _to_text(data: Dict[str, Any], activity_type: str) -> str:
    lines: List[str] = []
    lines.append(data.get("title") or ACTIVITY_LABELS.get(activity_type, "Activity Sheet"))
    lines.append("")

    instructions = data.get("student_instructions") or []
    if instructions:
        lines.append("Student Instructions:")
        for item in instructions:
            lines.append(f"- {item}")
        lines.append("")

    items = data.get("worksheet_items") or []
    if items:
        lines.append("Activity Items:")
        for item in items:
            lines.append(str(item))
        lines.append("")

    headers = data.get("table_headers") or []
    rows = data.get("table_rows") or []
    if headers and rows:
        lines.append("Table Activity:")
        lines.append(" | ".join(headers))
        lines.append(" | ".join(["---"] * len(headers)))
        for row in rows:
            lines.append(" | ".join(str(cell) for cell in row))
        lines.append("")

    word_bank = data.get("word_bank") or []
    if word_bank:
        lines.append("Word Bank:")
        lines.append(", ".join(word_bank))
        lines.append("")

    grid = data.get("puzzle_grid") or []
    if grid:
        lines.append("Puzzle Grid:")
        for row in grid:
            lines.append(str(row))
        lines.append("")

    answer_key = data.get("answer_key") or []
    if answer_key:
        lines.append("Answer Key:")
        for item in answer_key:
            lines.append(f"- {item}")
        lines.append("")

    mark_scheme = data.get("mark_scheme") or []
    if mark_scheme:
        lines.append("Mark Scheme:")
        for item in mark_scheme:
            lines.append(f"- {item}")
        lines.append("")

    teacher_notes = data.get("teacher_notes") or []
    if teacher_notes:
        lines.append("Teacher Notes:")
        for item in teacher_notes:
            lines.append(f"- {item}")

    return "\n".join(lines).strip()


def generate_activity(payload: Dict[str, Any]) -> Dict[str, Any]:
    activity_type = payload["activity_type"]
    title = f"{ACTIVITY_LABELS.get(activity_type, 'Activity Sheet')} - {payload['topic']}"

    if not OPENAI_API_KEY:
        words = [payload["topic"].upper(), payload["subject"].upper(), payload["curriculum"].upper()]
        data = {
            "title": title,
            "student_instructions": [
                f"Complete this {ACTIVITY_LABELS.get(activity_type, 'activity').lower()} based on {payload['topic']}.",
                "Use your lesson notes and class discussion to help you.",
            ],
            "worksheet_items": _fallback_items(activity_type, payload["topic"], payload["subject"], payload["question_count"]),
            "answer_key": ["Teacher-generated answer key unavailable in fallback mode."],
            "mark_scheme": ["Award marks for accuracy, relevance, and clear working where appropriate."] if payload.get("include_mark_scheme") else [],
            "teacher_notes": ["Fallback mode was used because OPENAI_API_KEY is not configured."],
            "table_headers": ["Question", "Student Response"] if activity_type in {"math_problem_solving", "case_study"} else [],
            "table_rows": [[f"Task {i}", ""] for i in range(1, min(payload["question_count"], 6) + 1)] if activity_type in {"math_problem_solving", "case_study"} else [],
            "puzzle_grid": _fallback_grid(words) if activity_type in {"word_search", "crossword"} else [],
            "word_bank": words if activity_type in {"word_search", "crossword"} else [],
            "lesson_snippet": [
                f"Embedded activity: use a short {ACTIVITY_LABELS.get(activity_type, 'activity').lower()} on {payload['topic']}.",
                "Review answers as a class during plenary or independent practice.",
            ],
        }
        return {
            "title": data["title"],
            "activity_type": activity_type,
            "content": _to_text(data, activity_type),
            "lesson_snippet": "\n".join(f"- {item}" for item in data.get("lesson_snippet", [])),
            "raw": data,
        }

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = PROMPT_TEMPLATE.format(
        activity_type_label=ACTIVITY_LABELS.get(activity_type, activity_type),
        curriculum=payload["curriculum"],
        subject=payload["subject"],
        grade_level=payload["grade_level"],
        topic=payload["topic"],
        difficulty=payload.get("difficulty", "Intermediate"),
        question_count=payload.get("question_count", 6),
        duration_minutes=payload.get("duration_minutes", 20),
        include_answer_key=str(payload.get("include_answer_key", True)),
        include_mark_scheme=str(payload.get("include_mark_scheme", False)),
        additional_notes=payload.get("additional_notes", ""),
        lesson_text=payload.get("lesson_text", "")[:6000],
    )

    response = client.responses.create(model=OPENAI_MODEL, input=prompt)
    raw_text = getattr(response, "output_text", "").strip()
    if not raw_text:
        raise RuntimeError("No activity content was returned by the AI service.")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        data = {
            "title": title,
            "student_instructions": ["Use the generated activity below."],
            "worksheet_items": [raw_text],
            "answer_key": [],
            "mark_scheme": [],
            "teacher_notes": [],
            "table_headers": [],
            "table_rows": [],
            "puzzle_grid": [],
            "word_bank": [],
            "lesson_snippet": ["Use the full generated activity as an extension or homework task."],
        }

    return {
        "title": data.get("title") or title,
        "activity_type": activity_type,
        "content": _to_text(data, activity_type),
        "lesson_snippet": "\n".join(f"- {item}" for item in (data.get("lesson_snippet") or [])),
        "raw": data,
    }
