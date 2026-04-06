from __future__ import annotations

import uuid
from pathlib import Path

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

        if stripped.endswith(":") and len(stripped) < 80:
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            continue

        doc.add_paragraph(stripped)

    doc.save(file_path)
    return file_path

def export_to_pdf(html: str, title: str | None = None):
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = EXPORT_DIR / file_name

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <title>{title or "Export"}</title>
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
                background: #f6f1ea;
                color: #14324a;
                margin: 0;
                padding: 0;
            }}
            .wrapper {{
                max-width: 1000px;
                margin: 0 auto;
                padding: 30px;
            }}
            .preview-container {{
                background: #f4efe8;
                border: 1px solid #d7cfc3;
                border-radius: 12px;
                padding: 24px;
            }}
            h1, h2, h3, h4 {{
                color: #14324a;
                margin-top: 0;
            }}
            p, div, span, li {{
                font-size: 16px;
                line-height: 1.7;
            }}
            ul, ol {{
                padding-left: 1.4rem;
            }}
            strong {{
                color: #14324a;
            }}
            mjx-container {{
                font-size: 1.05em !important;
            }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="preview-container">
                {html or ""}
            </div>
        </div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        page.set_content(full_html, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.pdf(
            path=str(file_path),
            format="A4",
            print_background=True,
            margin={
                "top": "15mm",
                "bottom": "15mm",
                "left": "12mm",
                "right": "12mm",
            },
        )
        browser.close()

    return file_path