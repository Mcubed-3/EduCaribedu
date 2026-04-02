from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()


class LessonSections5E(BaseModel):
    Engagement: List[str] = Field(min_length=2, max_length=3)
    Exploration: List[str] = Field(min_length=2, max_length=3)
    Explanation: List[str] = Field(min_length=2, max_length=3)
    Evaluation: List[str] = Field(min_length=2, max_length=3)
    Extension: List[str] = Field(min_length=1, max_length=2)


class LessonSections4C(BaseModel):
    Creativity: List[str] = Field(min_length=2, max_length=3)
    Critical_Thinking: List[str] = Field(min_length=2, max_length=3)
    Communication: List[str] = Field(min_length=2, max_length=3)
    Collaboration: List[str] = Field(min_length=2, max_length=3)


class LessonParts5E(BaseModel):
    prior_knowledge_questions: List[str] = Field(min_length=3, max_length=4)
    resources: List[str] = Field(min_length=3, max_length=5)
    sections: LessonSections5E
    assessment: List[str] = Field(min_length=2, max_length=3)
    reflection: List[str] = Field(min_length=3, max_length=4)


class LessonParts4C(BaseModel):
    prior_knowledge_questions: List[str] = Field(min_length=3, max_length=4)
    resources: List[str] = Field(min_length=3, max_length=5)
    sections: LessonSections4C
    assessment: List[str] = Field(min_length=2, max_length=3)
    reflection: List[str] = Field(min_length=3, max_length=4)


def _build_prompt(payload: dict, objectives: List[str], strand: str, resource_suggestions: List[str]) -> str:
    structure = payload["structure"]
    lesson_type = payload["lesson_type"]
    difficulty = payload["difficulty"]
    subject = payload["subject"]
    grade_level = payload["grade_level"]
    topic = payload["topic"]
    subtopic = payload.get("subtopic", "")
    description = payload.get("description", "")
    user_resources = payload.get("resources", "")

    section_names = (
        "Creativity, Critical Thinking, Communication, Collaboration"
        if structure == "4Cs"
        else "Engagement, Exploration, Explanation, Evaluation, Extension"
    )

    return f"""
Create a concise, classroom-ready lesson plan body.

Style rules:
- Write for a teacher who wants a usable lesson plan, not a long teaching script.
- Keep the output practical, clear, and professional.
- Avoid overly long paragraphs.
- Avoid repeating the topic name in every bullet.
- Keep each bullet focused on one concrete action.
- Give definite classroom activities, not vague suggestions.
- State what the teacher does and what students do.
- Use age-appropriate language for {grade_level}.
- Match the lesson to {subject}.
- Match the topic exactly: "{topic}".
- Use the selected structure exactly: {structure}.
- Use the selected lesson type exactly: {lesson_type}.
- Use the selected difficulty exactly: {difficulty}.
- Keep the lesson realistic for a normal classroom period.
- Prefer standard classroom resources unless the lesson type clearly requires practical materials.
- Do not turn the lesson into a full lab manual unless the lesson type is Practical.
- Do not make the resources list too long.
- Do not make the reflection section too long.
- Keep assessment concise and classroom-appropriate.
- Resources must be plain text only, not clickable links.

Output quality rules:
- Prior knowledge questions must be topic-specific and short.
- Resources should be 3 to 5 concise items.
- Section activities should be detailed enough to use, but not over-explained.
- Most sections should have 2 bullets. A third bullet is only allowed if truly needed.
- Assessment should be 2 or 3 concise bullets.
- Reflection should be 3 or 4 concise bullets.
- If practical, include hands-on activity steps, but keep them summary-level.
- If theory or discussion, avoid pretending it is a lab.

Curriculum context:
Curriculum: {payload['curriculum']}
Subject: {subject}
Grade/Level: {grade_level}
Topic: {topic}
Subtopic: {subtopic}
Strand: {strand}
Objectives: {objectives}
Teacher description: {description}
User-supplied resources: {user_resources}
Suggested resources: {resource_suggestions}

Important:
- The sections must use these names exactly: {section_names}
- The output should feel varied and natural, not repetitive.
- The lesson must align with the listed objectives.
- Keep the overall tone concise, polished, and teacher-friendly.
""".strip()


def generate_dynamic_lesson_parts(
    payload: dict,
    objectives: List[str],
    strand: str,
    resource_suggestions: List[str],
) -> Optional[Dict[str, Any]]:
    if not OPENAI_API_KEY:
        print("AI DEBUG: No OPENAI_API_KEY found.")
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = _build_prompt(payload, objectives, strand, resource_suggestions)

        schema_model = LessonParts4C if payload["structure"] == "4Cs" else LessonParts5E

        print(f"AI DEBUG: Calling model {OPENAI_MODEL} with Pydantic structured parsing...")

        response = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=(
                "You are an expert Caribbean curriculum-aligned lesson planner. "
                "Produce concise, high-quality, classroom-ready lesson content. "
                "Do not be verbose. Do not output a teaching script. "
                "Return content that fits the provided schema."
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

        if payload["structure"] == "4Cs":
            sections = data.get("sections", {})
            if "Critical_Thinking" in sections:
                sections["Critical Thinking"] = sections.pop("Critical_Thinking")
            data["sections"] = sections

        print("AI DEBUG: Parsed structured output successfully.")
        return data

    except Exception as e:
        print(f"AI DEBUG: Exception during API call: {type(e).__name__}: {e}")
        return None