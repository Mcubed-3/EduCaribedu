from __future__ import annotations

import html
import re
import uuid
from pathlib import Path

from docx import Document
from docx.shared import Pt
from playwright.sync_api import sync_playwright

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

BOLD_LABELS = ("Formula:", "Substitute:", "Simplify:", "Answer:", "Method:", "Worked Example:")


def _clean_text(value: str) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return stripped.endswith(":") and len(stripped) <= 80 and not _is_numbered_item(stripped)


def _is_list_item(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("- ") or stripped.startswith("• ")


def _is_numbered_item(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return re.match(r"^\d+\.\s", stripped) is not None


def _starts_with_bold_label(line: str) -> bool:
    stripped = line.strip()
    return any(stripped.startswith(label) for label in BOLD_LABELS)


def _split_label_line(line: str):
    stripped = line.strip()
    for label in BOLD_LABELS:
        if stripped.startswith(label):
            return label, stripped[len(label):].strip()
    return None, stripped


def _build_html_from_text(title: str, content: str) -> str:
    safe_title = html.escape(title or "Export")
    lines = _clean_text(content).splitlines()

    html_lines = [
        "<html>",
        "<head>",
        '<meta charset="utf-8" />',
        f"<title>{safe_title}</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; color: #14324a; background: white; margin: 0; padding: 28px; line-height: 1.55; }",
        ".wrapper { max-width: 900px; margin: 0 auto; }",
        "h1 { font-size: 22px; margin: 0 0 18px 0; }",
        "h2 { font-size: 18px; margin: 20px 0 10px 0; }",
        "p { margin: 0 0 10px 0; white-space: pre-wrap; }",
        ".list-item { margin: 0 0 8px 0; white-space: pre-wrap; }",
        ".number-item { margin: 0 0 10px 0; white-space: pre-wrap; }",
        ".label-line { margin: 0 0 10px 0; white-space: pre-wrap; }",
        ".spacer { height: 10px; }",
        "</style>",
        "</head>",
        "<body>",
        '<div class="wrapper">',
    ]

    if title:
        html_lines.append(f"<h1>{safe_title}</h1>")

    for line in lines:
        stripped = line.strip()

        if not stripped:
            html_lines.append('<div class="spacer"></div>')
            continue

        if _starts_with_bold_label(stripped):
            label, rest = _split_label_line(stripped)
            html_lines.append(
                f'<p class="label-line"><strong>{html.escape(label)}</strong> {html.escape(rest)}</p>'
            )
            continue

        escaped = html.escape(line)

        if _is_heading(stripped):
            html_lines.append(f"<h2>{html.escape(stripped[:-1])}</h2>")
        elif _is_numbered_item(stripped):
            html_lines.append(f'<p class="number-item">{escaped}</p>')
        elif _is_list_item(stripped):
            html_lines.append(f'<p class="list-item">{escaped}</p>')
        else:
            html_lines.append(f"<p>{escaped}</p>")

    html_lines.extend([
        "</div>",
        "</body>",
        "</html>",
    ])

    return "\n".join(html_lines)


def export_to_docx(title: str, content: str):
    file_name = f"{uuid.uuid4()}.docx"
    file_path = EXPORT_DIR / file_name

    doc = Document()
    doc.add_heading(title or "Export", level=0)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Arial"
    normal_style.font.size = Pt(11)

    for line in _clean_text(content).splitlines():
        stripped = line.strip()

        if not stripped:
            doc.add_paragraph("")
            continue

        if _is_heading(stripped):
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            continue

        if _starts_with_bold_label(stripped):
            label, rest = _split_label_line(stripped)
            p = doc.add_paragraph()
            label_run = p.add_run(label)
            label_run.bold = True
            if rest:
                p.add_run(f" {rest}")
            continue

        if _is_list_item(stripped):
            doc.add_paragraph(stripped, style="List Bullet")
            continue

        doc.add_paragraph(stripped)

    doc.save(file_path)
    return file_path


def export_to_pdf(title: str, content: str):
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = EXPORT_DIR / file_name

    full_html = _build_html_from_text(title=title or "Export", content=content or "")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        page.set_content(full_html, wait_until="load")
        page.pdf(
            path=str(file_path),
            format="A4",
            print_background=True,
            margin={
                "top": "15mm",
                "bottom": "15mm",
                "left": "15mm",
                "right": "15mm",
            },
        )
        browser.close()

    return file_path