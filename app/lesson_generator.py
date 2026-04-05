from __future__ import annotations
from typing import Dict, List
import hashlib
import json

from .ai_generator import generate_dynamic_lesson_parts
from .engine_state import engine

CACHE = {}

def cache_key(payload):
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def generate_lesson(payload: dict) -> dict:
    key = cache_key(payload)
    if key in CACHE:
        return CACHE[key]

    curriculum = payload.get("curriculum", "")
    subject = payload.get("subject", "")
    grade = payload.get("grade_level", "")
    topic = payload.get("topic", "")
    difficulty = payload.get("difficulty", "Intermediate")

    # ---- OBJECTIVES ----
    objectives = engine.build_objectives(
        curriculum,
        subject,
        grade,
        topic,
        3,
        difficulty,
        payload.get("description", ""),
    )
    objective_text = [o["text"] for o in objectives]

    # ---- BASE STRUCTURE ----
    lesson = {
        "curriculum": curriculum,
        "subject": subject,
        "grade_level": grade,
        "topic": topic,
        "difficulty": difficulty,
        "structure": "5Es",
        "generation_mode": "fallback",

        "attainment_target": f"Students understand and apply concepts of {topic}.",
        "theme": topic,
        "strand": "General Strand",

        "class_profile": {
            "learning_styles": ["Visual", "Auditory", "Kinesthetic"],
            "mixed_ability_support": "Differentiation, scaffolding, and extension tasks included.",
        },

        "objectives": objective_text,

        "prior_learning": f"Students have basic familiarity with concepts related to {topic}.",

        "sections": {
            "Engagement": [f"Introduce {topic} using real-world example."],
            "Exploration": [f"Students investigate {topic} through guided activity."],
            "Explanation": [f"Teacher explains key concepts of {topic}."],
            "Evaluation": ["Quick assessment or exit ticket."],
            "Extension": ["Apply knowledge in real-world context."]
        },

        "assessment": ["Questioning", "Exit ticket"],
        "assessment_criteria": "Accuracy, understanding, application",

        "apse_pathways": ["Problem solving", "Collaboration"],
        "stem_skills": ["Critical thinking", "Analysis"],

        "reflection": [
            "What worked well?",
            "What needs improvement?"
        ],
    }

    # ---- AI ENHANCEMENT ----
    try:
        ai = generate_dynamic_lesson_parts(
            payload=payload,
            objectives=objective_text,
            strand="General Strand",
            resource_suggestions=[]
        )

        if ai:
            lesson["generation_mode"] = "ai-enhanced"

            if ai.get("sections"):
                lesson["sections"].update(ai["sections"])

            lesson["reflection"] = ai.get("reflection", lesson["reflection"])

    except Exception as e:
        print("AI ERROR:", e)

    result = {
        "title": f"{subject} Lesson Plan - {topic}",
        "lesson": lesson
    }

    CACHE[key] = result
    return result


def format_objectives(objectives: List[Dict[str, str]]) -> List[str]:
    return [obj["text"] for obj in objectives]


def _prior_questions(topic: str, subject: str, difficulty: str) -> List[str]:
    questions = [
        f"What do you already know about {topic}?",
        f"Where have you seen or heard about {topic} in everyday life?",
        f"What words, ideas, or examples come to mind when you hear '{topic}'?",
    ]

    subject_map = {
        "Biology": [
            f"What life processes or biological ideas connect to {topic}?",
            f"How might {topic} help living organisms survive or function?",
        ],
        "Mathematics": [
            f"What previous math skill or idea is related to {topic}?",
            f"Have you used {topic} before in a calculation or real-life problem?",
        ],
        "English": [
            f"What have you already read, written, or discussed that connects to {topic}?",
            f"What language features or communication skills might be useful in a lesson on {topic}?",
        ],
        "Language Arts": [
            f"What reading, writing, speaking, or language ideas connect to {topic}?",
            f"What examples from previous lessons relate to {topic}?",
        ],
        "Integrated Science": [
            f"What scientific ideas or observations already connect to {topic}?",
            f"What experiment, model, or investigation could help us understand {topic}?",
        ],
        "Social Studies": [
            f"What people, places, events, or issues connect to {topic}?",
            f"How does {topic} relate to community, society, or the wider world?",
        ],
        "Agricultural Science": [
            f"What farming, crop, or livestock ideas already connect to {topic}?",
            f"How does {topic} support Caribbean food production or farm management?",
        ],
    }

    questions.extend(subject_map.get(subject, []))

    if difficulty == "Beginner":
        questions.append(f"What simple fact or example do you already know about {topic}?")
    elif difficulty == "Advanced":
        questions.append(f"What deeper question or problem about {topic} would you like to explore?")

    deduped = []
    for question in questions:
        if question not in deduped:
            deduped.append(question)

    return deduped[:5]


