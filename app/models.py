from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


# ----------------------------
# LESSON + OBJECTIVES
# ----------------------------

class ObjectiveRequest(BaseModel):
    curriculum: str
    subject: str
    grade_level: str
    topic: str
    difficulty: str = "Intermediate"
    objective_count: int = 3
    description: str = ""


class LessonRequest(BaseModel):
    curriculum: str
    subject: str
    grade_level: str
    structure: str
    difficulty: str
    lesson_type: str
    topic: str
    subtopic: str = ""
    objective_count: int = 3
    duration_minutes: int = 60
    description: str = ""
    resources: str = ""


# ----------------------------
# ✅ FIXED ACTIVITY MODEL
# ----------------------------

class ActivityRequest(BaseModel):
    # ✅ NEW (frontend uses this)
    lesson_payload: Optional[Dict[str, Any]] = None

    # fallback support (old system)
    curriculum: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    topic: Optional[str] = None

    # activity config
    activity_type: Literal[
        "mixed_quiz",
        "mcq",
        "short_answer",
        "essay",
        "math_problem_solving",
        "crossword",
        "word_search",
        "case_study",
        "exit_ticket",
        "homework_sheet",
    ]

    difficulty: str = "Intermediate"

    # ✅ MATCH FRONTEND
    item_count: int = Field(default=8, ge=3, le=20)

    include_answer_key: bool = True
    include_mark_scheme: bool = False

    # optional extras
    integrate_into_lesson: bool = False
    duration_minutes: int = Field(default=20, ge=5, le=120)
    lesson_text: str = ""
    additional_notes: str = ""

    # 🔥 BACKWARD COMPATIBILITY
    question_count: Optional[int] = None

    def get_count(self) -> int:
        """
        Ensures compatibility between old (question_count)
        and new (item_count) frontend.
        """
        return self.item_count or self.question_count or 8


# ----------------------------
# PAYMENTS
# ----------------------------

class CheckoutSessionRequest(BaseModel):
    target_plan: Literal["pro", "plus"] = "pro"


# ----------------------------
# LESSON STORAGE
# ----------------------------

class SaveLessonRequest(BaseModel):
    lesson_payload: Dict[str, Any]


class UpdateLessonRequest(BaseModel):
    lesson_payload: Dict[str, Any]


# ----------------------------
# EXPORT
# ----------------------------

class ExportRequest(BaseModel):
    title: str
    content: str


# ----------------------------
# ADMIN
# ----------------------------

class AdminFrameworkRequest(BaseModel):
    framework: Dict[str, Any]


class AdminUserUpdateRequest(BaseModel):
    role: str
    plan: str


class PlanUpdateRequest(BaseModel):
    plan: str


class AdminBillingUpdateRequest(BaseModel):
    role: str
    plan: str
    subscription_status: str
    payment_provider: str
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""
    subscription_started_at: str = ""
    subscription_renews_at: str = ""
    billing_notes: str = ""