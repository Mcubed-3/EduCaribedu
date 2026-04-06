from __future__ import annotations

import hashlib
import json
import re
from typing import Dict, List

from .ai_generator import generate_dynamic_lesson_parts
from .engine_state import engine

FIVE_E_SECTIONS = ["Engagement", "Exploration", "Explanation", "Evaluation", "Extension"]
FOUR_C_SECTIONS = ["Creativity", "Critical Thinking", "Communication", "Collaboration"]

CACHE: Dict[str, dict] = {}


def cache_key(payload: dict) -> str:
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()


# ✅ FIXED CLEANER (THIS WAS YOUR BUG)
def _clean_math_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    text = re.sub(r"\\\(|\\\)|\\\[|\\\]", "", text)
    text = text.replace("\\", "")

    # convert powers
    text = re.sub(r"\^\{(\d+)\}", r"^\1", text)

    # fix sqrt
    text = text.replace("sqrt", "√")

    # remove JSON garbage
    text = text.replace('"', "").replace("{", "").replace("}", "")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _clean_list(items):
    if not isinstance(items, list):
        return items
    return [_clean_math_text(str(i)) for i in items if str(i).strip()]


# ✅ SUBJECT-SMART FALLBACK (FULL FRAMEWORK SUPPORT)
def _subject_context(subject: str, topic: str) -> str:
    s = subject.lower()

    if "math" in s:
        return f"Students solve problems and apply {topic} in real-life and exam contexts."
    if "biology" in s:
        return f"Students explore biological meaning and application of {topic}."
    if "chemistry" in s:
        return f"Students investigate chemical principles related to {topic}."
    if "physics" in s:
        return f"Students analyse physical concepts and calculations involving {topic}."
    if "agricultural" in s:
        return f"Students apply {topic} to Caribbean agriculture and farming systems."
    if "geography" in s:
        return f"Students relate {topic} to environmental and spatial understanding."
    if "history" in s:
        return f"Students examine events and perspectives connected to {topic}."
    if "english" in s or "language" in s:
        return f"Students develop communication skills through {topic}."
    if "business" in s:
        return f"Students apply {topic} to real-world business situations."
    if "it" in s or "technology" in s:
        return f"Students use digital tools and systems related to {topic}."

    return f"Students understand and apply {topic} in meaningful real-world contexts."


def _fallback_sections(topic, subject):
    return {
        "Engagement": [
            f"Introduce {topic} using a real-life or Caribbean-based example."
        ],
        "Exploration": [
            f"Students explore {topic} through guided activities and examples."
        ],
        "Explanation": [
            f"Teacher explains key ideas and demonstrates {topic} step-by-step."
        ],
        "Evaluation": [
            f"Students complete tasks to demonstrate understanding of {topic}."
        ],
        "Extension": [
            f"Students apply {topic} to real-world or exam-style problems."
        ],
    }


def generate_lesson(payload: dict) -> dict:

    key = cache_key(payload)
    if key in CACHE:
        return CACHE[key]

    subject = payload.get("subject", "")
    topic = payload.get("topic", "")

    objectives = engine.build_objectives(
        payload["curriculum"],
        subject,
        payload["grade_level"],
        topic,
        payload.get("objective_count", 3),
        payload.get("difficulty", "Intermediate"),
        payload.get("description", ""),
    )

    objective_text = [obj["text"] for obj in objectives]

    fallback = {
        "attainment_target": _subject_context(subject, topic),
        "sections": _fallback_sections(topic, subject),
        "prior_knowledge_questions": [
            f"What do you already know about {topic}?",
            f"Where have you seen {topic} before?",
        ],
        "resources": [
            f"{subject} textbook",
            "Teacher notes",
            "Worksheet"
        ],
        "assessment": [
            f"Solve or explain problems based on {topic}"
        ],
        "reflection": [
            f"Did students understand {topic}?"
        ],
    }

    lesson = {
        "curriculum": payload["curriculum"],
        "subject": subject,
        "grade_level": payload["grade_level"],
        "topic": topic,
        "objectives": objective_text,
        "generation_mode": "fallback",
        **fallback
    }

    # ✅ AI GENERATION (NOW SAFE)
    try:
        ai_parts = generate_dynamic_lesson_parts(
            payload=payload,
            objectives=objective_text,
            strand="General",
            resource_suggestions=fallback["resources"],
        )

        if ai_parts:
            lesson.update({
                "attainment_target": _clean_math_text(ai_parts.get("attainment_target", lesson["attainment_target"])),
                "sections": ai_parts.get("sections", lesson["sections"]),
                "prior_knowledge_questions": _clean_list(ai_parts.get("prior_knowledge_questions", lesson["prior_knowledge_questions"])),
                "resources": _clean_list(ai_parts.get("resources", lesson["resources"])),
                "assessment": _clean_list(ai_parts.get("assessment", lesson["assessment"])),
                "reflection": _clean_list(ai_parts.get("reflection", lesson["reflection"])),
                "generation_mode": "ai"
            })

    except Exception as e:
        print("LESSON AI ERROR:", str(e))

    result = {
        "title": f"{subject} Lesson Plan - {topic}",
        "lesson": lesson
    }

    CACHE[key] = result
    return result