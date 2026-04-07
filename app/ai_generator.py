from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from .math_bank_service import format_math_bank_for_prompt

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

STEM_SUBJECTS = {
    "agricultural science",
    "agriculture",
    "mathematics",
    "math",
    "biology",
    "chemistry",
    "physics",
    "integrated science",
    "science",
    "information technology",
    "it",
    "resource and technology",
    "engineering and mechanisms",
    "industrial techniques",
    "geography",
}

MATH_HEAVY_SUBJECTS = {
    "agricultural science",
    "agriculture",
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
    "resource and technology",
    "engineering and mechanisms",
    "industrial techniques",
    "business basics",
}


class ClassProfile(BaseModel):
    learner_profile: str = Field(min_length=20, max_length=420)
    learning_styles: List[str] = Field(min_length=2, max_length=4)
    mixed_ability_support: Optional[str] = None


class DomainObjectives(BaseModel):
    cognitive: str = Field(min_length=12, max_length=240)
    affective: str = Field(min_length=12, max_length=240)
    psychomotor: str = Field(min_length=12, max_length=240)


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
    attainment_target: str = Field(min_length=20, max_length=420)
    theme: str = Field(min_length=3, max_length=140)
    strand: str = Field(min_length=3, max_length=140)
    class_profile: ClassProfile
    domain_objectives: DomainObjectives
    prior_learning: str = Field(min_length=20, max_length=420)
    prior_knowledge_questions: List[str] = Field(min_length=3, max_length=5)
    resources: List[str] = Field(min_length=3, max_length=6)
    sections: LessonSections5E
    assessment: List[str] = Field(min_length=2, max_length=4)
    assessment_criteria: str = Field(min_length=20, max_length=420)
    apse_pathways: List[str] = Field(min_length=2, max_length=4)
    stem_skills: List[str] = Field(default_factory=list, max_length=5)
    reflection: List[str] = Field(min_length=3, max_length=5)


class LessonParts4C(BaseModel):
    attainment_target: str = Field(min_length=20, max_length=420)
    theme: str = Field(min_length=3, max_length=140)
    strand: str = Field(min_length=3, max_length=140)
    class_profile: ClassProfile
    domain_objectives: DomainObjectives
    prior_learning: str = Field(min_length=20, max_length=420)
    prior_knowledge_questions: List[str] = Field(min_length=3, max_length=5)
    resources: List[str] = Field(min_length=3, max_length=6)
    sections: LessonSections4C
    assessment: List[str] = Field(min_length=2, max_length=4)
    assessment_criteria: str = Field(min_length=20, max_length=420)
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


def _math_output_rules(subject: str, topic: str, structure: str, grade_level: str, curriculum: str) -> str:
    subject_key = (subject or "").strip().lower()

    math_bank_snippets = format_math_bank_for_prompt(
        subject=subject,
        grade_level=grade_level,
        curriculum=curriculum,
        topic=topic,
        limit=6,
    )

    strict_rules = f"""
CRITICAL MATH OUTPUT RULES (STRICT):
- NEVER use LaTeX.
- NEVER use backslashes.
- NEVER use \\( \\), \\[ \\], \\frac, \\sqrt, superscript braces, subscript braces, or escaped symbols.
- Write ALL expressions in clean plain text only.
- Use the math bank examples below whenever they fit the lesson naturally.

Math bank examples:
{math_bank_snippets}

Required plain-text style examples:
x^2 - 5x + 6 = 0
(x + 3) / 4
√(x/2)
x = (-b ± √(b^2 - 4ac)) / 2a
y = 2x + 1
(2, -1)
3/4
m^2
cm^3
12%

Formatting rules:
- Keep each equation on one line
- Do not split expressions across bullets or sentences
- Do not wrap variables in brackets
- If a formula is needed, write it exactly as a readable line, not as markup
- If a table is needed for business/accounts/family consumer management, use a clean text-table style
"""

    if subject_key not in MATH_HEAVY_SUBJECTS:
        return (
            strict_rules
            + f"""

Use these rules only when {subject} naturally requires calculations, formulas, measurement, coordinates, ratios, data handling, equations, graphs, or numerical reasoning in the topic '{topic}'.
If no math is needed, do not force math into the lesson.
"""
        )

    extra_4c = ""
    if structure == "4Cs":
        extra_4c = """
Additional 4Cs rule:
- In 4Cs lessons, do not split one calculation or equation into separate bullets.
- Keep each full expression or worked example together in one bullet.
"""

    return (
        strict_rules
        + f"""

This lesson topic may naturally require mathematical or symbolic notation.
Use only clean readable plain-text math for the topic '{topic}' in the subject '{subject}'.
{extra_4c}
"""
    )


