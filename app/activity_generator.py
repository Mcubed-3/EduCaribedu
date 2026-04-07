from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from .math_bank_service import format_math_bank_for_prompt

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

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
    "agriculture",
    "information technology",
    "it",
    "business basics",
    "accounts",
    "accounting",
    "geography",
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


def _subject_group(subject: str) -> str:
    s = (subject or "").strip().lower()

    if s in {"mathematics", "math"}:
        return "math"
    if s in {"biology", "chemistry", "physics", "integrated science", "science"}:
        return "science"
    if s in {"language arts", "english"}:
        return "language"
    if s in {"spanish", "french/spanish"}:
        return "modern_language"
    if s in {"social studies", "history", "geography", "integrated studies"}:
        return "social_humanities"
    if s in {
        "information technology",
        "it",
        "resource and technology",
        "engineering and mechanisms",
        "industrial techniques",
    }:
        return "technology_design"
    if s in {"agricultural science", "agriculture"}:
        return "agriculture"
    if s in {"health and family life education", "physical education", "family and consumer management"}:
        return "wellness_life"
    if s in {"business basics", "accounts", "accounting", "jace"}:
        return "enterprise"
    if s in {"drama", "music", "visual arts"}:
        return "creative_arts"

    return "general"


def _math_rules(subject: str, topic: str, grade_level: str, curriculum: str) -> str:
    subject_key = (subject or "").strip().lower()

    bank_text = format_math_bank_for_prompt(
        subject=subject,
        grade_level=grade_level,
        curriculum=curriculum,
        topic=topic,
        limit=6,
    )

    if subject_key not in MATH_HEAVY_SUBJECTS:
        return f"""
If formulas, symbols, measurements, ratios, tables, coordinates, or calculations appear, write them in clean plain text only.

Do NOT use LaTeX.
Do NOT use backslashes.
Do NOT use dfrac, tfrac, pm, sqrt{{}}, mathrm{{}}, Delta, Rightarrow, bigl, bigr, cdot, or similar notation.

If numerical structure is needed, write it plainly.

Math bank examples:
{bank_text}
""".strip()

    return f"""
CRITICAL MATH RULES:
- NEVER use LaTeX.
- NEVER use backslashes.
- NEVER use dfrac, tfrac, pm, sqrt{{}}, mathrm{{}}, Delta, Rightarrow, bigl, bigr, cdot, or similar notation.
- Write all mathematics in clean editable plain text.
- Use readable forms like:
  x^2 - 5x + 6 = 0
  x = (-b ± √(b^2 - 4ac)) / 2a
  moles = mass / molar mass
  profit % = (profit / cost price) × 100
  area = 18 m^2
  scale = 1 : 50 000

- If a table is needed for business/accounts/family consumer management, use a clean text-table style.
- Keep each worked step on its own readable line.

Math bank examples:
{bank_text}
""".strip()


