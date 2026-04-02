# EduCarib AI - Local Python Build

This is a local-first redesign of EduCarib AI with a **FastAPI backend** and a **curriculum engine starter layer**.

## What is included

- FastAPI backend
- local curriculum engine starter
- NSC starter mappings
- CSEC starter mappings
- Bloom difficulty mapping
- 5Es and 4Cs lesson structures
- curriculum match endpoint
- objective suggestion endpoint
- lesson generation endpoint
- simple modern dashboard UI

## What is not yet included

- full parsing of every uploaded PDF into deep searchable records
- teacher auth
- subscription billing
- PDF/DOCX export
- database persistence

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

## Project structure

```text
app/
  main.py
  models.py
  curriculum_engine.py
  lesson_generator.py
  data/
    curriculum_seed.json
    bloom_verbs.json
  templates/
    index.html
  static/
    styles.css
    app.js
```

## Recommended next upgrade

1. expand `curriculum_seed.json` using the uploaded NSC and CSEC files.
2. add a database to persist users and lessons.
3. add admin upload tools.
4. connect OpenAI or another LLM only after the structured curriculum layer is strong.

## Notes

This build is designed so the **curriculum engine can remain portable** even if you later move the frontend to another stack or into Emergent.
