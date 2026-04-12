from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .activity_generator import generate_activity
from .auth_service import (
    can_export_docx,
    can_export_pdf,
    can_generate_activities,
    can_generate_lessons,
    can_save_more_lessons,
    cancel_user_paid_plan,
    create_session,
    create_user,
    delete_session,
    find_user_by_stripe_customer_id,
    find_user_by_stripe_subscription_id,
    get_plan_status,
    get_user_profile,
    get_user_by_email,
    get_user_by_session,
    increment_activity_generation_count,
    increment_generation_count,
    init_auth_db,
    list_signup_events,
    list_users,
    save_user_profile,
    update_user_billing,
    update_user_plan,
    update_user_role_plan,
    update_user_stripe_subscription,
    verify_user,
)
from .curriculum_admin_service import (
    create_framework,
    delete_framework,
    get_framework,
    list_frameworks,
    update_framework,
)
from .engine_state import engine
from .export_service import export_to_docx, export_to_pdf
from .feedback_service import (
    create_feedback,
    init_feedback_db,
    list_all_feedback,
    list_feedback_for_user,
)
from .lesson_generator import generate_lesson
from .models import (
    ActivityRequest,
    AdminBillingUpdateRequest,
    AdminFrameworkRequest,
    AdminUserUpdateRequest,
    ExportRequest,
    LessonRequest,
    ObjectiveRequest,
    PlanUpdateRequest,
    SaveLessonRequest,
    UpdateLessonRequest,
)
from .storage_service import (
    delete_lesson,
    get_lesson,
    list_lessons,
    save_new_lesson,
    update_existing_lesson,
)
from .stripe_service import (
    create_checkout_session,
    create_portal_session,
    get_stripe_public_config,
    to_iso_from_unix,
    verify_webhook,
)

app = FastAPI(title="EduCarib AI Local Python")
BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

SESSION_COOKIE = "educarib_session"

init_auth_db()
init_feedback_db()


def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE, "")
    return get_user_by_session(token)


def get_current_user_optional(request: Request):
    try:
        return get_current_user(request)
    except:
        return None


def require_user(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def require_admin(request: Request):
    user = require_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _dashboard_summary(user_email: str):
    lessons = list_lessons(user_email)
    frameworks = engine.frameworks

    subjects = sorted({item.get("subject", "") for item in frameworks if item.get("subject")})
    curricula = sorted({item.get("curriculum", "") for item in frameworks if item.get("curriculum")})
    levels = sorted({item.get("level", "") for item in frameworks if item.get("level")})

    recent_lessons = lessons[:5]

    return {
        "saved_count": len(lessons),
        "framework_count": len(frameworks),
        "subject_count": len(subjects),
        "curriculum_count": len(curricula),
        "level_count": len(levels),
        "subjects": subjects,
        "recent_lessons": recent_lessons,
    }


@app.get("/robots.txt")
def robots_txt():
    return FileResponse(BASE_DIR / "static" / "robots.txt", media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap_xml():
    return FileResponse(BASE_DIR / "static" / "sitemap.xml", media_type="application/xml")


@app.get("/ads.txt")
def ads_txt():
    return FileResponse("app/static/ads.txt", media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = get_current_user(request)

    if user:
        dashboard = _dashboard_summary(user["email"])
        plan_status = get_plan_status(user, dashboard["saved_count"])
    else:
        dashboard = {
            "saved_count": 0,
            "framework_count": 0,
            "subject_count": 0,
            "curriculum_count": 0,
            "level_count": 0,
            "subjects": [],
            "recent_lessons": [],
        }
        plan_status = {
            "monthly_generations": {"used": 0, "limit": 5},
            "saved_lessons": {"used": 0, "limit": 0},
            "docx_export": False,
            "pdf_export": False,
            "activity_generation": False,
            "ads_enabled": True,
            "subscription_status": "guest",
        }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dashboard": dashboard,
            "current_user": user or {
                "email": "",
                "role": "guest",
                "plan": "guest",
            },
            "plan_status": plan_status,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/pricing", response_class=HTMLResponse)
def pricing_page(request: Request):
    user = get_current_user(request)

    if user:
        saved_count = len(list_lessons(user["email"]))
        plan_status = get_plan_status(user, saved_count)
        current_user = user
    else:
        plan_status = {
            "plan": "free",
            "role": "guest",
            "subscription_status": "guest",
            "payment_provider": "",
            "monthly_generations": {
                "used": 0,
                "limit": 5,
                "remaining": 5,
                "allowed": True,
            },
            "saved_lessons": {
                "used": 0,
                "limit": 0,
                "remaining": 0,
                "allowed": False,
            },
            "activity_generations": {
                "used": 0,
                "limit": 0,
                "remaining": 0,
                "allowed": False,
            },
            "docx_export": False,
            "pdf_export": True,
            "ads_enabled": True,
            "activity_generation": False,
        }
        current_user = {
            "email": "",
            "role": "guest",
            "plan": "free",
        }

    return templates.TemplateResponse(
        "pricing.html",
        {
            "request": request,
            "current_user": current_user,
            "plan_status": plan_status,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/feedback", response_class=HTMLResponse)
def feedback_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "feedback.html",
        {
            "request": request,
            "current_user": user,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/privacy", response_class=HTMLResponse)
def privacy_page(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request):
    return templates.TemplateResponse(
        "terms.html",
        {
            "request": request,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "mode": "login",
            "error": "",
            "site_url": "https://educaribedu.org",
        },
    )


@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    user = verify_user(email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "mode": "login",
                "error": "Invalid email or password.",
                "site_url": "https://educaribedu.org",
            },
            status_code=400,
        )

    token = create_session(user["id"])
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=14 * 24 * 60 * 60,
    )
    return response


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "mode": "signup",
            "error": "",
            "site_url": "https://educaribedu.org",
        },
    )


@app.post("/signup", response_class=HTMLResponse)
def signup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    email = email.strip().lower()

    if get_user_by_email(email):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "mode": "signup",
                "error": "An account with that email already exists.",
                "site_url": "https://educaribedu.org",
            },
            status_code=400,
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "mode": "signup",
                "error": "Password must be at least 6 characters.",
                "site_url": "https://educaribedu.org",
            },
            status_code=400,
        )

    user = create_user(email, password, role="user", plan="free")
    token = create_session(user["id"])

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=14 * 24 * 60 * 60,
    )
    return response


