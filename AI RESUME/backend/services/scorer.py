from __future__ import annotations

import math
import re
from typing import Iterable, Set

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Minimal skills lexicon; extend as needed
SKILLS = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "ruby", "php", "swift", "kotlin", "rust", "sql",
    # Data/ML
    "machine learning", "deep learning", "nlp", "computer vision", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "data analysis", "data engineering", "etl", "airflow", "spark", "hadoop", "power bi", "tableau", "excel",
    # Cloud/DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "ci/cd", "jenkins", "gitlab ci", "github actions",
    # Web/Frameworks
    "react", "angular", "vue", "django", "flask", "fastapi", "spring", "spring boot", "node.js", "express", ".net", 
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "snowflake", "redshift", "bigquery",
    # Testing/QA
    "unit testing", "integration testing", "pytest", "jest", "cypress", "selenium",
    # Misc
    "rest", "graphql", "microservices", "agile", "scrum", "jira", "linux", "bash", "shell", "oop", "design patterns"
}

_word = re.compile(r"[a-zA-Z][a-zA-Z+.#-]*")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def tokenize(text: str) -> Set[str]:
    return set(m.group(0).lower() for m in _word.finditer(text or ""))


def extract_skills(text: str) -> Set[str]:
    t = (text or "").lower()
    found: Set[str] = set()
    for skill in SKILLS:
        # Word-boundary match to avoid substrings; allow dots in tech names
        pattern = r"(?<![\w+.#-])" + re.escape(skill) + r"(?![\w+.#-])"
        if re.search(pattern, t):
            found.add(skill)
    return found


class ScoreEngine:
    def __init__(self, max_features: int = 5000):
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=max_features)
        self.alpha = 0.7  # weight for semantic similarity
        self.beta = 0.3   # weight for skill overlap

    def similarity(self, a: str, b: str) -> float:
        a = normalize(a)
        b = normalize(b)
        if not a or not b:
            return 0.0
        X = self.vectorizer.fit_transform([a, b])
        sim = cosine_similarity(X[0:1], X[1:2])[0, 0]
        if math.isnan(sim):
            return 0.0
        return float(sim)

    def skill_overlap(self, job_skills: Set[str], resume_skills: Set[str]) -> float:
        if not job_skills and not resume_skills:
            return 0.0
        if not job_skills:
            # Fallback: ratio of resume skills present in global lexicon
            return min(1.0, len(resume_skills) / max(1, len(SKILLS)))
        inter = job_skills & resume_skills
        return len(inter) / max(1, len(job_skills))

    def score(self, job_desc: str, resume_text: str, *, job_skills: Set[str] | None = None, resume_skills: Set[str] | None = None) -> dict:
        if job_skills is None:
            job_skills = extract_skills(job_desc)
        if resume_skills is None:
            resume_skills = extract_skills(resume_text)
        sim = self.similarity(job_desc, resume_text)
        overlap = self.skill_overlap(job_skills, resume_skills)
        total = (self.alpha * sim + self.beta * overlap) * 100.0  # percentage
        return {
            "similarity": round(sim, 4),
            "skill_overlap": round(overlap, 4),
            "total": round(total, 1),
        }