def _resources(match: Dict, user_resources: str, subject: str, topic: str, lesson_type: str) -> List[str]:
    items = list(match.get("resources", []))

    fallback = [
        f"{subject} textbook section on {topic}",
        f"Teacher-made notes or slides on {topic}",
        f"Board, projector, or chart paper for class discussion",
    ]

    if subject.strip().lower() == "agricultural science":
        fallback.extend([
            f"Images or cards showing examples linked to {topic}",
            "Local or Caribbean farm examples for discussion",
        ])

    if lesson_type == "Practical":
        fallback.extend([
            f"Worksheet or activity sheet on {topic}",
            f"Simple classroom materials for a practical activity on {topic}",
        ])

    items.extend(fallback)

    if user_resources:
        items.extend([part.strip() for part in user_resources.split(",") if part.strip()])

    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)

    return deduped[:6]


def _build_4c_sections(topic: str, subject: str, lesson_type: str, difficulty: str, objectives: List[str]) -> Dict[str, List[str]]:
    creativity = [
        f"Begin with a creative hook connected to {topic}, such as an image, scenario, prompt, demonstration, or quick challenge.",
        f"Students generate examples, ideas, or representations that show what they think or know about {topic}.",
    ]

    critical_thinking = [
        f"Guide students through one or two tasks that require them to examine, compare, explain, solve, or investigate an aspect of {topic}.",
        f"Teacher questioning pushes students toward {difficulty.lower()}-level thinking using the lesson objectives as a guide.",
    ]

    communication = [
        f"Students explain their reasoning, findings, or ideas about {topic} orally or in writing.",
        "Teacher checks for clear expression, subject vocabulary, and accurate understanding.",
    ]

    collaboration = [
        f"Pairs or groups complete a short activity, discussion, sort, investigation, or problem-solving task related to {topic}.",
        "Students share a final response, conclusion, or product with the class.",
    ]

    if subject == "Biology":
        creativity[1] = f"Students sketch, label, sort, or brainstorm biological examples linked to {topic}."
        critical_thinking[0] = f"Students interpret biological information, diagrams, or short data tasks related to {topic}."
    elif subject == "Mathematics":
        creativity[1] = f"Students suggest examples, patterns, or real-life uses of {topic}."
        critical_thinking[0] = f"Students solve guided and independent problems connected to {topic} and explain their reasoning."
    elif subject in ["English", "Language Arts"]:
        communication[0] = f"Students discuss, present, write, or respond using ideas linked to {topic}."
    elif subject == "Integrated Science":
        critical_thinking[0] = f"Students analyze scientific examples, observations, or investigations related to {topic}."
    elif subject == "Agricultural Science":
        critical_thinking[0] = f"Students compare and classify examples linked to {topic} and connect them to Caribbean farming needs."
        collaboration[0] = f"Pairs or groups complete a card sort, comparison chart, or decision-making task related to {topic}."

    if lesson_type == "Practical":
        collaboration[0] = f"Pairs or groups complete a hands-on task or short investigation related to {topic}."
    elif lesson_type == "Discussion":
        communication[0] = f"Students explain, discuss, justify, and respond to ideas connected to {topic}."

    if difficulty == "Advanced":
        critical_thinking.append(f"Include a deeper task where students justify, analyze, or evaluate an aspect of {topic}.")
        communication.append("Students defend their thinking using appropriate subject vocabulary and evidence.")

    return {
        "Creativity": creativity,
        "Critical Thinking": critical_thinking,
        "Communication": communication,
        "Collaboration": collaboration,
    }


