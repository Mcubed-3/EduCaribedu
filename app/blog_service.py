"""
EduCarib AI – Production blog service.

Database-backed manual blog system with:
- SQLite post storage
- Draft / published status
- Safe image upload support
- Basic HTML sanitising for admin-written posts
- Like / dislike reactions stored per visitor key

This file is safe to call from app startup with init_blog_db().
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

_auth_db_env = os.getenv("AUTH_DB_PATH", "").strip()
DB_PATH = Path(_auth_db_env) if _auth_db_env else STORAGE_DIR / "auth.db"

IMAGE_DIR = BASE_DIR / "static" / "blog_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

VALID_STATUSES = {"draft", "published"}
VALID_REACTIONS = {"like", "dislike"}

ALLOWED_TAGS = {
    "p", "br", "hr", "strong", "b", "em", "i", "u", "ul", "ol", "li",
    "h2", "h3", "h4", "blockquote", "a", "span",
}
ALLOWED_ATTRS = {
    "a": {"href", "target", "rel"},
    "span": {"class"},
}
ALLOWED_PROTOCOLS = ("http://", "https://", "mailto:", "/")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if not _column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_blog_db() -> None:
    """Create and migrate blog tables. Safe to call at startup."""
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'General',
            content TEXT NOT NULL DEFAULT '',
            image_path TEXT NOT NULL DEFAULT '',
            image_alt TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL DEFAULT 'EduCarib AI Team',
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT NOT NULL DEFAULT ''
        )
        """
    )

    _add_column_if_missing(conn, "blog_posts", "views", "INTEGER NOT NULL DEFAULT 0")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS blog_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            visitor_key TEXT NOT NULL,
            reaction TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(post_id, visitor_key),
            FOREIGN KEY(post_id) REFERENCES blog_posts(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_blog_reactions_post ON blog_reactions(post_id)")
    conn.commit()
    conn.close()


def _clean_text(value: str, max_len: int = 5000) -> str:
    value = (value or "").strip()
    if len(value) > max_len:
        value = value[:max_len].strip()
    return value


def _normalise_status(status: str) -> str:
    status = (status or "draft").strip().lower()
    return status if status in VALID_STATUSES else "draft"


def _slugify(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return (text[:80] or secrets.token_hex(6)).strip("-")


def _unique_slug(base_slug: str, exclude_id: Optional[int] = None) -> str:
    conn = _get_conn()
    slug = base_slug
    suffix = 0
    while True:
        if exclude_id:
            row = conn.execute(
                "SELECT id FROM blog_posts WHERE slug = ? AND id != ?",
                (slug, exclude_id),
            ).fetchone()
        else:
            row = conn.execute("SELECT id FROM blog_posts WHERE slug = ?", (slug,)).fetchone()
        if not row:
            conn.close()
            return slug
        suffix += 1
        slug = f"{base_slug}-{suffix}"


def sanitize_content(content: str) -> str:
    """Allow a small safe subset of article HTML."""
    content = (content or "").strip()
    if not content:
        return ""

    if BeautifulSoup is None:
        paragraphs = [f"<p>{escape(p.strip())}</p>" for p in content.split("\n\n") if p.strip()]
        return "\n".join(paragraphs)

    soup = BeautifulSoup(content, "html.parser")

    for tag in list(soup.find_all(True)):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            continue

        allowed = ALLOWED_ATTRS.get(tag.name, set())
        for attr in list(tag.attrs.keys()):
            if attr not in allowed:
                del tag.attrs[attr]

        if tag.name == "a":
            href = str(tag.get("href", "")).strip()
            if not href or not href.lower().startswith(ALLOWED_PROTOCOLS):
                tag.unwrap()
                continue
            tag["href"] = href
            if href.startswith("http"):
                tag["target"] = "_blank"
                tag["rel"] = "noopener noreferrer"

    return str(soup).strip()


def save_image(filename: str, data: bytes) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("File type not allowed. Use jpg, jpeg, png, webp, or gif.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image must be under 5 MB.")

    safe_name = secrets.token_hex(16) + ext
    dest = IMAGE_DIR / safe_name
    dest.write_bytes(data)
    return f"/static/blog_images/{safe_name}"


def delete_image(image_path: str) -> None:
    if not image_path:
        return
    filename = Path(image_path).name
    target = IMAGE_DIR / filename
    try:
        if target.exists() and target.is_file():
            target.unlink()
    except Exception:
        pass


def _date_display(raw: str) -> str:
    try:
        dt = datetime.fromisoformat(raw)
        return f"{dt.day} {dt.strftime('%B %Y')}"
    except Exception:
        return ""


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    raw = d.get("published_at") or d.get("created_at", "")
    d["date_display"] = _date_display(raw)
    try:
        d["date"] = datetime.fromisoformat(raw).strftime("%Y-%m-%d")
    except Exception:
        d["date"] = ""

    word_count = len(re.sub(r"<[^>]+>", " ", d.get("content", "")).split())
    minutes = max(1, round(word_count / 200))
    d["read_time"] = f"{minutes} min read"

    counts = get_reaction_counts_by_post_id(int(d["id"]))
    d.update(counts)
    return d


def _validate_post_fields(title: str, description: str, content: str) -> None:
    if not title.strip():
        raise ValueError("Title is required.")
    if len(title.strip()) > 180:
        raise ValueError("Title must be 180 characters or fewer.")
    if not description.strip():
        raise ValueError("SEO description / summary is required.")
    if len(description.strip()) > 320:
        raise ValueError("Description should be 320 characters or fewer.")
    if not content.strip():
        raise ValueError("Article content is required.")


def create_post(
    title: str,
    description: str,
    category: str,
    content: str,
    author: str,
    image_path: str = "",
    image_alt: str = "",
    status: str = "draft",
) -> Dict[str, Any]:
    title = _clean_text(title, 180)
    description = _clean_text(description, 320)
    category = _clean_text(category or "General", 80)
    author = _clean_text(author or "EduCarib AI Team", 100)
    image_alt = _clean_text(image_alt, 180)
    status = _normalise_status(status)
    clean_content = sanitize_content(content)
    _validate_post_fields(title, description, clean_content)

    now = datetime.utcnow().isoformat()
    slug = _unique_slug(_slugify(title))
    published_at = now if status == "published" else ""

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO blog_posts
            (slug, title, description, category, content, image_path, image_alt,
             author, status, created_at, updated_at, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (slug, title, description, category, clean_content, image_path, image_alt,
         author, status, now, now, published_at),
    )
    conn.commit()
    row_id = int(cur.lastrowid)
    conn.close()
    created = get_post_by_id(row_id)
    if not created:
        raise RuntimeError("Post was created but could not be loaded.")
    return created


def update_post(
    post_id: int,
    title: str,
    description: str,
    category: str,
    content: str,
    author: str,
    image_path: str = "",
    image_alt: str = "",
    status: str = "draft",
) -> Optional[Dict[str, Any]]:
    existing = get_post_by_id(post_id)
    if not existing:
        return None

    title = _clean_text(title, 180)
    description = _clean_text(description, 320)
    category = _clean_text(category or "General", 80)
    author = _clean_text(author or "EduCarib AI Team", 100)
    image_alt = _clean_text(image_alt, 180)
    status = _normalise_status(status)
    clean_content = sanitize_content(content)
    _validate_post_fields(title, description, clean_content)

    now = datetime.utcnow().isoformat()
    slug = _unique_slug(_slugify(title), exclude_id=post_id)
    published_at = existing.get("published_at", "")
    if status == "published" and not published_at:
        published_at = now
    if status == "draft":
        published_at = existing.get("published_at", "")

    conn = _get_conn()
    conn.execute(
        """
        UPDATE blog_posts
        SET slug=?, title=?, description=?, category=?, content=?, image_path=?,
            image_alt=?, author=?, status=?, updated_at=?, published_at=?
        WHERE id=?
        """,
        (slug, title, description, category, clean_content, image_path, image_alt,
         author, status, now, published_at, post_id),
    )
    conn.commit()
    conn.close()
    return get_post_by_id(post_id)


def delete_post(post_id: int) -> bool:
    post = get_post_by_id(post_id)
    if not post:
        return False
    delete_image(post.get("image_path", ""))
    conn = _get_conn()
    conn.execute("DELETE FROM blog_reactions WHERE post_id=?", (post_id,))
    conn.execute("DELETE FROM blog_posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()
    return True


def get_post_by_id(post_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def get_post_by_slug(slug: str, published_only: bool = True) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    if published_only:
        row = conn.execute(
            "SELECT * FROM blog_posts WHERE slug=? AND status='published'",
            (slug,),
        ).fetchone()
    else:
        row = conn.execute("SELECT * FROM blog_posts WHERE slug=?", (slug,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def list_posts(published_only: bool = True) -> List[Dict[str, Any]]:
    conn = _get_conn()
    if published_only:
        rows = conn.execute(
            """
            SELECT * FROM blog_posts
            WHERE status='published'
            ORDER BY COALESCE(NULLIF(published_at, ''), created_at) DESC
            """
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM blog_posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_related_posts(slug: str, limit: int = 3) -> List[Dict[str, Any]]:
    post = get_post_by_slug(slug, published_only=True)
    category = post.get("category", "") if post else ""
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT * FROM blog_posts
        WHERE slug != ? AND status='published'
        ORDER BY CASE WHEN category=? THEN 0 ELSE 1 END,
                 COALESCE(NULLIF(published_at, ''), created_at) DESC
        LIMIT ?
        """,
        (slug, category, limit),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def increment_view(slug: str) -> None:
    conn = _get_conn()
    conn.execute("UPDATE blog_posts SET views = views + 1 WHERE slug=? AND status='published'", (slug,))
    conn.commit()
    conn.close()


def make_visitor_key(ip: str = "", user_agent: str = "") -> str:
    raw = f"{ip}|{user_agent}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()


def get_reaction_counts_by_post_id(post_id: int) -> Dict[str, int]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT reaction, COUNT(*) AS total FROM blog_reactions WHERE post_id=? GROUP BY reaction",
        (post_id,),
    ).fetchall()
    conn.close()
    counts = {"likes": 0, "dislikes": 0}
    for row in rows:
        if row["reaction"] == "like":
            counts["likes"] = int(row["total"])
        elif row["reaction"] == "dislike":
            counts["dislikes"] = int(row["total"])
    return counts


def set_reaction(slug: str, visitor_key: str, reaction: str) -> Dict[str, Any]:
    reaction = (reaction or "").strip().lower()
    if reaction not in VALID_REACTIONS:
        raise ValueError("Reaction must be like or dislike.")

    post = get_post_by_slug(slug, published_only=True)
    if not post:
        raise LookupError("Post not found.")

    now = datetime.utcnow().isoformat()
    conn = _get_conn()
    existing = conn.execute(
        "SELECT reaction FROM blog_reactions WHERE post_id=? AND visitor_key=?",
        (post["id"], visitor_key),
    ).fetchone()

    if existing and existing["reaction"] == reaction:
        conn.execute(
            "DELETE FROM blog_reactions WHERE post_id=? AND visitor_key=?",
            (post["id"], visitor_key),
        )
        user_reaction = ""
    else:
        conn.execute(
            """
            INSERT INTO blog_reactions (post_id, visitor_key, reaction, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(post_id, visitor_key)
            DO UPDATE SET reaction=excluded.reaction, updated_at=excluded.updated_at
            """,
            (post["id"], visitor_key, reaction, now, now),
        )
        user_reaction = reaction

    conn.commit()
    conn.close()

    counts = get_reaction_counts_by_post_id(int(post["id"]))
    return {"ok": True, "reaction": user_reaction, **counts}
