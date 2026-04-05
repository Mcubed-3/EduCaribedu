import json
import openai


def generate_dynamic_lesson_parts(payload, objectives, strand, resource_suggestions):
    subject = payload["subject"]
    topic = payload["topic"]
    grade = payload["grade_level"]
    difficulty = payload["difficulty"]
    lesson_type = payload["lesson_type"]
    duration = payload["duration_minutes"]

    stem_subjects = ["math", "mathematics", "science", "biology", "chemistry", "physics", "it"]
    include_stem = subject.lower() in stem_subjects

    prompt = f"""
You are an expert Caribbean teacher following official curriculum standards.

Create a FULL professional lesson plan.

-------------------------------------
CONTEXT:
Subject: {subject}
Grade: {grade}
Topic: {topic}
Difficulty: {difficulty}
Lesson Type: {lesson_type}
Duration: {duration} minutes
Strand: {strand}

Objectives:
{objectives}

-------------------------------------

REQUIREMENTS:

1. Use FULL lesson structure:
- Attainment Target
- Theme
- Strand
- Class Profile (learning styles + mixed ability)
- Objectives (Cognitive, Affective, Psychomotor)
- Prior Learning
- Engage
- Explore
- Explain
- Elaborate
- Evaluate
- Assessment Criteria
- Reflection

2. MUST include:
- Visual, auditory, kinesthetic strategies
- Mixed ability differentiation
- Real classroom activities (NOT generic)
- Teacher + student roles

3. Include APSE pathways:
- Careers
- Real-world skills

4. {"Include STEM skills and practical elements." if include_stem else ""}

5. Caribbean context:
- Use relatable classroom examples

-------------------------------------

RETURN JSON:

{{
  "attainment_target": "...",
  "theme": "...",
  "strand": "...",

  "class_profile": {{
    "learning_styles": "...",
    "needs": "..."
  }},

  "objectives": {{
    "cognitive": "...",
    "affective": "...",
    "psychomotor": "..."
  }},

  "prior_learning": "...",

  "engage": "...",
  "explore": "...",
  "explain": "...",
  "elaborate": "...",
  "evaluate": "...",

  "assessment_criteria": "...",

  "apse_pathways": "...",

  "stem_skills": "...",

  "reflection": "..."
}}

NO extra text. Only JSON.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("AI ERROR:", e)
        return None