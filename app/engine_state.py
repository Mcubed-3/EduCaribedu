from __future__ import annotations

from .curriculum_engine import CurriculumEngine
import json
import os

engine = CurriculumEngine()

# 🔥 LOAD CURRICULUM DATA ON STARTUP
BASE_DIR = os.path.dirname(__file__)
framework_path = os.path.join(BASE_DIR, "data", "frameworks.json")

if os.path.exists(framework_path):
    with open(framework_path, "r", encoding="utf-8") as f:
        engine.frameworks = json.load(f)
else:
    print("⚠️ WARNING: frameworks.json not found. Dropdowns will be empty.")