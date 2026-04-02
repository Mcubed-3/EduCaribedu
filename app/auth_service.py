from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

DB_PATH = STORAGE_DIR / "auth.db"

SESSION_DAYS = 14

PLAN_LIMITS = {
    "free": {
        "monthly_generations": 10,
        "saved_lessons": 5,
        "docx_export": False,
        "pdf_export": True,
        "ads_enabled": True,
    },
    "pro": {
        "monthly_generations": None,
        "saved_lessons": None,
        "docx_export": True,
        "pdf_export": True,
        "ads_enabled": False,
    },
    "admin": {
        "monthly_generations": None,
        "saved_lessons": None,
        "docx_export": True,
        "pdf_export": True,
        "ads_enabled": False,
    },
}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db() -> None:
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            plan TEXT NOT NULL DEFAULT 'free',
            subscription_status TEXT NOT NULL DEFAULT 'inactive',
            payment_provider TEXT NOT NULL DEFAULT '',
            paypal_customer_id TEXT NOT NULL DEFAULT '',
            paypal_subscription_id TEXT NOT NULL DEFAULT '',
            subscription_started_at TEXT NOT NULL DEFAULT '',
            subscription_renews_at TEXT NOT NULL DEFAULT '',
            billing_notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_usage (
            user_id INTEGER NOT NULL,
            month_key TEXT NOT NULL,
            generation_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(user_id, month_key),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    # lightweight migration support
    existing_cols = {
        row["name"]
        for row in cur.execute("PRAGMA table_info(users)").fetchall()
    }

    extra_columns = {
        "subscription_status": "TEXT NOT NULL DEFAULT 'inactive'",
        "payment_provider": "TEXT NOT NULL DEFAULT ''",
        "paypal_customer_id": "TEXT NOT NULL DEFAULT ''",
        "paypal_subscription_id": "TEXT NOT NULL DEFAULT ''",
        "subscription_started_at": "TEXT NOT NULL DEFAULT ''",
        "subscription_renews_at": "TEXT NOT NULL DEFAULT ''",
        "billing_notes": "TEXT NOT NULL DEFAULT ''",
    }

    for col, ddl in extra_columns.items():
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")

    conn.commit()
    conn.close()

    _ensure_default_admin()


def _ensure_default_admin() -> None:
    admin_email = os.getenv("ADMIN_EMAIL", "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()

    if not admin_email or not admin_password:
        return

    existing = get_user_by_email(admin_email)
    if existing:
        return

    create_user(
        admin_email,
        admin_password,
        role="admin",
        plan="admin",
        subscription_status="active",
        payment_provider="manual",
        billing_notes="Bootstrap admin account",
    )


def _hash_password(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    )
    return dk.hex()


def _normalize_plan(role: str, plan: str) -> str:
    if role == "admin":
        return "admin"
    return plan or "free"


def _normalize_subscription_status(plan: str, subscription_status: str) -> str:
    if plan in {"pro", "admin"}:
        return subscription_status or "active"
    return subscription_status or "inactive"


def create_user(
    email: str,
    password: str,
    role: str = "user",
    plan: str = "free",
    subscription_status: str = "inactive",
    payment_provider: str = "",
    paypal_customer_id: str = "",
    paypal_subscription_id: str = "",
    subscription_started_at: str = "",
    subscription_renews_at: str = "",
    billing_notes: str = "",
) -> Dict[str, Any]:
    email = email.strip().lower()
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    created_at = datetime.utcnow().isoformat()
    plan = _normalize_plan(role, plan)
    subscription_status = _normalize_subscription_status(plan, subscription_status)

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (
            email, password_hash, salt, role, plan,
            subscription_status, payment_provider, paypal_customer_id, paypal_subscription_id,
            subscription_started_at, subscription_renews_at, billing_notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            password_hash,
            salt,
            role,
            plan,
            subscription_status,
            payment_provider,
            paypal_customer_id,
            paypal_subscription_id,
            subscription_started_at,
            subscription_renews_at,
            billing_notes,
            created_at,
        ),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()

    return get_user_by_id(user_id)  # type: ignore[return-value]


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def list_users() -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id, email, role, plan, subscription_status, payment_provider,
            paypal_customer_id, paypal_subscription_id,
            subscription_started_at, subscription_renews_at,
            billing_notes, created_at
        FROM users
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_user_role_plan(user_id: int, role: str, plan: str) -> Optional[Dict[str, Any]]:
    role = role.strip().lower()
    plan = plan.strip().lower()

    if role not in {"user", "admin"}:
        raise ValueError("Invalid role")

    if plan not in {"free", "pro", "admin"}:
        raise ValueError("Invalid plan")

    if role == "admin":
        plan = "admin"
        subscription_status = "active"
    else:
        if plan == "admin":
            plan = "pro"
        subscription_status = "active" if plan == "pro" else "inactive"

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET role = ?, plan = ?, subscription_status = ?
        WHERE id = ?
        """,
        (role, plan, subscription_status, user_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()

    if not updated:
        return None

    return get_user_by_id(user_id)


def update_user_plan(user_id: int, plan: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_id(user_id)
    if not user:
        return None

    role = user["role"]
    plan = plan.strip().lower()

    if plan not in {"free", "pro", "admin"}:
        raise ValueError("Invalid plan")

    if role == "admin":
        plan = "admin"
    elif plan == "admin":
        plan = "pro"

    subscription_status = "active" if plan in {"pro", "admin"} else "inactive"

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET plan = ?, subscription_status = ?
        WHERE id = ?
        """,
        (plan, subscription_status, user_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()

    if not updated:
        return None

    return get_user_by_id(user_id)


def update_user_billing(
    user_id: int,
    role: str,
    plan: str,
    subscription_status: str,
    payment_provider: str,
    paypal_customer_id: str,
    paypal_subscription_id: str,
    subscription_started_at: str,
    subscription_renews_at: str,
    billing_notes: str,
) -> Optional[Dict[str, Any]]:
    role = role.strip().lower()
    plan = plan.strip().lower()
    subscription_status = subscription_status.strip().lower()

    if role not in {"user", "admin"}:
        raise ValueError("Invalid role")

    if plan not in {"free", "pro", "admin"}:
        raise ValueError("Invalid plan")

    if subscription_status not in {"inactive", "trialing", "active", "past_due", "cancelled"}:
        raise ValueError("Invalid subscription status")

    if role == "admin":
        plan = "admin"
        subscription_status = "active"
    elif plan == "admin":
        plan = "pro"

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET
            role = ?,
            plan = ?,
            subscription_status = ?,
            payment_provider = ?,
            paypal_customer_id = ?,
            paypal_subscription_id = ?,
            subscription_started_at = ?,
            subscription_renews_at = ?,
            billing_notes = ?
        WHERE id = ?
        """,
        (
            role,
            plan,
            subscription_status,
            payment_provider.strip(),
            paypal_customer_id.strip(),
            paypal_subscription_id.strip(),
            subscription_started_at.strip(),
            subscription_renews_at.strip(),
            billing_notes.strip(),
            user_id,
        ),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()

    if not updated:
        return None

    return get_user_by_id(user_id)


def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)
    if not user:
        return None

    expected = user["password_hash"]
    actual = _hash_password(password, user["salt"])

    if hmac.compare_digest(expected, actual):
        return {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "plan": user["plan"],
            "subscription_status": user.get("subscription_status", "inactive"),
            "payment_provider": user.get("payment_provider", ""),
            "paypal_customer_id": user.get("paypal_customer_id", ""),
            "paypal_subscription_id": user.get("paypal_subscription_id", ""),
            "subscription_started_at": user.get("subscription_started_at", ""),
            "subscription_renews_at": user.get("subscription_renews_at", ""),
            "billing_notes": user.get("billing_notes", ""),
            "created_at": user["created_at"],
        }

    return None


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=SESSION_DAYS)

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sessions (token, user_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            token,
            user_id,
            created_at.isoformat(),
            expires_at.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return token


def get_user_by_session(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            s.token, s.expires_at,
            u.id, u.email, u.role, u.plan,
            u.subscription_status, u.payment_provider,
            u.paypal_customer_id, u.paypal_subscription_id,
            u.subscription_started_at, u.subscription_renews_at,
            u.billing_notes, u.created_at
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ?
        """,
        (token,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at < datetime.utcnow():
        delete_session(token)
        return None

    return {
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
        "plan": row["plan"],
        "subscription_status": row["subscription_status"],
        "payment_provider": row["payment_provider"],
        "paypal_customer_id": row["paypal_customer_id"],
        "paypal_subscription_id": row["paypal_subscription_id"],
        "subscription_started_at": row["subscription_started_at"],
        "subscription_renews_at": row["subscription_renews_at"],
        "billing_notes": row["billing_notes"],
        "created_at": row["created_at"],
    }


def delete_session(token: str) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def get_plan_limits(plan: str) -> Dict[str, Any]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def get_month_key(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.utcnow()
    return dt.strftime("%Y-%m")


def get_generation_count(user_id: int, month_key: Optional[str] = None) -> int:
    month_key = month_key or get_month_key()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT generation_count
        FROM monthly_usage
        WHERE user_id = ? AND month_key = ?
        """,
        (user_id, month_key),
    )
    row = cur.fetchone()
    conn.close()
    return int(row["generation_count"]) if row else 0


def increment_generation_count(user_id: int, month_key: Optional[str] = None) -> int:
    month_key = month_key or get_month_key()
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO monthly_usage (user_id, month_key, generation_count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, month_key)
        DO UPDATE SET generation_count = generation_count + 1
        """,
        (user_id, month_key),
    )

    conn.commit()

    cur.execute(
        """
        SELECT generation_count
        FROM monthly_usage
        WHERE user_id = ? AND month_key = ?
        """,
        (user_id, month_key),
    )
    row = cur.fetchone()
    conn.close()
    return int(row["generation_count"]) if row else 0


def can_generate_lessons(user: Dict[str, Any]) -> Dict[str, Any]:
    limits = get_plan_limits(user["plan"])
    limit = limits["monthly_generations"]

    if limit is None:
        return {
            "allowed": True,
            "used": get_generation_count(user["id"]),
            "limit": None,
            "remaining": None,
        }

    used = get_generation_count(user["id"])
    remaining = max(limit - used, 0)

    return {
        "allowed": used < limit,
        "used": used,
        "limit": limit,
        "remaining": remaining,
    }


def can_save_more_lessons(user: Dict[str, Any], current_saved_count: int) -> Dict[str, Any]:
    limits = get_plan_limits(user["plan"])
    limit = limits["saved_lessons"]

    if limit is None:
        return {
            "allowed": True,
            "used": current_saved_count,
            "limit": None,
            "remaining": None,
        }

    remaining = max(limit - current_saved_count, 0)

    return {
        "allowed": current_saved_count < limit,
        "used": current_saved_count,
        "limit": limit,
        "remaining": remaining,
    }


def can_export_docx(user: Dict[str, Any]) -> bool:
    return bool(get_plan_limits(user["plan"]).get("docx_export", False))


def can_export_pdf(user: Dict[str, Any]) -> bool:
    return bool(get_plan_limits(user["plan"]).get("pdf_export", True))


def get_plan_status(user: Dict[str, Any], saved_lesson_count: int) -> Dict[str, Any]:
    generation = can_generate_lessons(user)
    saved = can_save_more_lessons(user, saved_lesson_count)
    limits = get_plan_limits(user["plan"])

    return {
        "plan": user["plan"],
        "role": user["role"],
        "subscription_status": user.get("subscription_status", "inactive"),
        "payment_provider": user.get("payment_provider", ""),
        "monthly_generations": generation,
        "saved_lessons": saved,
        "docx_export": limits["docx_export"],
        "pdf_export": limits["pdf_export"],
        "ads_enabled": limits["ads_enabled"],
    }