def _quality_rules(subject: str, topic: str, structure: str, difficulty: str, lesson_type: str) -> str:
    return f"""
QUALITY RULES:
- Make the lesson feel like it was written by a real Caribbean teacher.
- Keep the subject and topic aligned naturally. Do not force another subject into the lesson.
- Avoid generic filler.
- Avoid repetition of the topic title in every line.
- Use realistic classroom actions for teacher and students.
- Keep all bullets actionable and classroom-ready.
- Make examples, scenarios, and applications feel Caribbean where natural.
- Keep the lesson appropriate for {difficulty} level.
- Make the structure genuinely reflect {structure}, not just relabel generic bullets.
- Make the lesson type genuinely reflect {lesson_type}.
- If the topic is practical or skill-based, include practical handling, observation, demonstration, performance, or worked examples where appropriate.
"""


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
        "Include practical or skill-building STEM elements where natural: observation, classification, measuring, problem-solving, data use, experimentation, design, or application."
        if is_stem
        else "Do not force STEM language if it does not fit the subject, but keep the lesson skill-based and practical where appropriate."
    )

    math_rules = _math_output_rules(subject, topic, structure, grade_level, curriculum)
    quality_rules = _quality_rules(subject, topic, structure, difficulty, lesson_type)

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

{quality_rules}

Additional rules:
- Include learning styles in the class profile.
- {mixed_ability_text}
- {stem_text}
- {math_rules}
- Sections must use these names exactly: {section_names}
- Reflection should sound like a teacher's after-lesson review.
- Do not include a separate general Objectives block. Use only specific objectives through domain_objectives.

Structure guidance:
- attainment_target: one strong sentence
- theme and strand: concise and relevant
- class_profile.learner_profile: 1 concise paragraph about readiness, interests, and needs
- class_profile.learning_styles: 2 to 4 items such as Visual, Auditory, Kinesthetic
- class_profile.mixed_ability_support: include only when the selected difficulty is Mixed Ability
- domain_objectives: one sentence each for cognitive, affective, psychomotor
- prior_learning: one concise paragraph
- prior_knowledge_questions: 3 to 5 short, topic-specific questions
- resources: 3 to 6 realistic items
- section bullets: 2 to 4 bullets each, with clear teacher and student actions
- assessment: 2 to 4 concise bullets
- assessment_criteria: one concise paragraph
- apse_pathways: 2 to 4 concise items
- stem_skills: 0 to 5 concise items
- reflection: 3 to 5 concise bullets
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
        print("AI DEBUG: Starting request...")
        print("AI DEBUG: OPENAI_API_KEY present:", bool(OPENAI_API_KEY))
        print("AI DEBUG: MODEL:", OPENAI_MODEL)

        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = _build_prompt(payload, objectives, strand, resource_suggestions)
        schema_model = LessonParts4C if payload["structure"] == "4Cs" else LessonParts5E

        response = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=(
                "You are an expert Caribbean curriculum-aligned lesson planner. "
                "Return only structured lesson content that fits the provided schema. "
                "Do not add markdown, code fences, commentary, JSON wrappers, or formatting markup. "
                "All mathematical, scientific, financial, and technical expressions must be plain readable text, never LaTeX."
            ),
            input=prompt,
            text_format=schema_model,
        )

        print("AI DEBUG: Response received")

        parsed = response.output_parsed
        if not parsed:
            print("AI DEBUG: No parsed output returned.")
            print(f"AI DEBUG: Raw response = {response}")
            return None

        data = parsed.model_dump()
        print("AI DEBUG SUCCESS:", data)

        if payload["difficulty"] != "Mixed Ability":
            data["class_profile"].pop("mixed_ability_support", None)

        if payload["structure"] == "4Cs":
            sections = data.get("sections", {})
            if "Critical_Thinking" in sections:
                sections["Critical Thinking"] = sections.pop("Critical_Thinking")
            data["sections"] = sections

        return data

    except Exception as exc:
        print("AI DEBUG: Exception during API call:", type(exc).__name__, str(exc))
        return None