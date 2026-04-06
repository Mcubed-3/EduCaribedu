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

MATH_HEAVY_SUBJECTS = {
    "mathematics",
    "math",
    "physics",
    "chemistry",
    "integrated science",
    "science",
    "agricultural science",
    "information technology",
    "it",
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


def _math_rules(subject: str) -> str:
    if subject.strip().lower() not in MATH_HEAVY_SUBJECTS:
        return (
            "If formulas, symbols, measurements, ratios, or expressions appear, "
            "format them cleanly using MathJax-friendly LaTeX delimiters."
        )

    return """
CRITICAL MATH FORMAT RULES:
- Any equation, expression, fraction, exponent, root, coordinate, variable, or formula MUST be written in MathJax-friendly LaTeX.
- Inline maths must use \\( ... \\)
- Display maths must use \\[ ... \\]
- Fractions must use \\frac{a}{b}
- Powers must use x^2 or x^{10} inside math delimiters
- Roots must use \\sqrt{x}
- Coordinates must be written like \\((2, -1)\\)
- Simultaneous equations must be cleanly written, for example:
  \\(2x + 3y = 16\\) and \\(x - y = 1\\)
- Do NOT insert stray delimiters around plain words.
- Do NOT output malformed strings like \\(a\\) short scenario or \\(m\\) unless m is truly a variable.
- Do NOT double-escape delimiters.
""".strip()


PROMPT_TEMPLATE = r"""
You are generating a classroom activity STRICTLY aligned to the teaching context provided.

CRITICAL RULES:
- ONLY generate content related to the subject and topic provided.
- DO NOT include unrelated subjects.
- If lesson objectives and lesson sections are provided, use them directly.
- If no lesson is provided, generate an original standalone activity aligned to the curriculum, subject, grade level, difficulty, and topic.
- If include_mark_scheme is false, DO NOT return any mark scheme.
- DO NOT return teacher notes.
- DO NOT include a teacher notes section in any form.
- Keep all wording classroom-ready, readable, and clean.
- Make answer keys structured, step-by-step where appropriate, and easy for teachers to use.
- Do not produce strange slashes, broken delimiters, or random symbolic wrappers around normal words.
- {math_rules}
- Do NOT wrap isolated single letters such as x, y, a, b, m, or c in math delimiters unless they are part of a full equation or expression.
- Write equations as full equations, for example \\(y = 2x + 1\\), not as separate fragments like y = \\(2x + 1\\).

Return ONLY valid JSON in this exact structure:

{{
  "title": "string",
  "student_instructions": ["string", "string"],
  "worksheet_items": ["string", "string"],
  "answer_key": ["string", "string"]
}}

If include_mark_scheme is true, you may also include:
{{
  "mark_scheme": ["string", "string"]
}}

Formatting rules for output:
- worksheet_items must be clean questions only
- answer_key must be organized item-by-item in the same order as worksheet_items
- each answer_key item should begin with the matching number, e.g. "1. ..."
- if a worked solution is needed, write it clearly and in order
- if activity_type is MCQ, include options inside worksheet_items
- if activity_type is math_problem_solving, use properly formatted mathematical notation and readable working

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


def _fallback_activity(
    ctx: Dict[str, Any],
    activity_type: str,
    count: int,
    include_answer_key: bool,
    include_mark_scheme: bool,
) -> Dict[str, Any]:
    topic = ctx.get("topic", "the topic")
    subject = ctx.get("subject", "the subject")
    grade_level = ctx.get("grade_level", "the selected grade")
    title = f"{ACTIVITY_LABELS.get(activity_type, 'Activity')} - {topic}"

    items: List[str] = []
    answers: List[str] = []
    mark_scheme: List[str] = []

    if activity_type == "math_problem_solving":
        for i in range(1, count + 1):
            items.append(
                f"{i}. Solve a problem related to {topic}. Show all working clearly and use proper mathematical notation."
            )
            if include_answer_key:
                answers.append(
                    f"{i}. Accept any correct worked solution related to {topic}, with clear method and correct final answer."
                )
            if include_mark_scheme:
                mark_scheme.append(
                    f"{i}. Award marks for correct method, accurate working, and correct final answer."
                )

    elif activity_type == "mcq":
        for i in range(1, count + 1):
            items.append(
                f"{i}. Which statement best relates to {topic} in {subject} for {grade_level}?\n"
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
                answers.append(f"{i}. Accept any relevant and accurate response connected to {topic}.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award 1 mark for a relevant and accurate response.")

    data: Dict[str, Any] = {
        "title": title,
        "student_instructions": [
            f"Complete this {ACTIVITY_LABELS.get(activity_type, 'activity').lower()} on {topic}.",
            "Write clearly and show full working where needed.",
        ],
        "worksheet_items": items,
        "answer_key": answers if include_answer_key else [],
    }

    if include_mark_scheme:
        data["mark_scheme"] = mark_scheme

    return data


def _clean_string(value: Any) -> str:
    text = str(value or "").strip()

    text = text.replace("\\\\(", "\\(").replace("\\\\)", "\\)")
    text = text.replace("\\\\[", "\\[").replace("\\\\]", "\\]")

    # Remove stray inline delimiters around plain letters in normal prose
    text = text.replace("\\(a\\) ", "a ")
    text = text.replace("\\(A\\) ", "A ")
    text = text.replace("\\(m\\)", "m")
    text = text.replace("\\(b\\)", "b")
    text = text.replace("\\(y\\)", "y")
    text = text.replace("\\(x\\)", "x")

    return text.strip()


def _normalize_activity_json(data: Dict[str, Any], include_answer_key: bool, include_mark_scheme: bool) -> Dict[str, Any]:
    normalized = {
        "title": _clean_string(data.get("title", "Activity")),
        "student_instructions": [_clean_string(x) for x in data.get("student_instructions", []) if _clean_string(x)],
        "worksheet_items": [_clean_string(x) for x in data.get("worksheet_items", []) if _clean_string(x)],
        "answer_key": [_clean_string(x) for x in data.get("answer_key", []) if _clean_string(x)],
    }

    if include_mark_scheme:
        normalized["mark_scheme"] = [_clean_string(x) for x in data.get("mark_scheme", []) if _clean_string(x)]

    if not include_answer_key:
        normalized["answer_key"] = []

    return normalized


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
            lines.append(str(item))
        lines.append("")

    if include_mark_scheme and data.get("mark_scheme"):
        lines.append("Mark Scheme:")
        for item in data["mark_scheme"]:
            lines.append(str(item))

    return "\n".join(lines).strip()


def generate_activity(payload: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _extract_lesson_context(payload)

    activity_type = (payload.get("activity_type") or "short_answer").strip()
    count = int(payload.get("item_count") or 8)
    include_answer_key = bool(payload.get("include_answer_key", True))
    include_mark_scheme = bool(payload.get("include_mark_scheme", False))

    title = f"{ACTIVITY_LABELS.get(activity_type, 'Activity')} - {ctx.get('topic', 'Topic')}"

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
        math_rules=_math_rules(ctx["subject"]),
    )

    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("Missing OPENAI_API_KEY")

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

    except Exception as exc:
        print(f"ACTIVITY AI DEBUG: {type(exc).__name__}: {exc}")
        data = _fallback_activity(ctx, activity_type, count, include_answer_key, include_mark_scheme)

    data.pop("teacher_notes", None)

    if not include_mark_scheme:
        data.pop("mark_scheme", None)

    normalized = _normalize_activity_json(
        data,
        include_answer_key=include_answer_key,
        include_mark_scheme=include_mark_scheme,
    )

    return {
        "title": normalized.get("title", title),
        "activity_type": activity_type,
        "content": _to_text(normalized, include_mark_scheme=include_mark_scheme),
        "lesson_snippet": "",
        "raw": normalized,
    }