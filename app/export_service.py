from __future__ import annotations

import uuid
from pathlib import Path

from docx import Document
from playwright.sync_api import sync_playwright

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


PREVIEW_EXPORT_STYLE = """
<style>
  body {
    font-family: Arial, sans-serif;
    background: #f6f1ea;
    color: #14324a;
    margin: 0;
    padding: 0;
  }

  .export-shell {
    max-width: 980px;
    margin: 0 auto;
    padding: 32px;
  }

  .preview-card {
    background: #f4efe8;
    border: 1px solid #d7cfc3;
    border-radius: 12px;
    padding: 24px;
    box-sizing: border-box;
  }

  .preview-card h1,
  .preview-card h2,
  .preview-card h3,
  .preview-card h4 {
    color: #14324a;
    margin-top: 0;
  }

  .preview-card p,
  .preview-card div,
  .preview-card span,
  .preview-card li {
    line-height: 1.7;
    font-size: 16px;
  }

  .preview-card ul,
  .preview-card ol {
    margin-top: 0.3rem;
    margin-bottom: 1rem;
    padding-left: 1.4rem;
  }

  .preview-card strong {
    color: #14324a;
  }

  .preview-card table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
  }

  .preview-card th,
  .preview-card td {
    border: 1px solid #d7cfc3;
    padding: 8px 10px;
    vertical-align: top;
  }

  .preview-card mjx-container {
    font-size: 1.02em !important;
  }

  .preview-card .math-block {
    margin: 0.35rem 0;
  }
</style>
"""


def export_to_docx(title: str, content: str):
    file_name = f"{uuid.uuid4()}.docx"
    file_path = EXPORT_DIR / file_name

    doc = Document()
    doc.add_heading(title or "Export", level=0)

    for line in (content or "").splitlines():
        stripped = line.rstrip()
        if not stripped:
            doc.add_paragraph("")
            continue

        if stripped.endswith(":") and len(stripped) < 80:
            doc.add_paragraph(stripped).bold = True
            continue

        doc.add_paragraph(stripped)

    doc.save(file_path)
    return file_path


def export_to_pdf(html: str, title: str = "Export"):
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = EXPORT_DIR / file_name

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <title>{title}</title>
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
        {PREVIEW_EXPORT_STYLE}
    </head>
    <body>
        <div class="export-shell">
          <div class="preview-card">
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

        page.wait_for_timeout(1800)

        page.pdf(
            path=str(file_path),
            format="A4",
            print_background=True,
            margin={
                "top": "18mm",
                "right": "14mm",
                "bottom": "18mm",
                "left": "14mm",
            },
        )
        browser.close()

    return file_path