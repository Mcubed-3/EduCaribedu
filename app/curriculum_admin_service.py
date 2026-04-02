from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent / "data"
MASTER_FILE = DATA_DIR / "master_curriculum_framework.json"


def _read_master() -> Dict[str, Any]:
    if not MASTER_FILE.exists():
        return {"frameworks": []}
    return json.loads(MASTER_FILE.read_text(encoding="utf-8"))


def _write_master(data: Dict[str, Any]) -> None:
    MASTER_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def list_frameworks(
    curriculum: str = "",
    subject: str = "",
    level: str = "",
    query: str = "",
) -> List[Dict[str, Any]]:
    data = _read_master()
    frameworks = data.get("frameworks", [])

    results = []
    q = query.lower().strip()

    for framework in frameworks:
        if curriculum and framework.get("curriculum", "").lower() != curriculum.lower():
            continue
        if subject and framework.get("subject", "").lower() != subject.lower():
            continue
        if level and framework.get("level", "").lower() != level.lower():
            continue

        if q:
            searchable = " ".join(
                [
                    framework.get("id", ""),
                    framework.get("curriculum", ""),
                    framework.get("subject", ""),
                    framework.get("level", ""),
                    framework.get("strand", ""),
                    framework.get("topic_group", ""),
                    " ".join(t.get("name", "") for t in framework.get("topics", [])),
                ]
            ).lower()
            if q not in searchable:
                continue

        results.append(framework)

    return results


def get_framework(framework_id: str) -> Optional[Dict[str, Any]]:
    data = _read_master()
    for framework in data.get("frameworks", []):
        if framework.get("id") == framework_id:
            return framework
    return None


def update_framework(framework_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = _read_master()
    frameworks = data.get("frameworks", [])

    for i, framework in enumerate(frameworks):
        if framework.get("id") == framework_id:
            frameworks[i] = payload
            data["frameworks"] = frameworks
            _write_master(data)
            return payload

    return None


def create_framework(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = _read_master()
    frameworks = data.get("frameworks", [])

    if not payload.get("id"):
        payload["id"] = f"framework_{uuid.uuid4().hex[:10]}"

    frameworks.append(payload)
    data["frameworks"] = frameworks
    _write_master(data)
    return payload


def delete_framework(framework_id: str) -> bool:
    data = _read_master()
    frameworks = data.get("frameworks", [])
    new_frameworks = [f for f in frameworks if f.get("id") != framework_id]

    if len(new_frameworks) == len(frameworks):
        return False

    data["frameworks"] = new_frameworks
    _write_master(data)
    return True