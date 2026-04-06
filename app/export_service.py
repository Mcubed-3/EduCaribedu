from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from docx import Document
from docx.shared import Inches
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


def export_to_docx_from_snapshot(title: str, html: str):
    file_name = f"{uuid.uuid4()}.docx"
    file_path = EXPORT_DIR / file_name

    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = Path(tmpdir) / "preview.png"
        _capture_preview_snapshot(html=html, image_path=image_path)

        doc = Document()
        doc.add_heading(title or "Export", level=0)
        doc.add_picture(str(image_path), width=Inches(6.5))
        doc.save(file_path)

    return file_path


def export_to_pdf(html: str, title: str | None = None):
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = EXPORT_DIR / file_name

    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = Path(tmpdir) / "preview.png"
        _capture_preview_snapshot(html=html, image_path=image_path)

        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1240, "height": 1754})

            pdf_html = f"""
            <html>
            <head>
                <meta charset="utf-8" />
                <title>{title or "Export"}</title>
                <style>
                    @page {{
                        size: A4;
                        margin: 12mm;
                    }}

                    html, body {{
                        margin: 0;
                        padding: 0;
                        background: white;
                    }}

                    .page {{
                        width: 100%;
                        box-sizing: border-box;
                    }}

                    img {{
                        width: 100%;
                        height: auto;
                        display: block;
                    }}
                </style>
            </head>
            <body>
                <div class="page">
                    <img src="file://{image_path.resolve()}" />
                </div>
            </body>
            </html>
            """

            page.set_content(pdf_html, wait_until="load")
            page.pdf(
                path=str(file_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "12mm",
                    "bottom": "12mm",
                    "left": "12mm",
                    "right": "12mm",
                },
            )
            browser.close()

    return file_path


def _capture_preview_snapshot(html: str, image_path: Path):
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
            chtml: {{
              scale: 1.0
            }},
            startup: {{
              typeset: true
            }}
          }};
        </script>
        <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>

        <style>
            html, body {{
                margin: 0;
                padding: 0;
                background: #f6f1ea;
                font-family: Arial, sans-serif;
                color: #14324a;
            }}

            body {{
                padding: 24px;
            }}

            .wrapper {{
                max-width: 1000px;
                margin: 0 auto;
            }}

            .preview-container {{
                background: #f4efe8;
                border: 1px solid #d7cfc3;
                border-radius: 12px;
                padding: 24px;
                box-sizing: border-box;
                overflow-wrap: break-word;
                word-wrap: break-word;
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
            <div class="preview-container" id="preview">
                {html or ""}
            </div>
        </div>
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1240, "height": 2200, "device_scale_factor": 2})
        page.set_content(full_html, wait_until="domcontentloaded")

        page.wait_for_function("window.MathJax !== undefined")
        page.evaluate(
            """
            async () => {
              if (window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) {
                await window.MathJax.startup.promise;
              }
              if (window.MathJax && window.MathJax.typesetPromise) {
                await window.MathJax.typesetPromise();
              }
            }
            """
        )
        page.wait_for_timeout(500)

        preview = page.locator("#preview")
        preview.screenshot(path=str(image_path))
        browser.close()