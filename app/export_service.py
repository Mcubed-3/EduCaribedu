from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import List

from docx import Document
from docx.shared import Inches, Pt
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


BASE_DIR = Path(__file__).parent
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def _sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w\s\-]", "", name).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:80] or "lesson_export"


def _split_lines(text: str) -> List[str]:
    return [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]


def _is_heading(line: str) -> bool:
    if not line:
        return False
    heading_candidates = {
        "Objectives:",
        "Prior Knowledge:",
        "Resources:",
        "Assessment:",
        "Reflection:",
        "Engagement:",
        "Exploration:",
        "Explanation:",
        "Evaluation:",
        "Extension:",
        "Creativity:",
        "Critical Thinking:",
        "Communication:",
        "Collaboration:",
    }
    return line.strip() in heading_candidates


def export_to_docx(title: str, content: str) -> Path:
    filename = f"{_sanitize_filename(title)}_{uuid.uuid4().hex[:8]}.docx"
    out_path = EXPORT_DIR / filename

    doc = Document()

    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)

    title_para = doc.add_paragraph()
    title_run = title_para.add_run(title.strip() or "Lesson Plan")
    title_run.bold = True
    title_run.font.size = Pt(18)

    lines = _split_lines(content)

    started = False
    for raw_line in lines:
        line = raw_line.strip()

        if not started and line == title.strip():
            started = True
            continue
        started = True

        if not line:
            doc.add_paragraph("")
            continue

        if _is_heading(line):
            p = doc.add_paragraph()
            r = p.add_run(line)
            r.bold = True
            r.font.size = Pt(13)
            continue

        if line.startswith("- "):
            doc.add_paragraph(line[2:].strip(), style="List Bullet")
            continue

        if re.match(r"^\d+\.\s", line):
            doc.add_paragraph(re.sub(r"^\d+\.\s*", "", line), style="List Number")
            continue

        doc.add_paragraph(line)

    doc.save(out_path)
    return out_path


def export_to_pdf(title: str, content: str) -> Path:
    filename = f"{_sanitize_filename(title)}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = EXPORT_DIR / filename

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_LEFT,
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "CustomBullet",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-8,
    )

    story = [Paragraph(title.strip() or "Lesson Plan", title_style)]

    lines = _split_lines(content)
    started = False

    for raw_line in lines:
        line = raw_line.strip()

        if not started and line == title.strip():
            started = True
            continue
        started = True

        if not line:
            story.append(Spacer(1, 6))
            continue

        safe = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        if _is_heading(line):
            story.append(Paragraph(safe, heading_style))
            continue

        if line.startswith("- "):
            bullet_text = "• " + safe[2:].strip()
            story.append(Paragraph(bullet_text, bullet_style))
            continue

        if re.match(r"^\d+\.\s", line):
            story.append(Paragraph(safe, body_style))
            continue

        story.append(Paragraph(safe, body_style))

    doc.build(story)
    return out_path