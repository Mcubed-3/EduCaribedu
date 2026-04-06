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

MATH_HEAVY_SUBJECTS = {
    "agricultural science",
    "mathematics",
    "math",
    "chemistry",
    "physics",
    "integrated science",
    "science",
    "information technology",
    "it",
    "economics",
    "geography",
    "technical drawing",
    "accounts",
    "accounting",
}


class ClassProfile(BaseModel):
    learner_profile: str = Field(min_length=20, max_length=320)
    learning_styles: List[str] = Field(min_length=2, max_length=4)
    mixed_ability_support: Optional[str] = None


class DomainObjectives(BaseModel):
    cognitive: str = Field(min_length=12, max_length=220)
    affective: str = Field(min_length=12, max_length=220)
    psychomotor: str = Field(min_length=12, max_length=220)


class LessonSections5E(BaseModel):
    Engagement: List[str] = Field(min_length=2, max_length=4)
    Exploration: List[str] = Field(min_length=2, max_length=4)
    Explanation: List[str] = Field(min_length=2, max_length=4)
    Evaluation: List[str] = Field(min_length=2, max_length=4)
    Extension: List[str] = Field(min_length=1, max_length=3)


class LessonSections4C(BaseModel):
    Creativity: List[str] = Field(min_length=2, max_length=4)
    Critical_Thinking: List[str] = Field(min_length=2, max_length=4)
    Communication: List[str] = Field(min_length=2, max_length=4)
    Collaboration: List[str] = Field(min_length=2, max_length=4)


class LessonParts5E(BaseModel):
    attainment_target: str = Field(min_length=20, max_length=320)
    theme: str = Field(min_length=3, max_length=120)
    strand: str = Field(min_length=3, max_length=120)
    class_profile: ClassProfile
    domain_objectives: DomainObjectives
    prior_learning: str = Field(min_length=20, max_length=320)
    prior_knowledge_questions: List[str] = Field(min_length=3, max_length=5)
    resources: List[str] = Field(min_length=3, max_length=6)
    sections: LessonSections5E
    assessment: List[str] = Field(min_length=2, max_length=4)
    assessment_criteria: str = Field(min_length=20, max_length=320)
    apse_pathways: List[str] = Field(min_length=2, max_length=4)
    stem_skills: List[str] = Field(default_factory=list, max_length=5)
    reflection: List[str] = Field(min_length=3, max_length=5)


class LessonParts4C(BaseModel):
    attainment_target: str = Field(min_length=20, max_length=320)
    theme: str = Field(min_length=3, max_length=120)
    strand: str = Field(min_length=3, max_length=120)
    class_profile: ClassProfile
    domain_objectives: DomainObjectives
    prior_learning: str = Field(min_length=20, max_length=320)
    prior_knowledge_questions: List[str] = Field(min_length=3, max_length=5)
    resources: List[str] = Field(min_length=3, max_length=6)
    sections: LessonSections4C
    assessment: List[str] = Field(min_length=2, max_length=4)
    assessment_criteria: str = Field(min_length=20, max_length=320)
    apse_pathways: List[str] = Field(min_length=2, max_length=4)
    stem_skills: List[str] = Field(default_factory=list, max_length=5)
    reflection: List[str] = Field(min_length=3, max_length=5)


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


def _math_output_rules(subject: str, topic: str, structure: str) -> str:
    if subject.strip().lower() not in MATH_HEAVY_SUBJECTS:
        return (
            "If formulas, equations, ratios, measurements, coordinates, units, graphs, or expressions appear, "
            "write them in a clean readable line format. Where true mathematical notation is needed, use MathJax-friendly LaTeX delimiters."
        )

    extra_4c = ""
    if structure == "4Cs":
        extra_4c = """
Additional 4Cs rule:
- In 4Cs lessons, do NOT split mathematical expressions into fragments across bullets.
- Write full equations and full expressions in one clean line.
- Do NOT write things like \\(y\\) = \\(2x + 1\\); instead write \\(y = 2x + 1\\).
- Do NOT wrap isolated variables such as x, y, a, b, m, or c unless they are part of a full equation or expression.
""".strip()

    return f"""
CRITICAL MATH / FORMULA RULES:
- This subject may include mathematical or symbolic notation.
- Write clean, readable mathematical lines for expressions and formulas.
- Inline maths must use \\( ... \\) only when proper math notation is needed.
- Display maths may use \\[ ... \\] for larger expressions.
- Fractions should be written clearly, for example \\(\\frac{{x+3}}{{4}}\\), and also remain understandable as a clean line.
- Square roots should be written clearly, for example \\(\\sqrt{{x/2}}\\).
- The quadratic formula should be written as a full line such as \\(x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}\\).
- Coordinates should be written as \\((2, -1)\\).
- Quadratic expressions should be written as full expressions like \\(x^2 - 5x + 6 = 0\\).
- Do NOT output malformed delimiters, stray slashes, or broken math fragments.
- Do NOT double-escape delimiters.
- Keep the notation readable even when copied into DOCX as plain text lines.
{extra_4c}
""".strip()


