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
- If a table is needed, use a clean text-table style.
- Keep each worked step on its own readable line.

Math bank examples:
{bank_text}
""".strip()


def _force_table_instruction(subject: str, topic: str) -> str:
    s = (subject or "").strip().lower()
    if s in {"business basics", "accounts", "accounting", "agricultural science", "agriculture"}:
        return f"""
TABLE RULE:
If the activity for {topic} includes budgets, costing, revenue, profit, farm inputs, resource lists, or financial comparisons, you MUST format the data as:

Table: Sample budget
Item | Qty | Unit price | Cost
Seed | 10 kg | $20/kg | $200
Fertiliser | 5 bags | $50/bag | $250

Rules:
- Use "Table:" on its own line before the table.
- Use "|" to separate columns.
- Do NOT use markdown tables.
- Keep calculation lines below the table as normal lines.
"""
    return ""


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
- {table_rules}

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
- if activity_type is mcq, each question must place answer options on separate lines labeled A, B, C, D
- if activity_type is short_answer, questions should be brief and clearly phrased
- if activity_type is essay, prompts should be open-ended and suitable for paragraph responses
- if activity_type is case_study, include a short scenario followed by clear questions
- if activity_type is exit_ticket, keep the items short and quick to complete
- if activity_type is homework_sheet, include a varied progression of items
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
    grade_level = ctx.get("grade_level", "")
    title = f"{ACTIVITY_LABELS.get(activity_type, 'Activity')} - {topic}"

    items: List[str] = []
    answers: List[str] = []
    mark_scheme: List[str] = []

    if _subject_group(subject) == "enterprise":
        items = [
            "Table: Sample budget",
            "Item | Qty | Unit price | Cost",
            "Seed | 10 kg | $20/kg | $200",
            "Fertiliser | 5 bags | $50/bag | $250",
            "Labour | 20 hours | $10/hour | $200",
            "Total Variable Cost | | | $650",
            "Fixed Cost | | | $150",
            "Total Cost | | | $800",
        ]
        while len(items) < count:
            idx = len(items) - 7
            items.append(f"{idx}. Use the budget table above to answer a question about revenue, total cost, or profit.")
        if include_answer_key:
            answers = [
                "1. Use the cost figures shown in the table.",
                "2. Revenue = Price per unit * Quantity sold.",
                "3. Profit = Revenue - Total Cost.",
            ]
        if include_mark_scheme:
            mark_scheme = [
                "1. Award marks for correct use of table values.",
                "2. Award marks for correct formula and substitution.",
                "3. Award marks for correct final answer.",
            ]
    elif activity_type == "math_problem_solving":
        for i in range(1, count + 1):
            items.append(f"{i}. Solve a problem related to {topic}. Show all working clearly.")
            if include_answer_key:
                answers.append(f"{i}. Accept a correct worked solution related to {topic}, with clear method and correct final answer.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award marks for method, working, and correct final answer.")
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
    elif activity_type == "short_answer":
        for i in range(1, count + 1):
            items.append(f"{i}. Give a short response about {topic}.")
            if include_answer_key:
                answers.append(f"{i}. Accept any relevant and accurate response connected to {topic}.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. 1 mark for a relevant response.")
    elif activity_type == "essay":
        for i in range(1, count + 1):
            items.append(f"{i}. Write a paragraph response about {topic}, using clear examples.")
            if include_answer_key:
                answers.append(f"{i}. Accept any well-developed and accurate response connected to {topic}.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award marks for relevance, development, accuracy, and clarity.")
    elif activity_type == "case_study":
        items = [
            f"Case Study: Read the scenario below about {topic} and answer the questions that follow.",
            f"1. Explain the main issue shown in the case study about {topic}.",
            f"2. Identify two important details from the case study.",
            f"3. Suggest one practical response or solution.",
        ][:count]
        if include_answer_key:
            answers = [
                "1. Accept a clear explanation of the main issue in the scenario.",
                "2. Accept any two relevant and accurate details.",
                "3. Accept any practical and relevant response.",
            ][: len(items)]
        if include_mark_scheme:
            mark_scheme = [
                "1. Award marks for a clear and relevant explanation.",
                "2. Award marks for two accurate details.",
                "3. Award marks for a practical and relevant suggestion.",
            ][: len(items)]
    elif activity_type == "exit_ticket":
        for i in range(1, count + 1):
            items.append(f"{i}. Give a brief answer related to {topic}.")
            if include_answer_key:
                answers.append(f"{i}. Accept a brief correct response related to {topic}.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. 1 mark for a correct response.")
    elif activity_type == "homework_sheet":
        for i in range(1, count + 1):
            label = ""
            if i <= max(2, count // 4):
                label = "Starter: "
            elif i == count:
                label = "Challenge: "
            items.append(f"{i}. {label}Complete a homework task related to {topic}.")
            if include_answer_key:
                answers.append(f"{i}. Accept any correct and relevant response or working.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award marks for accuracy, method, and completeness where relevant.")
    else:
        for i in range(1, count + 1):
            items.append(f"{i}. Write a short response about {topic} in {subject}.")
            if include_answer_key:
                answers.append(f"{i}. Accept a relevant answer connected to {topic}.")
            if include_mark_scheme:
                mark_scheme.append(f"{i}. Award 1 mark for a relevant and accurate response.")

    data: Dict[str, Any] = {
        "title": title,
        "student_instructions": [
            f"Complete this {ACTIVITY_LABELS.get(activity_type, 'activity').lower()} on {topic}.",
            "Write clearly and use full working where needed.",
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


def _normalize_question_spacing(text: str, activity_type: str, number: int) -> str:
    clean = _clean_string(text)
    clean = re.sub(r"\s*\n\s*", "\n", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    if clean.startswith("Table:") or "|" in clean:
        return clean

    if activity_type == "mcq":
        clean = re.sub(r"^(\d+)\.\s*", "", clean).strip()
        for marker in ["A.", "B.", "C.", "D."]:
            clean = re.sub(rf"\s+{re.escape(marker)}\s+", f"\n   {marker} ", clean)
        return f"{number}. {clean}"

    if re.match(rf"^{number}\.\s", clean):
        return clean

    return f"{number}. {clean}"


def _normalize_answer_key_item(text: str, number: int) -> str:
    clean = _clean_string(text)
    clean = re.sub(r"^(\d+)\.\s*", "", clean).strip()
    return f"{number}. {clean}" if clean else f"{number}."


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
            lines.append(f"- {_clean_string(item)}")
        lines.append("")

    if data.get("worksheet_items"):
        lines.append("Questions:")
        for idx, item in enumerate(data["worksheet_items"], start=1):
            normalized = _normalize_question_spacing(str(item), data.get("activity_type", ""), idx)
            lines.append(normalized)
            lines.append("")
        if lines and lines[-1] == "":
            lines.pop()

    if data.get("answer_key"):
        lines.append("")
        lines.append("Answer Key:")
        for idx, item in enumerate(data["answer_key"], start=1):
            lines.append(_normalize_answer_key_item(str(item), idx))
            lines.append("")
        if lines and lines[-1] == "":
            lines.pop()

    if include_mark_scheme and data.get("mark_scheme"):
        lines.append("")
        lines.append("Mark Scheme:")
        for idx, item in enumerate(data["mark_scheme"], start=1):
            lines.append(f"{idx}. {_clean_string(item)}")
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
        table_rules=_force_table_instruction(
            ctx["subject"],
            ctx["topic"],
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
            data = _normalize_activity_json(data, include_answer_key, include_mark_scheme)
        except Exception:
            data = _fallback_activity(ctx, activity_type, count, include_answer_key, include_mark_scheme)

    except Exception as exc:
        print(f"ACTIVITY AI DEBUG: {type(exc).__name__}: {exc}")
        data = _fallback_activity(ctx, activity_type, count, include_answer_key, include_mark_scheme)

    data.pop("teacher_notes", None)

    if not include_mark_scheme:
        data.pop("mark_scheme", None)

    data["activity_type"] = activity_type

    content = _to_text(data, include_mark_scheme=include_mark_scheme)

    return {
        "title": data.get("title", title),
        "activity_type": activity_type,
        "content": content,
        "lesson_snippet": "",
        "raw": data,
    }