@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE, "")
    if token:
        delete_session(token)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "current_user": user,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "current_user": user,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/api/me")
def me(request: Request):
    user = get_current_user_optional(request)

    if not user:
        return {
            "user": {
                "email": "",
                "role": "guest",
                "plan": "guest",
            },
            "profile": {},
            "plan_status": {
                "plan": "guest",
                "role": "guest",
                "subscription_status": "guest",
                "payment_provider": "",
                "monthly_generations": {
                    "used": 0,
                    "limit": 5,
                    "remaining": 5,
                    "allowed": True,
                },
                "saved_lessons": {
                    "used": 0,
                    "limit": 0,
                    "remaining": 0,
                    "allowed": False,
                },
                "activity_generations": {
                    "used": 0,
                    "limit": 0,
                    "remaining": 0,
                    "allowed": False,
                },
                "docx_export": False,
                "pdf_export": True,
                "ads_enabled": True,
                "activity_generation": False,
            },
        }

    saved_count = len(list_lessons(user["email"]))
    profile = get_user_profile(user["id"])
    return {
        "user": user,
        "profile": profile,
        "plan_status": get_plan_status(user, saved_count),
    }


@app.get("/api/profile")
def api_get_profile(request: Request):
    user = require_user(request)
    return get_user_profile(user["id"])


@app.post("/api/profile")
async def api_save_profile(request: Request):
    user = require_user(request)
    payload = await request.json()
    profile = save_user_profile(
        user["id"],
        payload.get("subjects", []),
        payload.get("grade_levels", []),
        payload.get("curriculum", ""),
    )
    return profile


@app.get("/api/dashboard")
def dashboard_data(request: Request):
    user = require_user(request)
    return _dashboard_summary(user["email"])


@app.get("/api/config")
def config(request: Request):
    user = get_current_user_optional(request)
    profile = get_user_profile(user["id"]) if user else {}

    subjects = sorted({
        item.get("subject", "").strip()
        for item in engine.frameworks
        if item.get("subject", "").strip()
    })

    curricula = sorted({
        item.get("curriculum", "").strip()
        for item in engine.frameworks
        if item.get("curriculum", "").strip()
    })

    levels = [
        "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
        "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11",
    ]

    return {
        "subjects": subjects,
        "curricula": curricula,
        "levels": levels,
        "structures": ["5Es", "4Cs"],
        "difficulties": ["Beginner", "Intermediate", "Advanced", "Mixed Ability"],
        "lesson_types": ["Theory", "Practical", "Discussion", "Mixed"],
        "profile": profile,
    }