def _build_prompt(
    payload: dict,
    objectives: List[str],
    strand: str,
    resource_suggestions: List[str],
) -> str:
    structure = payload["structure"]
    lesson_type = payload["lesson_type"]
    difficulty = payload["difficulty"]
    subject = payload["subject"]
    grade_level = payload["grade_level"]
    topic = payload["topic"]
    subtopic = payload.get("subtopic", "")
    description = payload.get("description", "")
    user_resources = payload.get("resources", "")
    curriculum = payload["curriculum"]
    is_stem = subject.strip().lower() in STEM_SUBJECTS

    mixed_ability_text = (
        "Include mixed-ability support in the class profile because the selected difficulty is Mixed Ability."
        if difficulty == "Mixed Ability"
        else "Do not include mixed-ability support in the class profile unless it is specifically required."
    )

    section_names = (
        "Creativity, Critical Thinking, Communication, Collaboration"
        if structure == "4Cs"
        else "Engagement, Exploration, Explanation, Evaluation, Extension"
    )

    stem_text = (
        "Include practical or skill-building STEM elements where natural: observation, classification, measuring, problem-solving, data use, or application."
        if is_stem
        else "Do not force STEM language if it does not fit the subject, but keep the lesson skill-based and practical where possible."
    )

    math_rules = _math_output_rules(subject, topic, structure)

    return f"""
Create a polished, curriculum-aligned Caribbean lesson plan that feels like a real teacher wrote it.

Context:
- Curriculum: {curriculum}
- Subject: {subject}
- Grade/Level: {grade_level}
- Topic: {topic}
- Subtopic: {subtopic}
- Strand match: {strand}
- Structure: {structure}
- Lesson type: {lesson_type}
- Difficulty: {difficulty}
- Duration: {payload.get('duration_minutes', 60)} minutes
- Objectives from curriculum engine: {objectives}
- Teacher brief: {description}
- User resources: {user_resources}
- Suggested resources: {resource_suggestions}
- {_teacher_profile_text(payload)}

Required quality rules:
- Keep the lesson classroom-ready, realistic, and teacher-friendly.
- Use Caribbean-appropriate examples or contexts where natural.
- Include learning styles in the class profile.
- {mixed_ability_text}
- {stem_text}
- {math_rules}
- Do not write generic filler.
- Do not repeat the topic unnecessarily.
- Keep every bullet concrete and actionable.
- Sections must use these names exactly: {section_names}
- Reflection should sound like a teacher’s after-lesson review.
- Resources must be plain text items, not clickable links.
- Do NOT include a separate general 'Objectives' block. The lesson should use only specific objectives through domain_objectives.

Structure guidance:
- attainment_target: one strong sentence.
- theme and strand: concise and relevant.
- class_profile.learner_profile: 1 concise paragraph about readiness/interests/needs.
- class_profile.learning_styles: 2 to 4 items such as Visual, Auditory, Kinesthetic.
- class_profile.mixed_ability_support: include ONLY when the selected difficulty is Mixed Ability.
- domain_objectives: one sentence each for cognitive, affective, psychomotor.
- prior_learning: one concise paragraph.
- prior_knowledge_questions: 3 to 5 short, topic-specific questions.
- resources: 3 to 6 realistic items.
- section bullets: 2 to 4 bullets each, with teacher and student actions.
- assessment: 2 to 4 concise bullets.
- assessment_criteria: one concise paragraph.
- apse_pathways: 2 to 4 concise items.
- stem_skills: 0 to 5 concise items.
- reflection: 3 to 5 concise bullets.
""".strip()


def generate_dynamic_lesson_parts(
    payload: dict,
    objectives: List[str],
    strand: str,
    resource_suggestions: List[str],
) -> Optional[Dict[str, Any]]:
    required = ["curriculum", "subject", "grade_level", "topic", "structure", "lesson_type", "difficulty"]
    missing = [key for key in required if not payload.get(key)]
    if missing:
        print("AI DEBUG: Missing lesson payload keys:", missing)
        return None

    if not OPENAI_API_KEY:
        print("AI DEBUG: No OPENAI_API_KEY found.")
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = _build_prompt(payload, objectives, strand, resource_suggestions)
        schema_model = LessonParts4C if payload["structure"] == "4Cs" else LessonParts5E

        response = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=(
                "You are an expert Caribbean curriculum-aligned lesson planner. "
                "Return only structured lesson content that fits the provided schema. "
                "Do not add markdown, code fences, or commentary."
            ),
            input=prompt,
            text_format=schema_model,
        )

        parsed = response.output_parsed
        if not parsed:
            print("AI DEBUG: No parsed output returned.")
            print(f"AI DEBUG: Raw response = {response}")
            return None

        data = parsed.model_dump()

        if payload["difficulty"] != "Mixed Ability":
            data["class_profile"].pop("mixed_ability_support", None)

        if payload["structure"] == "4Cs":
            sections = data.get("sections", {})
            if "Critical_Thinking" in sections:
                sections["Critical Thinking"] = sections.pop("Critical_Thinking")
            data["sections"] = sections

        return data

    except Exception as exc:
        print(f"AI DEBUG: Exception during API call: {type(exc).__name__}: {exc}")
        return None