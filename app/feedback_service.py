from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

DB_PATH = STORAGE_DIR / "feedback.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_feedback_db() -> None:
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            page TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def create_feedback(
    email: str,
    role: str,
    category: str,
    subject: str,
    page: str,
    message: str,
) -> Dict[str, Any]:
    email = email.strip().lower()
    role = (role or "user").strip().lower()
    category = category.strip()
    subject = subject.strip()
    page = page.strip()
    message = message.strip()
    created_at = datetime.utcnow().isoformat()

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO feedback_messages (
            email, role, category, subject, page, message, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
        """,
        (email, role, category, subject, page, message, created_at),
    )
    conn.commit()
    feedback_id = cur.lastrowid
    conn.close()

    return get_feedback_by_id(feedback_id)


def get_feedback_by_id(feedback_id: int) -> Dict[str, Any]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM feedback_messages WHERE id = ?", (feedback_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}


def list_feedback_for_user(email: str) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM feedback_messages
        WHERE email = ?
        ORDER BY created_at DESC
        """,
        (email.strip().lower(),),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_all_feedback() -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM feedback_messages
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]