from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

LESSONS_FILE = STORAGE_DIR / "saved_lessons.json"

if not LESSONS_FILE.exists():
    LESSONS_FILE.write_text("[]", encoding="utf-8")


def _read_lessons() -> List[Dict[str, Any]]:
    try:
        return json.loads(LESSONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_lessons(data: List[Dict[str, Any]]) -> None:
    LESSONS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_lessons(owner_email: str) -> List[Dict[str, Any]]:
    lessons = [x for x in _read_lessons() if x.get("owner_email") == owner_email]
    return sorted(lessons, key=lambda x: x.get("updated_at", ""), reverse=True)


def get_lesson(owner_email: str, lesson_id: str) -> Optional[Dict[str, Any]]:
    lessons = _read_lessons()
    for lesson in lessons:
        if lesson.get("id") == lesson_id and lesson.get("owner_email") == owner_email:
            return lesson
    return None


def save_new_lesson(owner_email: str, lesson_payload: Dict[str, Any]) -> Dict[str, Any]:
    lessons = _read_lessons()
    now = datetime.utcnow().isoformat()

    record = {
        "id": str(uuid.uuid4()),
        "owner_email": owner_email,
        "title": lesson_payload.get("title", "Untitled Lesson"),
        "curriculum": lesson_payload.get("lesson", {}).get("curriculum", ""),
        "subject": lesson_payload.get("lesson", {}).get("subject", ""),
        "grade_level": lesson_payload.get("lesson", {}).get("grade_level", ""),
        "topic": lesson_payload.get("lesson", {}).get("topic", ""),
        "created_at": now,
        "updated_at": now,
        "data": lesson_payload,
    }

    lessons.append(record)
    _write_lessons(lessons)
    return record


def update_existing_lesson(owner_email: str, lesson_id: str, lesson_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    lessons = _read_lessons()
    now = datetime.utcnow().isoformat()

    for i, lesson in enumerate(lessons):
        if lesson.get("id") == lesson_id and lesson.get("owner_email") == owner_email:
            lessons[i]["title"] = lesson_payload.get("title", lesson.get("title", "Untitled Lesson"))
            lessons[i]["curriculum"] = lesson_payload.get("lesson", {}).get("curriculum", lesson.get("curriculum", ""))
            lessons[i]["subject"] = lesson_payload.get("lesson", {}).get("subject", lesson.get("subject", ""))
            lessons[i]["grade_level"] = lesson_payload.get("lesson", {}).get("grade_level", lesson.get("grade_level", ""))
            lessons[i]["topic"] = lesson_payload.get("lesson", {}).get("topic", lesson.get("topic", ""))
            lessons[i]["updated_at"] = now
            lessons[i]["data"] = lesson_payload
            _write_lessons(lessons)
            return lessons[i]

    return None


def delete_lesson(owner_email: str, lesson_id: str) -> bool:
    lessons = _read_lessons()
    new_lessons = [
        lesson for lesson in lessons
        if not (lesson.get("id") == lesson_id and lesson.get("owner_email") == owner_email)
    ]
    if len(new_lessons) == len(lessons):
        return False
    _write_lessons(new_lessons)
    return True