import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CURRICULUM_DIR = BASE_DIR / "curriculum_data"


def load_curriculum(subject: str, grade: str, curriculum: str):
    file_path = CURRICULUM_DIR / curriculum / subject.lower() / f"{grade}.json"

    if not file_path.exists():
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)