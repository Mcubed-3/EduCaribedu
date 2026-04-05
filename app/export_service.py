from __future__ import annotations

from pathlib import Path
import uuid

from docx import Document
from playwright.sync_api import sync_playwright

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


def export_to_docx(title: str, content: str):
    file_name = f"{uuid.uuid4()}.docx"
    file_path = EXPORT_DIR / file_name

    doc = Document()
    doc.add_heading(title or "Export", level=0)

    for line in (content or "").splitlines():
        stripped = line.strip()
        if not stripped:
            doc.add_paragraph("")
            continue
        doc.add_paragraph(stripped)

    doc.save(file_path)
    return file_path


def export_to_pdf(html: str):
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = EXPORT_DIR / file_name

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <script>
          window.MathJax = {{
            tex: {{
              inlineMath: [['\\\\(', '\\\\)'], ['$', '$']],
              displayMath: [['\\\\[', '\\\\]'], ['$$', '$$']]
            }},
            svg: {{ fontCache: 'global' }}
          }};
        </script>
        <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 40px;
                line-height: 1.6;
                color: #111;
            }}
            h1, h2, h3 {{
                color: #0b3d2e;
            }}
        </style>
    </head>
    <body>
        {html or ""}
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        page.set_content(full_html, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.pdf(
            path=str(file_path),
            format="A4",
            print_background=True,
        )
        browser.close()

    return file_path