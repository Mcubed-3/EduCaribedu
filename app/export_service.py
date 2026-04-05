from playwright.sync_api import sync_playwright
from pathlib import Path
import uuid
import os

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


def export_to_pdf(html: str):
    file_name = f"{uuid.uuid4()}.pdf"
    file_path = EXPORT_DIR / file_name

    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
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
        {html}
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()

        page.set_content(full_html, wait_until="networkidle")

        # Ensure MathJax fully renders
        page.wait_for_function("window.MathJax !== undefined")
        page.wait_for_timeout(1500)

        page.pdf(
            path=str(file_path),
            format="A4",
            print_background=True
        )

        browser.close()

    return file_path