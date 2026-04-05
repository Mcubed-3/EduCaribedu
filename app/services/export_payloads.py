def lesson_plan_to_sections(lesson: dict):
    return [
        {"heading": "Attainment Target", "content": lesson.get("attainment_target")},

        {"heading": "Theme / Strand", "content": {
            "Theme": lesson.get("theme"),
            "Strand": lesson.get("strand"),
        }},

        {"heading": "Class Profile", "content": lesson.get("class_profile")},

        {"heading": "Objectives", "content": lesson.get("objectives")},

        {"heading": "Prior Learning", "content": lesson.get("prior_learning")},

        {"heading": "Engage", "content": lesson.get("engage")},
        {"heading": "Explore", "content": lesson.get("explore")},
        {"heading": "Explain", "content": lesson.get("explain")},
        {"heading": "Elaborate", "content": lesson.get("elaborate")},
        {"heading": "Evaluate", "content": lesson.get("evaluate")},

        {"heading": "Assessment Criteria", "content": lesson.get("assessment_criteria")},

        {"heading": "APSE Pathways", "content": lesson.get("apse_pathways")},

        {"heading": "STEM / Skills", "content": lesson.get("stem_skills")},

        {"heading": "Post Lesson Reflection", "content": lesson.get("reflection")},
    ]