@app.get("/api/feedback")
def feedback_list(request: Request):
    user = require_user(request)

    if user.get("role") == "admin":
        return {
            "admin_view": True,
            "items": list_all_feedback(),
        }

    return {
        "admin_view": False,
        "items": list_feedback_for_user(user["email"]),
    }


@app.post("/api/feedback")
async def feedback_create(request: Request):
    user = require_user(request)
    payload = await request.json()

    category = (payload.get("category") or "").strip()
    subject = (payload.get("subject") or "").strip()
    page = (payload.get("page") or "").strip()
    message = (payload.get("message") or "").strip()

    if not category or not subject or not message:
        raise HTTPException(status_code=400, detail="Category, subject, and message are required.")

    item = create_feedback(
        email=user["email"],
        role=user.get("role", "user"),
        category=category,
        subject=subject,
        page=page,
        message=message,
    )

    return {"message": "Feedback submitted.", "item": item}


@app.post("/api/curriculum/search")
def curriculum_search(request: Request, payload: ObjectiveRequest):
    require_user(request)
    return engine.search(
        payload.curriculum,
        payload.subject,
        payload.grade_level,
        payload.topic,
        payload.description,
    )


@app.post("/api/objectives/generate")
def objective_suggest(request: Request, payload: ObjectiveRequest):
    require_user(request)
    objectives = engine.build_objectives(
        payload.curriculum,
        payload.subject,
        payload.grade_level,
        payload.topic,
        payload.objective_count,
        payload.difficulty,
        payload.description,
    )
    return {"objectives": objectives, "verbs": engine.bloom_verbs(payload.difficulty)}


