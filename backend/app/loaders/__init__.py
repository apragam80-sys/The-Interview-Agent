"""
Data loaders package for Curriculum and Candidate datasets.
"""

from app.loaders.curriculum_loader import CurriculumLoader
from app.loaders.candidate_loader import CandidateLoader

__all__ = ["CurriculumLoader", "CandidateLoader"]
