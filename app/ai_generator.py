from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()

STEM_SUBJECTS = {
    "agricultural science",
    "mathematics",
    "math",
    "biology",
    "chemistry",
    "physics",
    "integrated science",
    "science",
    "information technology",
    "it",
}


# =========================
# MODELS
# =========================

class ClassProfile(BaseModel):
    learner_profile: str = Field(min_length=20, max_length=320)
    learning_styles: List[str] = Field(min_length=2, max_length=4)
    mixed_ability_support: Optional[str] = None  # ✅ NOW OPTIONAL


class DomainObjectives(BaseModel):
    cognitive: str = Field(min_length=12, max_length=220)
    affective: str = Field(min_length=12, max_length=220)
    psychomotor: str = Field(min_length=12, max_length=220)


class LessonSections5E(BaseModel):
    Engagement: List[str]
    Exploration: List[str]
    Explanation: List[str]
    Evaluation: List[str]
    Extension: List[str]


class LessonSections4C(BaseModel):
    Creativity: List[str]
    Critical_Thinking: List[str]
    Communication: List[str]
    Collaboration: List[str]


class LessonParts5E(BaseModel):
    attainment_target: str
    theme: str
    strand: str
    class_profile: ClassProfile
    domain_objectives: DomainObjectives
    prior_learning: str
    prior_knowledge_questions: List[str]
    resources: List[str]
    sections: LessonSections5E
    assessment: List[str]
    assessment_criteria: str
    apse_pathways: List[str]
    stem_skills: List[str] = []
    reflection: List[str]


class LessonParts4C(BaseModel):
    attainment_target: str
    theme: str
    strand: str
    class_profile: ClassProfile
    domain_objectives: DomainObjectives
    prior_learning: str
    prior_knowledge_questions: List[str]
    resources: List[str]
    sections: LessonSections4C
    assessment: List[str]
    assessment_criteria: str
    apse_pathways: List[str]
    stem_skills: List[str] = []
    reflection: List[str]


# =========================
# PROMPT BUILDER
# =========================

def _teacher_profile_text(payload: dict) -> str:
    profile = payload.get("teacher_profile") or {}
    subjects = ", ".join(profile.get("subjects", []) or [])
    grade_levels = ", ".join(profile.get("grade_levels", []) or [])
    curriculum = profile.get("curriculum", "")

    if not any([subjects, grade_levels, curriculum]):
        return "No teacher profile details were provided."

    return (
        f"Teacher profile defaults: subjects={subjects or 'not set'}; "
        f"grade levels={grade_levels or 'not set'}; curriculum={curriculum or 'not set'}."
    )


def _build_prompt(payload, objectives, strand, resource_suggestions):
    structure = payload["structure"]
    lesson_type = payload["lesson_type"]
    difficulty = payload["difficulty"]
    subject = payload["subject"]
    grade_level = payload["grade_level"]
    topic = payload["topic"]

    is_stem = subject.lower() in STEM_SUBJECTS

    # 🔥 Conditional mixed ability instruction
    if difficulty == "Mixed Ability":
        mixed_ability_text = "Include mixed-ability support in the class profile."
    else:
        mixed_ability_text = "Do NOT include mixed-ability support."

    stem_text = (
        "Include practical STEM or skill-based activities."
        if is_stem else
        "Keep the lesson practical and skill-based where appropriate."
    )

    return f"""
Create a Caribbean-standard lesson plan.

Context:
- Subject: {subject}
- Grade: {grade_level}
- Topic: {topic}
- Structure: {structure}
- Difficulty: {difficulty}
- Strand: {strand}
- Objectives: {objectives}

Rules:
- Keep it teacher-ready and realistic
- Include learning styles
- {mixed_ability_text}
- {stem_text}
- Do NOT repeat objectives
- Do NOT include a separate 'Objectives' section
- Only include 'Specific Objectives'

Ensure all sections are detailed but concise.
"""


# =========================
# MAIN GENERATOR
# =========================

def generate_dynamic_lesson_parts(
    payload,
    objectives,
    strand,
    resource_suggestions,
):
    if not OPENAI_API_KEY:
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = _build_prompt(payload, objectives, strand, resource_suggestions)

        schema = LessonParts4C if payload["structure"] == "4Cs" else LessonParts5E

        response = client.responses.parse(
            model=OPENAI_MODEL,
            input=prompt,
            text_format=schema,
        )

        data = response.output_parsed.model_dump()

        # 🔥 CLEANUP: Remove mixed ability if not selected
        if payload["difficulty"] != "Mixed Ability":
            data["class_profile"].pop("mixed_ability_support", None)

        return data

    except Exception as e:
        print("AI ERROR:", e)
        return None