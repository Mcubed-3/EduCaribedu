from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple

DATA_DIR = Path(__file__).parent / "data"

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "by", "with",
    "is", "are", "be", "from", "into", "at", "as", "it", "this", "that", "these",
    "those", "i", "want", "students", "student", "lesson", "teach", "teaching",
    "learn", "learning", "about", "using", "use", "their", "them", "they",
    "simple", "basic", "understand", "work", "activity", "activities"
}


def load_all_curriculum() -> Dict[str, Any]:
    data = {"frameworks": []}
    for file in DATA_DIR.glob("*.json"):
        if "bloom" in file.name.lower():
            continue
        content = json.loads(file.read_text(encoding="utf-8"))
        data["frameworks"].extend(content.get("frameworks", []))
    return data


def load_bloom() -> Dict[str, Any]:
    return json.loads((DATA_DIR / "bloom_verbs.json").read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    cleaned = normalize_text(text)
    return [tok for tok in cleaned.split() if tok and tok not in STOPWORDS]


def similarity_score(a: str, b: str) -> float:
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def token_overlap_score(query: str, target: str) -> float:
    q_tokens = set(tokenize(query))
    t_tokens = set(tokenize(target))
    if not q_tokens or not t_tokens:
        return 0.0
    overlap = q_tokens & t_tokens
    return len(overlap) / max(len(q_tokens), 1)


def partial_score(a: str, b: str) -> float:
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return similarity_score(a, b)


class CurriculumEngine:
    def __init__(self):
        self.frameworks: List[Dict[str, Any]] = []
        self.bloom: Dict[str, Any] = {}
        self.reload_data()

    def reload_data(self) -> None:
        curriculum = load_all_curriculum()
        bloom = load_bloom()
        self.frameworks = curriculum.get("frameworks", [])
        self.bloom = bloom
        print(f"ENGINE RELOADED: {len(self.frameworks)} framework entries loaded.")

    def list_subjects(self) -> List[str]:
        return sorted({item["subject"] for item in self.frameworks if item.get("subject")})

    def _candidate_frameworks(self, curriculum: str, subject: str, grade_level: str) -> List[Dict[str, Any]]:
        candidates = [
            f for f in self.frameworks
            if f.get("curriculum", "").lower() == curriculum.lower()
            and f.get("subject", "").lower() == subject.lower()
        ]

        if grade_level:
            exact = [
                f for f in candidates
                if grade_level.lower() in f.get("level", "").lower()
                or grade_level.lower() in " ".join(f.get("bands", [])).lower()
            ]
            if exact:
                candidates = exact

        return candidates

    def _score_topic_match(self, topic: str, description: str, item: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        topic_clean = normalize_text(topic)
        description_clean = normalize_text(description)

        name = item.get("name", "")
        aliases = item.get("aliases", [])
        keywords = item.get("keywords", [])
        objective_text = " ".join(obj.get("text", "") for obj in item.get("objectives", []))

        alias_text = " ".join(aliases)
        keyword_text = " ".join(keywords)
        combined_target = " ".join([name, alias_text, keyword_text, objective_text])

        debug = {
            "exact_name": 0.0,
            "exact_alias": 0.0,
            "exact_keyword": 0.0,
            "topic_overlap": 0.0,
            "topic_partial": 0.0,
            "topic_similarity": 0.0,
            "description_overlap": 0.0,
            "description_partial": 0.0,
        }

        if topic_clean == normalize_text(name):
            debug["exact_name"] = 100.0
            return 100.0, debug

        for alias in aliases:
            if topic_clean == normalize_text(alias):
                debug["exact_alias"] = 95.0
                return 95.0, debug

        for keyword in keywords:
            if topic_clean == normalize_text(keyword):
                debug["exact_keyword"] = 90.0
                return 90.0, debug

        debug["topic_overlap"] = token_overlap_score(topic, combined_target) * 50.0
        debug["topic_partial"] = partial_score(topic, combined_target) * 25.0
        debug["topic_similarity"] = similarity_score(topic, combined_target) * 15.0

        if description_clean:
            debug["description_overlap"] = token_overlap_score(description, combined_target) * 10.0
            debug["description_partial"] = partial_score(description, combined_target) * 5.0

        total = sum(debug.values())
        return total, debug

    def search(
        self,
        curriculum: str,
        subject: str,
        grade_level: str,
        topic: str,
        description: str = "",
    ) -> Dict[str, Any]:
        candidates = self._candidate_frameworks(curriculum, subject, grade_level)

        best_topic = None
        best_score = -1.0
        best_debug = {}

        for frame in candidates:
            for item in frame.get("topics", []):
                score, debug = self._score_topic_match(topic, description, item)

                if score > best_score:
                    best_score = score
                    best_debug = debug
                    best_topic = {
                        **item,
                        "framework_id": frame.get("id", ""),
                        "level": frame.get("level", ""),
                        "curriculum": frame.get("curriculum", ""),
                        "subject": frame.get("subject", ""),
                        "strand": frame.get("strand", ""),
                        "topic_group": frame.get("topic_group", ""),
                    }

        if not best_topic and candidates:
            frame = candidates[0]
            item = frame.get("topics", [{}])[0]
            best_topic = {
                **item,
                "framework_id": frame.get("id", ""),
                "level": frame.get("level", ""),
                "curriculum": frame.get("curriculum", ""),
                "subject": frame.get("subject", ""),
                "strand": frame.get("strand", ""),
                "topic_group": frame.get("topic_group", ""),
            }
            best_score = 0.0

        return {
            "match": best_topic,
            "score": round(best_score, 2),
            "debug": best_debug,
        }

    def build_objectives(
        self,
        curriculum: str,
        subject: str,
        grade_level: str,
        topic: str,
        objective_count: int,
        difficulty: str,
        description: str = "",
    ) -> List[Dict[str, str]]:
        result = self.search(curriculum, subject, grade_level, topic, description)
        match = result["match"]

        if not match:
            return []

        preferred_levels = self.bloom.get(difficulty, {}).get("levels", [])
        objectives = match.get("objectives", [])

        ranked = sorted(
            objectives,
            key=lambda obj: (
                0 if obj.get("bloom") in preferred_levels else 1,
                obj.get("text", ""),
            ),
        )

        return ranked[:objective_count]

    def bloom_verbs(self, difficulty: str) -> List[str]:
        return self.bloom.get(difficulty, {}).get("verbs", [])