def _build_5e_sections(topic: str, subject: str, lesson_type: str, difficulty: str, objectives: List[str]) -> Dict[str, List[str]]:
    engagement = [
        f"Use a short warm-up, image, question, demonstration, or real-life scenario to introduce {topic}.",
        f"Activate students' interest and connect the lesson to prior knowledge about {topic}.",
    ]

    exploration = [
        f"Students investigate {topic} through examples, data, text, teacher-guided tasks, or paired/group activity.",
        f"Teacher circulates, probes thinking, and identifies misconceptions related to {topic}.",
    ]

    explanation = [
        f"Teacher facilitates discussion and clarifies the key concepts, vocabulary, and processes linked to {topic}.",
        "Students explain what they discovered and connect their ideas to the lesson objectives.",
    ]

    evaluation = [
        f"Use a formative check such as an exit ticket, mini quiz, oral questioning, short paragraph response, or worked task focused on {topic}.",
        f"Assess understanding against the lesson objectives for {topic}.",
    ]

    extension = [
        f"Provide homework, enrichment, or a real-world application task related to {topic}.",
        f"Students extend learning beyond the lesson through a brief follow-up activity on {topic}.",
    ]

    if subject == "Biology":
        exploration[0] = f"Students investigate {topic} through labelled diagrams, short experimental data, observation tasks, or a simple biological investigation."
        explanation[0] = f"Teacher clarifies the biological structures, functions, and processes involved in {topic}."
        extension[0] = f"Students apply learning on {topic} to living organisms, health, or environmental examples."
    elif subject == "Mathematics":
        exploration[0] = f"Students explore {topic} through worked examples, guided practice, pattern spotting, or real-life problems."
        explanation[0] = f"Teacher models the steps, rules, and reasoning involved in {topic}."
        evaluation[0] = f"Use a worked example, mini quiz, oral questioning, or short problem-solving task to assess understanding of {topic}."
        extension[0] = f"Students apply {topic} to homework, a word problem, or a real-world numerical situation."
    elif subject in ["English", "Language Arts"]:
        engagement[0] = f"Use a prompt, short text, question, discussion starter, or language example to introduce {topic}."
        exploration[0] = f"Students explore {topic} through reading, writing, speaking, listening, or text-based activities."
        explanation[0] = f"Teacher clarifies the language or literary ideas linked to {topic}, using examples from student responses or texts."
    elif subject == "Integrated Science":
        exploration[0] = f"Students explore {topic} through scientific examples, observations, simple data, or a guided practical task."
        explanation[0] = f"Teacher helps students explain the scientific concepts, processes, or systems related to {topic}."
    elif subject == "Social Studies":
        exploration[0] = f"Students explore {topic} through case examples, short texts, discussion prompts, or issue-based tasks."
        explanation[0] = f"Teacher clarifies the key social, civic, or environmental ideas related to {topic}."
    elif subject == "Agricultural Science":
        engagement[0] = f"Use photos, breed cards, a farm scenario, or a quick sorting activity to introduce {topic}."
        exploration[0] = f"Students examine examples, images, fact cards, or comparison charts linked to {topic}, with emphasis on Caribbean farming contexts."
        explanation[0] = f"Teacher clarifies important terms, characteristics, and practical farm uses linked to {topic}."
        extension[0] = f"Students apply learning on {topic} to Caribbean farming needs, management choices, or small-scale enterprise ideas."

    if lesson_type == "Practical":
        exploration[0] = f"Students investigate {topic} through a practical activity, observation, experiment, or hands-on task."
        evaluation.append("Assess how well students carry out the practical activity and interpret their results or observations.")
    elif lesson_type == "Discussion":
        engagement[1] = f"Use discussion to activate students' interest and draw out prior ideas about {topic}."
        explanation[1] = f"Students explain and justify their ideas about {topic} during guided discussion."

    if difficulty == "Beginner":
        explanation.append(f"Teacher provides simple examples, modelling, and guided support to help students understand {topic}.")
    elif difficulty == "Advanced":
        evaluation.append(f"Include a deeper question that asks students to analyze, justify, or evaluate an aspect of {topic}.")
        extension.append(f"Challenge students to independently research, compare, or apply {topic} in a new context.")

    return {
        "Engagement": engagement,
        "Exploration": exploration,
        "Explanation": explanation,
        "Evaluation": evaluation,
        "Extension": extension,
    }


def _build_sections(structure: str, topic: str, subject: str, lesson_type: str, difficulty: str, objectives: List[str]) -> Dict[str, List[str]]:
    if structure == "4Cs":
        return _build_4c_sections(topic, subject, lesson_type, difficulty, objectives)
    return _build_5e_sections(topic, subject, lesson_type, difficulty, objectives)