PROMPT_TEMPLATE = """
You are generating a classroom activity strictly aligned to the teaching context provided.

CRITICAL RULES:
- Only generate content related to the subject and topic provided.
- Do not include unrelated subjects.
- If lesson objectives and lesson sections are provided, use them directly.
- If no lesson is provided, generate an original standalone activity aligned to the curriculum, subject, grade level, difficulty, and topic.
- If include_mark_scheme is false, do not return any mark scheme.
- Do not return teacher notes.
- Do not include a teacher notes section in any form.
- Keep all wording classroom-ready, readable, neat, and structured.
- Make answer keys organized item-by-item and easy for teachers to use.
- Avoid generic filler.
- Use Caribbean context where natural.
- {math_rules}

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
- worksheet_items must contain clean student-facing questions only
- answer_key must match worksheet_items in order
- each answer_key item must begin with the matching number, e.g. "1. ..."
- keep answer_key concise and readable
- if worked solutions are needed, use short clear step lines
- for mixed ability worksheets, include a sensible progression from accessible to standard to challenge items
- if activity_type is MCQ, include options inside worksheet_items
- if activity_type is math_problem_solving, use plain-text mathematical notation only
- do not output markdown
- do not output code fences
- do not output explanations outside the JSON object

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

    group = _subject_group(subject)

    if activity_type == "math_problem_solving":
        for i in range(1, count + 1):
            label = ""
            if i <= max(2, count // 4):
                label = "Starter: "
            elif i == count:
                label = "Challenge: "
            items.append(f"{i}. {label}Solve a problem related to {topic}. Show all working clearly.")
            if include_answer_key:
                answers.append(f"{i}. Accept any correct worked solution related to {topic}, with clear method and correct final answer.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award marks for correct method, accurate working, and correct final answer.")

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

    elif group == "enterprise":
        for i in range(1, count + 1):
            items.append(f"{i}. Complete a short business/accounts task related to {topic}.")
            if include_answer_key:
                answers.append(f"{i}. Accept any accurate response or calculation linked to {topic}.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award marks for accuracy, relevance, and correct working where needed.")

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

    text = text.replace("\\\\(", "").replace("\\\\)", "")
    text = text.replace("\\\\[", "").replace("\\\\]", "")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("\\", "")

    replacements = {
        "dfrac": "",
        "tfrac": "",
        "pm": "±",
        "mathrm": "",
        "Rightarrow": "=>",
        "Delta": "discriminant",
        "cdot": "×",
        "bigl": "",
        "bigr": "",
        "left(": "(",
        "right)": ")",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    text = re.sub(r"sqrt\{([^{}]+)\}", r"√(\1)", text)
    text = re.sub(r"sqrt\(([^()]+)\)", r"√(\1)", text)
    text = re.sub(r"\^\{(\d+)\}", r"^\1", text)
    text = re.sub(r"\^\{([A-Za-z0-9]+)\}", r"^\1", text)

    text = text.replace("nStep", "\nStep")
    text = text.replace(".nStep", ".\nStep")
    text = text.replace(":n", ":\n")
    text = text.replace("sonx_", "so\nx_")
    text = text.replace("n(", "\n(")

    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _ensure_numbered_items(items: List[str]) -> List[str]:
    numbered: List[str] = []
    for idx, item in enumerate(items, start=1):
        clean = _clean_string(item)
        if not clean:
            continue
        if re.match(rf"^{idx}\.\s", clean):
            numbered.append(clean)
        else:
            numbered.append(f"{idx}. {clean}")
    return numbered


def _clean_student_instructions(items: List[str]) -> List[str]:
    cleaned = [_clean_string(x) for x in items if _clean_string(x)]
    result: List[str] = []

    for item in cleaned:
        if len(item) > 260 and ". " in item:
            parts = [p.strip() for p in item.split(". ") if p.strip()]
            for part in parts:
                if not part.endswith("."):
                    part = f"{part}."
                result.append(part)
        else:
            result.append(item)

    return result[:4]


def _normalize_question_spacing(text: str) -> str:
    clean = _clean_string(text)
    clean = re.sub(r"\s*\n\s*", "\n", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def _normalize_answer_key_item(text: str, number: int) -> str:
    clean = _clean_string(text)

    clean = re.sub(r"^(\d+)\.\s*", "", clean).strip()

    step_markers = [
        "Step 1:",
        "Step 2:",
        "Step 3:",
        "Step 4:",
        "Step 5:",
    ]
    for marker in step_markers:
        clean = clean.replace(marker, f"\n{marker}")

    clean = clean.replace(" Method:", "\nMethod:")
    clean = clean.replace(" Steps:", "\nSteps:")
    clean = clean.replace(" Final:", "\nFinal:")
    clean = clean.replace(" Answer:", "\nAnswer:")

    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

    if not clean:
        return f"{number}."

    return f"{number}. {clean}"


def _normalize_activity_json(data: Dict[str, Any], include_answer_key: bool, include_mark_scheme: bool) -> Dict[str, Any]:
    worksheet_items = [_normalize_question_spacing(x) for x in data.get("worksheet_items", []) if _clean_string(x)]
    worksheet_items = _ensure_numbered_items(worksheet_items)

    answer_key_raw = data.get("answer_key", []) if include_answer_key else []
    normalized_answers = [
        _normalize_answer_key_item(item, idx)
        for idx, item in enumerate(answer_key_raw, start=1)
        if _clean_string(item)
    ]

    normalized = {
        "title": _clean_string(data.get("title", "Activity")),
        "student_instructions": _clean_student_instructions(data.get("student_instructions", [])),
        "worksheet_items": worksheet_items,
        "answer_key": normalized_answers,
    }

    if include_mark_scheme:
        normalized["mark_scheme"] = _ensure_numbered_items(data.get("mark_scheme", []))

    if not include_answer_key:
        normalized["answer_key"] = []

    return normalized


def _format_answer_key_item(text: str) -> str:
    clean = _clean_string(text)

    if "\n" not in clean:
        return clean

    parts = [part.strip() for part in clean.split("\n") if part.strip()]
    if not parts:
        return clean

    first = parts[0]
    rest = parts[1:]

    if not rest:
        return first

    indented = [first]
    for part in rest:
        indented.append(f"   {part}")

    return "\n".join(indented)


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
        lines.append("Questions:")
        for item in data["worksheet_items"]:
            lines.append(str(item))
            lines.append("")
        if lines and lines[-1] == "":
            lines.pop()

    if data.get("answer_key"):
        lines.append("")
        lines.append("Answer Key:")
        for item in data["answer_key"]:
            lines.append(_format_answer_key_item(str(item)))
            lines.append("")
        if lines and lines[-1] == "":
            lines.pop()

    if include_mark_scheme and data.get("mark_scheme"):
        lines.append("")
        lines.append("Mark Scheme:")
        for item in data["mark_scheme"]:
            lines.append(str(item))
            lines.append("")
        if lines and lines[-1] == "":
            lines.pop()

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
        math_rules=_math_rules(
            ctx["subject"],
            ctx["topic"],
            ctx["grade_level"],
            ctx["curriculum"],
        ),
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
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                raw_text = raw_text[start : end + 1]
            data = json.loads(raw_text)
        except Exception:
            data = _fallback_activity(ctx, activity_type, count, include_answer_key, include_mark_scheme)

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