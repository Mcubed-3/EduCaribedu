from __future__ import annotations

import hashlib
import json
import re
from typing import Dict, List

from .ai_generator import generate_dynamic_lesson_parts
from .engine_state import engine

FIVE_E_SECTIONS = ["Engagement", "Exploration", "Explanation", "Evaluation", "Extension"]
FOUR_C_SECTIONS = ["Creativity", "Critical Thinking", "Communication", "Collaboration"]

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

CACHE: Dict[str, dict] = {}


def cache_key(payload: dict) -> str:
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def format_objectives(objectives: List[Dict[str, str]]) -> List[str]:
    return [obj["text"] for obj in objectives]


def _clean_math_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    cleaned = text
    cleaned = re.sub(r"\\\(|\\\)", "", cleaned)
    cleaned = re.sub(r"\\\[|\\\]", "", cleaned)
    cleaned = cleaned.replace("\\", "")
    cleaned = re.sub(r"\^\{(\d+)\}", r"^\1", cleaned)
    cleaned = re.sub(r"\^\{([A-Za-z0-9]+)\}", r"^\1", cleaned)
    cleaned = cleaned.replace("sqrt", "√")
    cleaned = cleaned.replace('"', "")
    cleaned = cleaned.replace("{", "")
    cleaned = cleaned.replace("}", "")
    cleaned = cleaned.replace("dfrac", "")
    cleaned = cleaned.replace("tfrac", "")
    cleaned = cleaned.replace("pm", "±")
    cleaned = cleaned.replace("Rightarrow", "=>")
    cleaned = cleaned.replace("Delta", "discriminant")
    cleaned = cleaned.replace("cdot", "*")
    cleaned = cleaned.replace("bigl", "")
    cleaned = cleaned.replace("bigr", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _clean_math_list(items):
    if not isinstance(items, list):
        return items
    return [_clean_math_text(str(item)) for item in items if str(item).strip()]


def _clean_domain_objectives(obj: Dict[str, str]) -> Dict[str, str]:
    if not isinstance(obj, dict):
        return obj
    return {
        "cognitive": _clean_math_text(obj.get("cognitive", "")),
        "affective": _clean_math_text(obj.get("affective", "")),
        "psychomotor": _clean_math_text(obj.get("psychomotor", "")),
    }


def _clean_class_profile(profile: Dict[str, object]) -> Dict[str, object]:
    if not isinstance(profile, dict):
        return profile

    cleaned = {
        "learner_profile": _clean_math_text(str(profile.get("learner_profile", ""))),
        "learning_styles": profile.get("learning_styles", []),
    }

    if profile.get("mixed_ability_support"):
        cleaned["mixed_ability_support"] = _clean_math_text(str(profile.get("mixed_ability_support", "")))

    return cleaned


def _resolve_from_profile(payload: dict) -> dict:
    profile = payload.get("teacher_profile") or {}

    if not payload.get("curriculum") and profile.get("curriculum"):
        payload["curriculum"] = profile["curriculum"]

    if not payload.get("subject") and profile.get("subjects"):
        payload["subject"] = profile["subjects"][0]

    if not payload.get("grade_level") and profile.get("grade_levels"):
        payload["grade_level"] = profile["grade_levels"][0]

    return payload


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
    if s in {"business basics", "jace", "accounts", "accounting"}:
        return "enterprise"
    if s in {"drama", "music", "visual arts"}:
        return "creative_arts"

    return "general"


def _prior_questions(topic: str, subject: str, difficulty: str) -> List[str]:
    group = _subject_group(subject)

    common = [
        f"What do you already know about {topic}?",
        f"Where have you seen or heard about {topic} in everyday life?",
        f"What words, ideas, or examples come to mind when you hear '{topic}'?",
    ]

    grouped = {
        "math": [
            f"What previous math skill or idea is related to {topic}?",
            f"Have you used {topic} before in a calculation or real-life problem?",
        ],
        "science": [
            f"What scientific ideas, observations, or experiments connect to {topic}?",
            f"How could data, diagrams, or investigations help us understand {topic}?",
        ],
        "language": [
            f"What reading, writing, speaking, or language ideas connect to {topic}?",
            f"What communication skills will help you engage successfully with {topic}?",
        ],
        "modern_language": [
            f"What words, phrases, or expressions do you already know that connect to {topic}?",
            f"How might listening, speaking, reading, or writing help you use {topic} confidently?",
        ],
        "social_humanities": [
            f"What people, places, events, or issues connect to {topic}?",
            f"How does {topic} relate to society, citizenship, community, or the wider world?",
        ],
        "technology_design": [
            f"What tools, systems, materials, or design ideas connect to {topic}?",
            f"How could {topic} help solve a practical problem?",
        ],
        "agriculture": [
            f"What farming, crop, livestock, soil, or environmental ideas connect to {topic}?",
            f"How does {topic} support Caribbean food production or farm management?",
        ],
        "wellness_life": [
            f"What healthy habits, movement skills, family-life skills, or safety ideas connect to {topic}?",
            f"How could {topic} help improve personal or social well-being?",
        ],
        "enterprise": [
            f"What money, business, enterprise, or decision-making ideas connect to {topic}?",
            f"How could {topic} be useful in everyday life or entrepreneurship?",
        ],
        "creative_arts": [
            f"What creative skills, performance ideas, or artistic techniques connect to {topic}?",
            f"How might {topic} help you express ideas, feelings, or stories creatively?",
        ],
        "general": [
            f"What previous learning connects to {topic}?",
            f"How could {topic} be useful in class or in everyday life?",
        ],
    }

    questions = common + grouped.get(group, grouped["general"])

    if difficulty == "Beginner":
        questions.append(f"What simple fact or example do you already know about {topic}?")
    elif difficulty == "Advanced":
        questions.append(f"What deeper question or problem about {topic} would you like to explore?")

    deduped: List[str] = []
    for question in questions:
        if question not in deduped:
            deduped.append(question)

    return deduped[:5]


def _resources(match: Dict, user_resources: str, subject: str, topic: str, lesson_type: str) -> List[str]:
    items = list(match.get("resources", []))
    group = _subject_group(subject)

    fallback = [
        f"{subject} textbook section on {topic}",
        f"Teacher-made notes or slides on {topic}",
        "Board, projector, chart paper, or notebook materials",
    ]

    group_resources = {
        "math": ["Worked examples sheet", "Graph paper, ruler, or calculator where needed"],
        "science": ["Diagrams, models, specimens, or simple investigation materials", "Science notebook or observation sheet"],
        "language": ["Reading passage, prompt, or writing organizer", "Vocabulary support or sentence starters"],
        "modern_language": ["Flashcards, dialogue prompt, or vocabulary list", "Listening or speaking practice materials"],
        "social_humanities": ["Map, image, timeline, case study, or short source material"],
        "technology_design": ["Design brief, tools list, or planning sheet", "Sample product, diagram, or digital device where available"],
        "agriculture": ["Images or cards showing examples linked to the topic", "Local or Caribbean agriculture examples for discussion"],
        "wellness_life": ["Scenario cards, reflection sheet, or demonstration materials"],
        "enterprise": ["Simple business scenario, budgeting sheet, or case study"],
        "creative_arts": ["Art, music, drama, or performance materials suitable for the lesson"],
    }

    fallback.extend(group_resources.get(group, []))

    if lesson_type == "Practical":
        fallback.extend([
            f"Worksheet or activity sheet on {topic}",
            f"Simple classroom materials for a practical activity on {topic}",
        ])

    items.extend(fallback)

    if user_resources:
        items.extend([part.strip() for part in user_resources.split(",") if part.strip()])

    deduped: List[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)

    return deduped[:6]


def _build_4c_sections(topic: str, subject: str, lesson_type: str, difficulty: str, objectives: List[str]) -> Dict[str, List[str]]:
    group = _subject_group(subject)

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

    if group == "math":
        creativity[1] = f"Students suggest examples, patterns, or real-life uses of {topic}."
        critical_thinking[0] = f"Students solve guided and independent problems connected to {topic} and explain their reasoning."
    elif group == "science":
        creativity[1] = f"Students observe, classify, sketch, label, or brainstorm scientific examples linked to {topic}."
        critical_thinking[0] = f"Students interpret scientific information, diagrams, observations, or short data tasks related to {topic}."
    elif group == "language":
        communication[0] = f"Students discuss, present, write, or respond using ideas linked to {topic}."
    elif group == "modern_language":
        communication[0] = f"Students practise speaking, listening, reading, or writing using language linked to {topic}."
    elif group == "social_humanities":
        critical_thinking[0] = f"Students examine maps, texts, events, issues, or evidence related to {topic}."
    elif group == "technology_design":
        critical_thinking[0] = f"Students analyse a practical problem, process, design, or system related to {topic}."
        collaboration[0] = f"Pairs or groups complete a planning, design, or troubleshooting task related to {topic}."
    elif group == "agriculture":
        critical_thinking[0] = f"Students compare and classify examples linked to {topic} and connect them to Caribbean agriculture."
        collaboration[0] = f"Pairs or groups complete a card sort, comparison chart, or decision-making task related to {topic}."
    elif group == "wellness_life":
        communication[0] = f"Students explain choices, behaviours, movement skills, or health ideas connected to {topic}."
    elif group == "enterprise":
        critical_thinking[0] = f"Students analyse a practical money, business, or entrepreneurial situation related to {topic}."
    elif group == "creative_arts":
        creativity[1] = f"Students explore ways to express ideas about {topic} through creative or performance-based responses."

    if lesson_type == "Practical":
        collaboration[0] = f"Pairs or groups complete a hands-on task or short investigation related to {topic}."
    elif lesson_type == "Discussion":
        communication[0] = f"Students explain, discuss, justify, and respond to ideas connected to {topic}."

    if difficulty == "Advanced":
        critical_thinking.append(f"Include a deeper task where students justify, analyse, or evaluate an aspect of {topic}.")
        communication.append("Students defend their thinking using appropriate subject vocabulary and evidence.")

    return {
        "Creativity": creativity,
        "Critical Thinking": critical_thinking,
        "Communication": communication,
        "Collaboration": collaboration,
    }


def _build_5e_sections(topic: str, subject: str, lesson_type: str, difficulty: str, objectives: List[str]) -> Dict[str, List[str]]:
    group = _subject_group(subject)

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

    if group == "math":
        exploration[0] = f"Students explore {topic} through worked examples, guided practice, pattern spotting, or real-life problems."
        explanation[0] = f"Teacher models the steps, rules, and reasoning involved in {topic}."
        evaluation[0] = f"Use a worked example, mini quiz, oral questioning, or short problem-solving task to assess understanding of {topic}."
        extension[0] = f"Students apply {topic} to homework, a word problem, or a real-world numerical situation."
    elif group == "science":
        exploration[0] = f"Students investigate {topic} through scientific examples, diagrams, observation, data, or a guided practical task."
        explanation[0] = f"Teacher clarifies the scientific ideas, structures, processes, or evidence linked to {topic}."
        extension[0] = f"Students apply learning on {topic} to health, environment, experiment, or everyday scientific contexts."
    elif group == "language":
        engagement[0] = f"Use a prompt, short text, question, discussion starter, or language example to introduce {topic}."
        exploration[0] = f"Students explore {topic} through reading, writing, speaking, listening, or text-based activities."
        explanation[0] = f"Teacher clarifies the language or literary ideas linked to {topic}, using examples from student responses or texts."
    elif group == "modern_language":
        engagement[0] = f"Use greetings, visuals, vocabulary, or a short exchange to introduce {topic}."
        exploration[0] = f"Students explore {topic} through guided listening, speaking, reading, or writing tasks."
        explanation[0] = f"Teacher models correct language, pronunciation, and sentence patterns linked to {topic}."
    elif group == "social_humanities":
        exploration[0] = f"Students explore {topic} through case examples, maps, short texts, source material, discussion prompts, or issue-based tasks."
        explanation[0] = f"Teacher clarifies the key social, historical, geographical, or civic ideas related to {topic}."
    elif group == "technology_design":
        exploration[0] = f"Students explore {topic} through design thinking, structured tasks, troubleshooting, digital tools, or practical investigation."
        explanation[0] = f"Teacher clarifies the process, system, design ideas, or technical vocabulary related to {topic}."
    elif group == "agriculture":
        engagement[0] = f"Use photos, farm scenarios, local examples, samples, or sorting activities to introduce {topic}."
        exploration[0] = f"Students examine examples, images, fact cards, or comparison charts linked to {topic}, with emphasis on Caribbean agriculture."
        explanation[0] = f"Teacher clarifies important terms, characteristics, and practical agricultural uses linked to {topic}."
        extension[0] = f"Students apply learning on {topic} to Caribbean farming needs, management choices, or small-scale enterprise ideas."
    elif group == "wellness_life":
        exploration[0] = f"Students explore {topic} through scenarios, demonstrations, movement tasks, reflection prompts, or guided discussion."
        explanation[0] = f"Teacher clarifies healthy choices, safe practice, social skills, or life skills related to {topic}."
    elif group == "enterprise":
        exploration[0] = f"Students explore {topic} through simple enterprise, budgeting, planning, or decision-making tasks."
        explanation[0] = f"Teacher clarifies key business, money, or entrepreneurship ideas related to {topic}."
    elif group == "creative_arts":
        exploration[0] = f"Students explore {topic} through performance, art-making, listening, viewing, rehearsal, or creative response."
        explanation[0] = f"Teacher clarifies the techniques, vocabulary, and creative choices linked to {topic}."

    if lesson_type == "Practical":
        exploration[0] = f"Students investigate {topic} through a practical activity, observation, experiment, performance, or hands-on task."
        evaluation.append("Assess how well students carry out the practical task and explain their results, process, or choices.")
    elif lesson_type == "Discussion":
        engagement[1] = f"Use discussion to activate students' interest and draw out prior ideas about {topic}."
        explanation[1] = f"Students explain and justify their ideas about {topic} during guided discussion."

    if difficulty == "Beginner":
        explanation.append(f"Teacher provides simple examples, modelling, and guided support to help students understand {topic}.")
    elif difficulty == "Advanced":
        evaluation.append(f"Include a deeper question that asks students to analyse, justify, or evaluate an aspect of {topic}.")
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
    group = _subject_group(subject)

    reflection = [
        f"How well did students meet the lesson objectives for {topic}?",
        f"What misconceptions or difficulties became clear during the lesson on {topic}?",
        f"What should be adjusted, strengthened, or simplified the next time {topic} is taught?",
    ]

    if group == "math":
        reflection.append(f"Were students able to show accurate working and explain their reasoning for tasks related to {topic}?")
    elif group == "science":
        reflection.append(f"Were students able to use correct scientific terms and explain the evidence, processes, or ideas involved in {topic}?")
    elif group == "language":
        reflection.append(f"Did students communicate their ideas clearly and use appropriate language related to {topic}?")
    elif group == "modern_language":
        reflection.append(f"Were students able to use target-language vocabulary, pronunciation, and sentence patterns appropriately in relation to {topic}?")
    elif group == "social_humanities":
        reflection.append(f"Were students able to connect {topic} to society, place, history, evidence, or citizenship in meaningful ways?")
    elif group == "technology_design":
        reflection.append(f"Were students able to apply practical thinking, design steps, digital skills, or safe procedures related to {topic}?")
    elif group == "agriculture":
        reflection.append(f"Were students able to connect the content to Caribbean agriculture, safe practice, or farm decision-making?")
    elif group == "wellness_life":
        reflection.append(f"Were students able to relate {topic} to healthy living, safe practice, personal development, or responsible behaviour?")
    elif group == "enterprise":
        reflection.append(f"Were students able to apply {topic} to practical business, money, or entrepreneurial situations?")
    elif group == "creative_arts":
        reflection.append(f"Were students able to express ideas creatively and use techniques, skills, or performance choices related to {topic}?")

    if difficulty == "Beginner":
        reflection.append(f"Did students need more scaffolding, modelling, or simpler examples to understand {topic}?")
    elif difficulty == "Advanced":
        reflection.append(f"Could students have been challenged further through more independent, analytical, or evaluative tasks on {topic}?")

    return reflection[:5]


def _fallback_domain_objectives(topic: str, subject: str) -> Dict[str, str]:
    group = _subject_group(subject)

    if group == "math":
        return {
            "cognitive": f"Students explain and apply mathematical ideas and procedures related to {topic}.",
            "affective": f"Students show confidence and persistence while solving tasks related to {topic}.",
            "psychomotor": f"Students complete written workings, diagrams, graphs, or calculations linked to {topic}.",
        }
    if group == "science":
        return {
            "cognitive": f"Students explain scientific ideas, evidence, or processes related to {topic}.",
            "affective": f"Students value scientific thinking and safe practice while studying {topic}.",
            "psychomotor": f"Students complete a practical, observational, diagrammatic, or written task linked to {topic}.",
        }
    if group in {"language", "modern_language"}:
        return {
            "cognitive": f"Students explain, interpret, and apply ideas related to {topic}.",
            "affective": f"Students show appreciation for effective communication while engaging with {topic}.",
            "psychomotor": f"Students complete an oral, written, reading, listening, or performance task linked to {topic}.",
        }
    if group == "creative_arts":
        return {
            "cognitive": f"Students explain and apply creative ideas and techniques related to {topic}.",
            "affective": f"Students show appreciation for artistic expression and responsible participation while engaging with {topic}.",
            "psychomotor": f"Students complete a practical, creative, performance, or visual task linked to {topic}.",
        }

    return {
        "cognitive": f"Students explain and apply the key ideas related to {topic} in {subject}.",
        "affective": f"Students show appreciation for the value and relevance of {topic} in classroom and real-life settings.",
        "psychomotor": f"Students complete a practical, written, oral, or visual task linked to {topic}.",
    }


def _fallback_class_profile(subject: str, difficulty: str) -> Dict[str, object]:
    group = _subject_group(subject)

    learning_styles = ["Visual", "Auditory", "Kinesthetic"]
    if group in {"math", "science", "technology_design"}:
        learning_styles.append("Logical/Mathematical")
    elif group in {"language", "modern_language"}:
        learning_styles.append("Verbal/Linguistic")
    elif group == "creative_arts":
        learning_styles.append("Creative")

    profile = {
        "learner_profile": (
            f"This class includes learners with varied readiness levels, interests, and prior knowledge in {subject}. "
            "The lesson should provide clear explanations, modelling, and opportunities for guided and independent work."
        ),
        "learning_styles": learning_styles[:4],
    }

    if difficulty == "Mixed Ability":
        profile["mixed_ability_support"] = (
            "Provide scaffolds, peer support, teacher check-ins, and extension prompts so learners at different readiness levels can all participate meaningfully."
        )

    return profile


def _fallback_prior_learning(topic: str, subject: str) -> str:
    return f"Students should already have some basic background knowledge, vocabulary, or everyday experience connected to {topic} in {subject}."


def _fallback_assessment_criteria(topic: str) -> str:
    return f"Students should accurately use key vocabulary, respond to questions or tasks on {topic}, and demonstrate understanding through discussion, written work, practical work, or performance as appropriate."


def _fallback_apse_pathways(topic: str, subject: str) -> List[str]:
    group = _subject_group(subject)

    common = [
        f"Communication, teamwork, and problem-solving through classroom tasks on {topic}",
        f"Real-world application of {topic} to community, work, or everyday decision-making",
    ]

    if group == "enterprise":
        return [
            f"Enterprise awareness linked to {subject} and the study of {topic}",
            *common,
        ]
    if group == "technology_design":
        return [
            f"Problem-solving, design thinking, and practical application linked to {subject} and {topic}",
            *common,
        ]
    if group == "creative_arts":
        return [
            f"Creative expression and performance linked to {subject} and the study of {topic}",
            *common,
        ]

    return [
        f"Career awareness linked to {subject} and the study of {topic}",
        *common,
    ]


def _fallback_stem_skills(subject: str, topic: str) -> List[str]:
    if subject.strip().lower() not in STEM_SUBJECTS:
        return []

    group = _subject_group(subject)

    if group == "math":
        return [
            f"Problem-solving and reasoning linked to {topic}",
            "Accurate working and checking",
            "Application of subject knowledge",
        ]
    if group == "science":
        return [
            f"Observation, analysis, and interpretation linked to {topic}",
            "Evidence-based thinking",
            "Practical application of subject knowledge",
        ]
    if group == "technology_design":
        return [
            f"Design thinking and practical problem-solving linked to {topic}",
            "Safe tool or system use",
            "Application of technical knowledge",
        ]

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
            normalized[section_name] = [_clean_math_text(str(item)) for item in value if str(item).strip()]
        elif isinstance(value, str) and value.strip():
            normalized[section_name] = [_clean_math_text(value.strip())]
        else:
            normalized[section_name] = fallback_sections.get(section_name, [])

    return normalized


def generate_lesson(payload: dict) -> dict:
    payload = _resolve_from_profile(dict(payload))

    payload["curriculum"] = payload.get("curriculum") or ""
    payload["subject"] = payload.get("subject") or ""
    payload["topic"] = payload.get("topic") or ""
    payload["grade_level"] = payload.get("grade_level") or payload.get("grade") or ""
    payload["structure"] = payload.get("structure") or "5Es"
    payload["difficulty"] = payload.get("difficulty") or "Intermediate"
    payload["lesson_type"] = payload.get("lesson_type") or "Theory"
    payload["objective_count"] = payload.get("objective_count") or 3
    payload["duration_minutes"] = payload.get("duration_minutes") or 60
    payload["subtopic"] = payload.get("subtopic") or ""
    payload["resources"] = payload.get("resources") or ""
    payload["description"] = payload.get("description") or ""

    required = ["curriculum", "subject", "grade_level", "topic"]
    missing = [key for key in required if not payload.get(key)]
    if missing:
        raise ValueError(f"Missing required lesson fields: {', '.join(missing)}")

    key = cache_key(payload)
    if key in CACHE:
        return CACHE[key]

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
        "Use oral questioning and at least one written, practical, oral, or performance-based task to gather evidence of learning.",
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

    lesson = dict(fallback_lesson)

    try:
        ai_parts = generate_dynamic_lesson_parts(
            payload=payload,
            objectives=objective_text,
            strand=match.get("strand", "General Strand"),
            resource_suggestions=fallback_resources,
        )

        if ai_parts:
            lesson["attainment_target"] = _clean_math_text(
                ai_parts.get("attainment_target", lesson["attainment_target"])
            )
            lesson["theme"] = _clean_math_text(
                ai_parts.get("theme", lesson["theme"])
            )
            lesson["strand"] = _clean_math_text(
                ai_parts.get("strand", lesson["strand"])
            )
            lesson["class_profile"] = _clean_class_profile(
                ai_parts.get("class_profile", lesson["class_profile"])
            )
            lesson["domain_objectives"] = _clean_domain_objectives(
                ai_parts.get("domain_objectives", lesson["domain_objectives"])
            )
            lesson["prior_learning"] = _clean_math_text(
                ai_parts.get("prior_learning", lesson["prior_learning"])
            )
            lesson["prior_knowledge_questions"] = _clean_math_list(
                ai_parts.get("prior_knowledge_questions", lesson["prior_knowledge_questions"])
            )
            lesson["resources"] = _clean_math_list(
                ai_parts.get("resources", lesson["resources"])
            )
            lesson["sections"] = _normalize_ai_sections(
                payload["structure"],
                ai_parts.get("sections", {}),
                fallback_sections,
            )
            lesson["assessment"] = _clean_math_list(
                ai_parts.get("assessment", lesson["assessment"])
            )
            lesson["assessment_criteria"] = _clean_math_text(
                ai_parts.get("assessment_criteria", lesson["assessment_criteria"])
            )
            lesson["apse_pathways"] = _clean_math_list(
                ai_parts.get("apse_pathways", lesson["apse_pathways"])
            )
            lesson["stem_skills"] = _clean_math_list(
                ai_parts.get("stem_skills", lesson["stem_skills"])
            )
            lesson["reflection"] = _clean_math_list(
                ai_parts.get("reflection", lesson["reflection"])
            )
            lesson["generation_mode"] = "ai"
    except Exception as exc:
        print("LESSON AI ERROR:", type(exc).__name__, str(exc))

    result = {
        "title": f"{payload.get('subject', '')} Lesson Plan - {payload.get('topic', '')}",
        "curriculum_match": match,
        "lesson": lesson,
    }

    CACHE[key] = result
    return result