def _build_reflection(topic: str, subject: str, difficulty: str) -> List[str]:
    reflection = [
        f"How well did students meet the lesson objectives for {topic}?",
        f"What misconceptions or difficulties became clear during the lesson on {topic}?",
        f"What should be adjusted, strengthened, or simplified the next time {topic} is taught?",
    ]

    if subject == "Biology":
        reflection.append(f"Were students able to use correct biological terms and explain the processes involved in {topic}?")
    elif subject == "Mathematics":
        reflection.append(f"Were students able to show accurate working and explain their reasoning for tasks related to {topic}?")
    elif subject in ["English", "Language Arts"]:
        reflection.append(f"Did students communicate their ideas clearly and use appropriate language related to {topic}?")
    elif subject == "Agricultural Science":
        reflection.append(f"Were students able to connect the content to Caribbean farming needs, safe practice, or farm decision-making?")

    if difficulty == "Beginner":
        reflection.append(f"Did students need more scaffolding, modelling, or simpler examples to understand {topic}?")
    elif difficulty == "Advanced":
        reflection.append(f"Could students have been challenged further through more independent, analytical, or evaluative tasks on {topic}?")

    return reflection[:5]


def _fallback_domain_objectives(topic: str, subject: str) -> Dict[str, str]:
    return {
        "cognitive": f"Students explain and apply the key ideas related to {topic} in {subject}.",
        "affective": f"Students show appreciation for the value and relevance of {topic} in classroom and real-life settings.",
        "psychomotor": f"Students complete a practical, written, oral, or visual task linked to {topic}.",
    }


def _fallback_class_profile(subject: str, difficulty: str) -> Dict[str, object]:
    return {
        "learner_profile": f"This class includes learners with varied readiness levels, interests, and prior knowledge in {subject}. The lesson should provide clear explanations, modelling, and opportunities for guided and independent work.",
        "learning_styles": ["Visual", "Auditory", "Kinesthetic"],
        "mixed_ability_support": f"Provide scaffolds, peer support, teacher check-ins, and extension prompts so {difficulty.lower()}-level learners can all participate meaningfully.",
    }


def _fallback_prior_learning(topic: str, subject: str) -> str:
    return f"Students should already have some basic background knowledge, vocabulary, or everyday experience connected to {topic} in {subject}."


def _fallback_assessment_criteria(topic: str) -> str:
    return f"Students should accurately use key vocabulary, respond to questions or tasks on {topic}, and demonstrate understanding through discussion, written work, or practical application."


def _fallback_apse_pathways(topic: str, subject: str) -> List[str]:
    return [
        f"Career awareness linked to {subject} and the study of {topic}",
        f"Communication, teamwork, and problem-solving through classroom tasks on {topic}",
        f"Real-world application of {topic} to community, work, or everyday decision-making",
    ]


def _fallback_stem_skills(subject: str, topic: str) -> List[str]:
    if subject.strip().lower() not in STEM_SUBJECTS:
        return []
    return [
        f"Observation and analysis linked to {topic}",
        "Problem-solving and evidence-based thinking",
        "Practical application of subject knowledge",
    ]


def _normalize_ai_sections(structure: str, ai_sections: Dict, fallback_sections: Dict[str, List[str]]) -> Dict[str, List[str]]:
    expected = FOUR_C_SECTIONS if structure == "4Cs" else FIVE_E_SECTIONS
    normalized: Dict[str, List[str]] = {}

    for section_name in expected:
        value = ai_sections.get(section_name)
        if isinstance(value, list) and value:
            normalized[section_name] = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            normalized[section_name] = [value.strip()]
        else:
            normalized[section_name] = fallback_sections.get(section_name, [])

    return normalized


