# REPLACE ENTIRE FILE

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()

# ---------------- MODELS ---------------- #

class ClassProfile(BaseModel):
    learner_profile: str
    learning_styles: List[str]
    mixed_ability_support: Optional[str] = None

class DomainObjectives(BaseModel):
    cognitive: str
    affective: str
    psychomotor: str

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

# ---------------- PROMPT ---------------- #

def _build_prompt(payload, objectives, strand, resource_suggestions):

    return f"""
You are an expert Caribbean teacher.

CRITICAL RULE:
DO NOT use LaTeX.
DO NOT use \\ or \\( \\) or \\frac or \\sqrt.

Write ALL math in CLEAN TEXT format:

GOOD:
x^2 - 5x + 6 = 0
(x + 3)/4
√(x/2)
x = (-b ± √(b² - 4ac)) / 2a

BAD:
\\(x^2\\)
\\frac{{x+3}}{{4}}

Make everything readable for students and editable in Word.

Lesson Details:
Subject: {payload["subject"]}
Topic: {payload["topic"]}
Grade: {payload["grade_level"]}
Structure: {payload["structure"]}
Difficulty: {payload["difficulty"]}

Return ONLY structured JSON.
"""

# ---------------- GENERATOR ---------------- #

def generate_dynamic_lesson_parts(payload, objectives, strand, resource_suggestions):

    if not OPENAI_API_KEY:
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        schema_model = LessonParts4C if payload["structure"] == "4Cs" else LessonParts5E

        response = client.responses.parse(
            model=OPENAI_MODEL,
            instructions="Return structured lesson JSON only.",
            input=_build_prompt(payload, objectives, strand, resource_suggestions),
            text_format=schema_model,
        )

        parsed = response.output_parsed
        if not parsed:
            return None

        return parsed.model_dump()

    except Exception as e:
        print("AI ERROR:", e)
        return None