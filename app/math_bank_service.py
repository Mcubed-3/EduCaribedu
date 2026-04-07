from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).parent
MATH_BANK_PATH = BASE_DIR / "math_bank.json"


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def load_math_bank() -> List[Dict[str, Any]]:
    if not MATH_BANK_PATH.exists():
        return []

    with open(MATH_BANK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("entries", [])


def _matches_subject(entry: Dict[str, Any], subject: str) -> bool:
    subject_norm = _normalize(subject)
    subjects = [_normalize(s) for s in entry.get("subjects", [])]
    return not subjects or subject_norm in subjects


def _matches_grade(entry: Dict[str, Any], grade_level: str) -> bool:
    grade_norm = _normalize(grade_level)
    grades = [_normalize(g) for g in entry.get("grade_levels", [])]
    return not grades or grade_norm in grades


def _matches_curriculum(entry: Dict[str, Any], curriculum: str) -> bool:
    curriculum_norm = _normalize(curriculum)
    curricula = [_normalize(c) for c in entry.get("curricula", [])]
    return not curricula or curriculum_norm in curricula


def _matches_topic(entry: Dict[str, Any], topic: str) -> bool:
    topic_norm = _normalize(topic)
    tags = [_normalize(tag) for tag in entry.get("topic_tags", [])]

    if not tags:
        return False

    return any(tag in topic_norm or topic_norm in tag for tag in tags)


def find_math_bank_entries(
    subject: str,
    grade_level: str,
    curriculum: str,
    topic: str,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    entries = load_math_bank()

    matches: List[Dict[str, Any]] = []
    for entry in entries:
        if not _matches_subject(entry, subject):
            continue
        if not _matches_grade(entry, grade_level):
            continue
        if not _matches_curriculum(entry, curriculum):
            continue
        if not _matches_topic(entry, topic):
            continue
        matches.append(entry)

    return matches[:limit]


def format_math_bank_for_prompt(
    subject: str,
    grade_level: str,
    curriculum: str,
    topic: str,
    limit: int = 6,
) -> str:
    matches = find_math_bank_entries(
        subject=subject,
        grade_level=grade_level,
        curriculum=curriculum,
        topic=topic,
        limit=limit,
    )

    if not matches:
        return "No matching math-bank entries found."

    lines: List[str] = []
    for item in matches:
        lines.append(
            f"- {item.get('id', 'unknown')}: plain_text={item.get('plain_text', '')}; "
            f"docx_safe={item.get('docx_safe', '')}; "
            f"usage_notes={item.get('usage_notes', '')}"
        )

    return "\n".join(lines)


def get_math_bank_plain_examples(
    subject: str,
    grade_level: str,
    curriculum: str,
    topic: str,
    limit: int = 6,
) -> List[str]:
    matches = find_math_bank_entries(
        subject=subject,
        grade_level=grade_level,
        curriculum=curriculum,
        topic=topic,
        limit=limit,
    )

    return [item.get("plain_text", "").strip() for item in matches if item.get("plain_text", "").strip()]