def generate_lesson(payload: dict) -> dict:
    payload["grade_level"] = payload.get("grade_level") or payload.get("grade") or ""
    payload["structure"] = payload.get("structure") or "5Es"
    payload["difficulty"] = payload.get("difficulty") or "Intermediate"
    payload["lesson_type"] = payload.get("lesson_type") or "Theory"
    payload["objective_count"] = payload.get("objective_count") or 3
    payload["duration_minutes"] = payload.get("duration_minutes") or 60

    objectives = engine.build_objectives(
        payload["curriculum"],
        payload["subject"],
        payload["grade_level"],
        payload["topic"],
        payload["objective_count"],
        payload["difficulty"],
        payload.get("description", ""),
    )

    search_result = engine.search(
        payload["curriculum"],
        payload["subject"],
        payload["grade_level"],
        payload["topic"],
        payload.get("description", ""),
    )
    match = search_result.get("match") or {}
    objective_text = format_objectives(objectives)

    fallback_sections = _build_sections(
        payload["structure"],
        payload["topic"],
        payload["subject"],
        payload["lesson_type"],
        payload["difficulty"],
        objective_text,
    )
    fallback_prior = _prior_questions(payload["topic"], payload["subject"], payload["difficulty"])
    fallback_resources = _resources(
        match,
        payload.get("resources", ""),
        payload["subject"],
        payload["topic"],
        payload["lesson_type"],
    )
    fallback_reflection = _build_reflection(payload["topic"], payload["subject"], payload["difficulty"])
    fallback_assessment = [
        f"Check students' responses against the stated objectives for {payload['topic']}.",
        "Use oral questioning and at least one written or performance-based task to gather evidence of learning.",
    ]

    fallback_lesson = {
        "curriculum": payload["curriculum"],
        "subject": payload["subject"],
        "grade_level": payload["grade_level"],
        "topic": payload["topic"],
        "subtopic": payload.get("subtopic") or "",
        "structure": payload["structure"],
        "difficulty": payload["difficulty"],
        "lesson_type": payload["lesson_type"],
        "duration_minutes": payload["duration_minutes"],
        "description": payload.get("description") or "",
        "attainment_target": match.get("attainment_target", "") or f"Students build understanding and practical application related to {payload['topic']}.",
        "theme": match.get("theme", "") or "Curriculum theme",
        "strand": match.get("strand", "") or "General Strand",
        "class_profile": _fallback_class_profile(payload["subject"], payload["difficulty"]),
        "domain_objectives": _fallback_domain_objectives(payload["topic"], payload["subject"]),
        "prior_learning": _fallback_prior_learning(payload["topic"], payload["subject"]),
        "objectives": objective_text,
        "suggested_standards": [match.get("strand", "General Strand")],
        "prior_knowledge_questions": fallback_prior,
        "resources": fallback_resources,
        "sections": fallback_sections,
        "assessment": fallback_assessment,
        "assessment_criteria": _fallback_assessment_criteria(payload["topic"]),
        "apse_pathways": _fallback_apse_pathways(payload["topic"], payload["subject"]),
        "stem_skills": _fallback_stem_skills(payload["subject"], payload["topic"]),
        "reflection": fallback_reflection,
        "generation_mode": "fallback",
    }

    ai_parts = generate_dynamic_lesson_parts(
        payload=payload,
        objectives=objective_text,
        strand=match.get("strand", "General Strand"),
        resource_suggestions=fallback_resources,
    )

    lesson = dict(fallback_lesson)

    if ai_parts:
        lesson["attainment_target"] = ai_parts.get("attainment_target", lesson["attainment_target"])
        lesson["theme"] = ai_parts.get("theme", lesson["theme"])
        lesson["strand"] = ai_parts.get("strand", lesson["strand"])
        lesson["class_profile"] = ai_parts.get("class_profile", lesson["class_profile"])
        lesson["domain_objectives"] = ai_parts.get("domain_objectives", lesson["domain_objectives"])
        lesson["prior_learning"] = ai_parts.get("prior_learning", lesson["prior_learning"])
        lesson["prior_knowledge_questions"] = ai_parts.get("prior_knowledge_questions", lesson["prior_knowledge_questions"])
        lesson["resources"] = ai_parts.get("resources", lesson["resources"])
        lesson["sections"] = _normalize_ai_sections(payload["structure"], ai_parts.get("sections", {}), fallback_sections)
        lesson["assessment"] = ai_parts.get("assessment", lesson["assessment"])
        lesson["assessment_criteria"] = ai_parts.get("assessment_criteria", lesson["assessment_criteria"])
        lesson["apse_pathways"] = ai_parts.get("apse_pathways", lesson["apse_pathways"])
        lesson["stem_skills"] = ai_parts.get("stem_skills", lesson["stem_skills"])
        lesson["reflection"] = ai_parts.get("reflection", lesson["reflection"])
        lesson["generation_mode"] = "ai"

    return {
        "title": f"{payload.get('subject', '')} Lesson Plan - {payload.get('topic', '')}",
        "curriculum_match": match,
        "lesson": lesson,
    }
