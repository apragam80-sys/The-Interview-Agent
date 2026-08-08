"""
Repository layer package providing unified data access interfaces for:
- Curriculum (Static JSON + ChromaDB Vector Store)
- Candidates (Benchmark profiles and learning signals)
- Sessions (SQLite persistence and turn history)
"""

from app.repositories.curriculum_repository import CurriculumRepository, get_curriculum_repository
from app.repositories.candidate_repository import CandidateRepository, get_candidate_repository
from app.repositories.session_repository import SessionRepository, get_session_repository

__all__ = [
    "CurriculumRepository",
    "get_curriculum_repository",
    "CandidateRepository",
    "get_candidate_repository",
    "SessionRepository",
    "get_session_repository"
]