@app.post("/api/lesson/generate")
def lesson_generate(request: Request, payload: LessonRequest):
    user = get_current_user_optional(request)

    # 🔒 Guest limit protection
    if not user:
        guest_count = int(request.headers.get("X-Guest-Count", 0))
        if guest_count >= 5:
            raise HTTPException(status_code=403, detail="Guest limit reached")
    if user:
        usage = can_generate_lessons(user)

        if not usage["allowed"]:
            raise HTTPException(
                status_code=403,
                detail=f"Monthly lesson generation limit reached for your {user['plan']} plan.",
            )
            

    profile = get_user_profile(user["id"]) if user else {}
    payload_data = payload.model_dump()
    payload_data["teacher_profile"] = profile

    if not payload_data.get("curriculum") and profile.get("curriculum"):
        payload_data["curriculum"] = profile["curriculum"]

    if not payload_data.get("subject") and profile.get("subjects"):
        payload_data["subject"] = profile["subjects"][0]

    if not payload_data.get("grade_level") and profile.get("grade_levels"):
        payload_data["grade_level"] = profile["grade_levels"][0]

    try:
        result = generate_lesson(payload_data)
        if user:
            increment_generation_count(user["id"])
        return result
    except Exception as e:
        print("LESSON GENERATE ERROR:", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Lesson generation failed: {str(e)}")


@app.post("/api/activity/generate")
def activity_generate(request: Request, payload: ActivityRequest):
    user = require_user(request)
    usage = can_generate_activities(user)

    if not usage["allowed"]:
        raise HTTPException(
            status_code=403,
            detail="Activity generation is available on the Plus plan only.",
        )

    source_mode = getattr(payload, "source_mode", "lesson")

    if source_mode == "lesson":
        if not payload.lesson_payload:
            raise HTTPException(
                status_code=400,
                detail="Lesson data is required before generating an activity.",
            )
    else:
        if not payload.curriculum or not payload.subject or not payload.grade_level or not payload.topic:
            raise HTTPException(
                status_code=400,
                detail="Curriculum, subject, grade level, and topic are required for standalone activity generation.",
            )

    try:
        result = generate_activity(payload.model_dump())
        increment_activity_generation_count(user["id"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        print("ACTIVITY GENERATE ERROR:", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail=f"Activity generation failed: {str(e)}")


@app.get("/api/lessons")
def lessons_list(request: Request):
    user = require_user(request)
    return {"lessons": list_lessons(user["email"])}


@app.get("/api/lessons/{lesson_id}")
def lesson_detail(request: Request, lesson_id: str):
    user = require_user(request)
    lesson = get_lesson(user["email"], lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@app.post("/api/lessons")
def lesson_save(request: Request, payload: SaveLessonRequest):
    user = require_user(request)
    current_lessons = list_lessons(user["email"])
    allowance = can_save_more_lessons(user, len(current_lessons))

    if not allowance["allowed"]:
        raise HTTPException(
            status_code=403,
            detail=f"Saved lesson limit reached for your {user['plan']} plan.",
        )

    saved = save_new_lesson(user["email"], payload.lesson_payload)
    return {"message": "Lesson saved.", "lesson": saved}


@app.put("/api/lessons/{lesson_id}")
def lesson_update(request: Request, lesson_id: str, payload: UpdateLessonRequest):
    user = require_user(request)
    updated = update_existing_lesson(user["email"], lesson_id, payload.lesson_payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson updated.", "lesson": updated}


@app.delete("/api/lessons/{lesson_id}")
def lesson_remove(request: Request, lesson_id: str):
    user = require_user(request)
    deleted = delete_lesson(user["email"], lesson_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson deleted."}


@app.post("/api/export/docx")
def export_docx(request: Request, payload: ExportRequest):
    user = require_user(request)

    if not can_export_docx(user):
        raise HTTPException(
            status_code=403,
            detail="DOCX export is available on the Pro plan only.",
        )

    path = export_to_docx(payload.title, payload.content)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )


@app.post("/api/export/pdf")
def export_pdf(request: Request, payload: ExportRequest):
    user = require_user(request)

    if not can_export_pdf(user):
        raise HTTPException(
            status_code=403,
            detail="PDF export is not available on your current plan.",
        )

    if not payload.content:
        raise HTTPException(
            status_code=400,
            detail="No content provided for export.",
        )

    try:
        path = export_to_pdf(payload.title, payload.content)
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=path.name,
        )
    except Exception as e:
        print("PDF EXPORT ERROR:", type(e).__name__, str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate PDF.",
        )


@app.post("/api/plan/update")
def update_plan(request: Request, payload: PlanUpdateRequest):
    user = require_user(request)

    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Admin plan cannot be changed here.")

    updated = update_user_plan(user["id"], payload.plan)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    saved_count = len(list_lessons(updated["email"]))
    return {
        "message": "Plan updated.",
        "user": updated,
        "plan_status": get_plan_status(updated, saved_count),
    }


@app.get("/api/stripe/config")
def stripe_config(request: Request):
    require_user(request)
    return get_stripe_public_config()


@app.post("/api/stripe/create-checkout-session")
async def stripe_create_checkout_session(request: Request, current_user=Depends(require_user)):
    if current_user["plan"] in {"pro", "plus", "admin"}:
        raise HTTPException(status_code=400, detail="You already have paid access.")

    payload = await request.json()
    target_plan = (payload.get("target_plan") or "pro").strip().lower()

    if target_plan not in {"pro", "plus"}:
        raise HTTPException(status_code=400, detail="Invalid target plan.")

    try:
        session = create_checkout_session(user=current_user, target_plan=target_plan)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Stripe checkout setup failed: {exc}")

    return {"url": session.url, "id": session.id}


@app.post("/api/stripe/create-portal-session")
def stripe_create_portal_session(current_user=Depends(require_user)):
    if current_user["plan"] not in {"pro", "plus", "admin"}:
        raise HTTPException(status_code=400, detail="Billing portal is only available for paid plans.")

    customer_id = (current_user.get("stripe_customer_id") or "").strip()
    if not customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer is stored for this account yet.")

    try:
        session = create_portal_session(customer_id=customer_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Stripe billing portal failed: {exc}")

    return {"url": session.url}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = verify_webhook(payload=payload, signature=sig)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Stripe webhook: {exc}")

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id_raw = (obj.get("metadata") or {}).get("user_id") or obj.get("client_reference_id")
        if user_id_raw:
            user_id = int(user_id_raw)
            subscription_id = obj.get("subscription", "") or ""
            customer_id = obj.get("customer", "") or ""

            update_user_stripe_subscription(
                user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                subscription_status="active",
                subscription_started_at=datetime.now(timezone.utc).isoformat(),
                billing_notes="Stripe Checkout completed",
            )

    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        customer_id = obj.get("customer", "") or ""
        subscription_id = obj.get("id", "") or ""
        status = obj.get("status", "inactive")
        current_period_end = obj.get("current_period_end")
        metadata = obj.get("metadata") or {}
        user_id_raw = metadata.get("user_id")

        user_id = None
        if user_id_raw:
            user_id = int(user_id_raw)
        else:
            matched = find_user_by_stripe_customer_id(customer_id) or find_user_by_stripe_subscription_id(subscription_id)
            if matched:
                user_id = int(matched["id"])

        if user_id:
            update_user_stripe_subscription(
                user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                subscription_status=status,
                subscription_started_at=datetime.now(timezone.utc).isoformat(),
                subscription_renews_at=to_iso_from_unix(current_period_end),
                billing_notes=f"Stripe subscription {status}",
            )

    elif event_type in {"customer.subscription.deleted", "invoice.payment_failed"}:
        customer_id = obj.get("customer", "") or ""
        subscription_id = (
            obj.get("id", "") if event_type == "customer.subscription.deleted"
            else obj.get("subscription", "") or ""
        )

        matched = find_user_by_stripe_subscription_id(subscription_id) or find_user_by_stripe_customer_id(customer_id)

        if matched:
            if event_type == "invoice.payment_failed":
                update_user_stripe_subscription(
                    int(matched["id"]),
                    stripe_customer_id=matched.get("stripe_customer_id", customer_id),
                    stripe_subscription_id=matched.get("stripe_subscription_id", subscription_id),
                    subscription_status="past_due",
                    subscription_started_at=matched.get("subscription_started_at", ""),
                    subscription_renews_at=matched.get("subscription_renews_at", ""),
                    billing_notes="Stripe invoice payment failed",
                )
            else:
                cancel_user_paid_plan(int(matched["id"]), note="Stripe subscription cancelled")

    return JSONResponse({"received": True})


@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "site_url": "https://educaribedu.org",
        },
    )


@app.get("/api/admin/frameworks")
def admin_list_frameworks(
    request: Request,
    curriculum: str = Query(default=""),
    subject: str = Query(default=""),
    level: str = Query(default=""),
    query: str = Query(default=""),
):
    require_admin(request)
    items = list_frameworks(curriculum=curriculum, subject=subject, level=level, query=query)
    return {"frameworks": items}


@app.get("/api/admin/frameworks/{framework_id}")
def admin_get_framework(request: Request, framework_id: str):
    require_admin(request)
    framework = get_framework(framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    return {"framework": framework}


@app.post("/api/admin/frameworks")
def admin_create_framework(request: Request, payload: AdminFrameworkRequest):
    require_admin(request)
    created = create_framework(payload.framework)
    engine.reload_data()
    return {"message": "Framework created and engine reloaded.", "framework": created}


@app.put("/api/admin/frameworks/{framework_id}")
def admin_update_framework(request: Request, framework_id: str, payload: AdminFrameworkRequest):
    require_admin(request)
    updated = update_framework(framework_id, payload.framework)
    if not updated:
        raise HTTPException(status_code=404, detail="Framework not found")
    engine.reload_data()
    return {"message": "Framework updated and engine reloaded.", "framework": updated}


@app.delete("/api/admin/frameworks/{framework_id}")
def admin_delete_framework(request: Request, framework_id: str):
    require_admin(request)
    deleted = delete_framework(framework_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Framework not found")
    engine.reload_data()
    return {"message": "Framework deleted and engine reloaded."}


@app.get("/api/admin/users")
def admin_list_users(request: Request):
    require_admin(request)
    return {"users": list_users(), "signup_events": list_signup_events()}


@app.put("/api/admin/users/{user_id}")
def admin_update_user(request: Request, user_id: int, payload: AdminUserUpdateRequest):
    require_admin(request)

    try:
        updated = update_user_role_plan(user_id, payload.role, payload.plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User updated.", "user": updated}


@app.put("/api/admin/users/{user_id}/billing")
def admin_update_user_billing(request: Request, user_id: int, payload: AdminBillingUpdateRequest):
    require_admin(request)

    try:
        updated = update_user_billing(
            user_id=user_id,
            role=payload.role,
            plan=payload.plan,
            subscription_status=payload.subscription_status,
            payment_provider=payload.payment_provider,
            paypal_customer_id="",
            paypal_subscription_id="",
            subscription_started_at=payload.subscription_started_at,
            subscription_renews_at=payload.subscription_renews_at,
            billing_notes=payload.billing_notes,
            stripe_customer_id=payload.stripe_customer_id,
            stripe_subscription_id=payload.stripe_subscription_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User billing updated.", "user": updated}

    @app.get("/lesson-examples", response_class=HTMLResponse)
def lesson_examples_page(request: Request):
    return templates.TemplateResponse(
        "lesson-examples.html",
        {
            "request": request,
            "site_url": "https://educaribedu.org",
        },
    )