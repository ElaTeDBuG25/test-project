from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .services.parser import extract_text_from_bytes
from .services.scorer import ScoreEngine, extract_skills

app = FastAPI(title="AI Resume Screening")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# In-memory storage
class Candidate:
    def __init__(self, id: int, name: str, email: Optional[str], filename: str, text: str):
        self.id = id
        self.name = name or "Unknown"
        self.email = email
        self.filename = filename
        self.text = text
        self.skills: List[str] = sorted(extract_skills(text))
        self.scores: Optional[dict] = None

candidates: List[Candidate] = []
next_candidate_id = 1

current_job: dict | None = None  # {id, description, skills}
next_job_id = 1

engine = ScoreEngine()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/job")
async def set_job(description: str = Form(...)):
    global current_job, next_job_id
    if not description or not description.strip():
        raise HTTPException(status_code=400, detail="Job description is required")
    job_skills = sorted(extract_skills(description))
    job = {"id": next_job_id, "description": description, "skills": job_skills}
    current_job = job
    next_job_id += 1
    return {"ok": True, "job": job}


@app.post("/api/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
):
    global next_candidate_id
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    created = []
    for f in files:
        raw = await f.read()
        try:
            text = extract_text_from_bytes(raw, f.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse {f.filename}: {e}")

        # Optionally persist uploaded file
        dest = UPLOADS_DIR / f.filename
        try:
            with dest.open("wb") as out:
                out.write(raw)
        except Exception:
            pass  # non-fatal

        cand = Candidate(id=next_candidate_id, name=name or f.filename, email=email, filename=f.filename, text=text)
        next_candidate_id += 1
        candidates.append(cand)
        created.append({
            "id": cand.id,
            "name": cand.name,
            "email": cand.email,
            "filename": cand.filename,
            "skills": cand.skills,
        })

    return {"ok": True, "count": len(created), "candidates": created}


@app.get("/api/candidates")
async def list_candidates():
    return {
        "ok": True,
        "candidates": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "filename": c.filename,
                "skills": c.skills,
                "scores": c.scores,
            }
            for c in candidates
        ],
    }


@app.post("/api/screen")
async def screen():
    if not current_job:
        raise HTTPException(status_code=400, detail="Set a job description first")
    if not candidates:
        return {"ok": True, "job": current_job, "results": []}

    job_desc = current_job["description"]
    job_skills = set(current_job["skills"]) if current_job else set()

    results = []
    for c in candidates:
        s = engine.score(job_desc, c.text, job_skills=job_skills, resume_skills=set(c.skills))
        c.scores = s
        results.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "filename": c.filename,
            "skills": c.skills,
            "scores": s,
        })

    # Sort by total descending
    results.sort(key=lambda r: r["scores"]["total"], reverse=True)

    return {"ok": True, "job": current_job, "results": results}


@app.get("/api/export")
async def export_csv():
    if not candidates:
        raise HTTPException(status_code=400, detail="No candidates to export")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "email", "filename", "similarity", "skill_overlap", "total", "skills"])
    for c in candidates:
        sim = c.scores.get("similarity") if c.scores else None
        overlap = c.scores.get("skill_overlap") if c.scores else None
        total = c.scores.get("total") if c.scores else None
        writer.writerow([
            c.id,
            c.name,
            c.email or "",
            c.filename,
            f"{sim:.3f}" if sim is not None else "",
            f"{overlap:.3f}" if overlap is not None else "",
            f"{total:.1f}" if total is not None else "",
            "; ".join(c.skills),
        ])

    mem = io.BytesIO(buf.getvalue().encode("utf-8"))
    headers = {"Content-Disposition": "attachment; filename=screening_results.csv"}
    return StreamingResponse(mem, media_type="text/csv", headers=headers)
