from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel


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
    paypal_customer_id: str = ""
    paypal_subscription_id: str = ""
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""
    subscription_started_at: str = ""
    subscription_renews_at: str = ""
    billing_notes: str = ""
