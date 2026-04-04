from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


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


class ActivityRequest(BaseModel):
    lesson_payload: Optional[Dict[str, Any]] = None

    curriculum: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = "Intermediate"

    activity_type: Literal[
        "mixed_quiz",
        "mcq",
        "short_answer",
        "essay",
        "math_problem_solving",
        "case_study",
        "exit_ticket",
        "homework_sheet",
    ]

    item_count: int = Field(default=8, ge=3, le=20)
    include_answer_key: bool = True
    include_mark_scheme: bool = False
    source_mode: Literal["lesson", "standalone"] = "lesson"

    integrate_into_lesson: bool = False
    duration_minutes: int = Field(default=20, ge=5, le=120)
    lesson_text: str = ""
    additional_notes: str = ""

    question_count: Optional[int] = None

    def get_count(self) -> int:
        return self.item_count or self.question_count or 8


class CheckoutSessionRequest(BaseModel):
    target_plan: Literal["pro", "plus"] = "pro"


class SaveLessonRequest(BaseModel):
    lesson_payload: Dict[str, Any]


class UpdateLessonRequest(BaseModel):
    lesson_payload: Dict[str, Any]


class ExportRequest(BaseModel):
    title: str
    content: str


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