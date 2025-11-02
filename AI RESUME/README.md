# AI Resume Screening System

A minimal FastAPI web app to parse resumes (PDF/DOCX/TXT), match them to a job description using TF‑IDF cosine similarity plus skill overlap, and rank candidates.

## Features
- Upload multiple resumes (PDF, DOCX, TXT)
- Submit a job description
- AI scoring: TF‑IDF similarity (70%) + skill overlap (30%)
- Extract detected skills
- Ranked table and CSV export

## Prerequisites
- Python 3.9+ recommended

## Setup (PowerShell on Windows)
1) Create and activate a virtual environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
pip install -r requirements.txt
```

3) Run the app

```powershell
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

4) Open in your browser
- http://127.0.0.1:8000

## Notes
- Scoring is heuristic; adjust weights/skills in `backend/services/scorer.py`.
- Data is stored in-memory for simplicity (restarts clear data).
- Add persistence or authentication as needed.
