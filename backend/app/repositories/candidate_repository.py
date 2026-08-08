"""
Candidate Repository.
Provides clean query interfaces for candidate profiles, cohort benchmark records,
struggled missions, skipped objectives, and commitment signals.
"""

from typing import List, Optional, Dict, Any
from app.models.schemas import CandidateProfile, CandidateMission, CandidateSignals
from app.loaders.candidate_loader import CandidateLoader
from app.config import logger


class CandidateRepository:
    """
    Repository for accessing candidate profiles and historical performance signals.
    """

    def __init__(self, loader: Optional[CandidateLoader] = None):
        """Initialize candidate repository."""
        self.loader = loader or CandidateLoader()

    def get_candidate(self, candidate_id: str) -> Optional[CandidateProfile]:
        """
        Retrieve candidate by ID (e.g. CAND-001).

        Args:
            candidate_id (str): Unique candidate identifier.

        Returns:
            Optional[CandidateProfile]: Candidate profile if found.
        """
        return self.loader.get_candidate_by_id(candidate_id)

    def get_candidate_by_name(self, name: str) -> Optional[CandidateProfile]:
        """
        Retrieve candidate by full or partial name.

        Args:
            name (str): Candidate name.

        Returns:
            Optional[CandidateProfile]: Candidate profile if found.
        """
        return self.loader.get_candidate_by_name(name)

    def get_all_candidates(self) -> List[CandidateProfile]:
        """Return all parsed candidate profiles."""
        return self.loader.get_all_candidates()

    def list_candidate_summaries(self) -> List[Dict[str, Any]]:
        """
        Return high-level summary cards for all candidates.

        Returns:
            List[Dict[str, Any]]: Summary metadata for candidate selector UI.
        """
        candidates = self.get_all_candidates()
        summaries = []
        for c in candidates:
            summaries.append({
                "id": c.member.id,
                "name": c.member.name,
                "jobRole": c.member.jobRole,
                "yearsExperience": c.member.yearsExperience,
                "education": c.member.education,
                "commitDays": c.signals.commitDays,
                "missionsCompleted": c.signals.missionsCompleted,
                "missionsFirstTry": c.signals.missionsFirstTry
            })
        return summaries

    def get_learning_analytics(self, candidate_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed learning analytics for a candidate.

        Args:
            candidate_id (str): Candidate ID.

        Returns:
            Dict[str, Any]: Analytics dictionary.
        """
        return self.loader.calculate_candidate_stats(candidate_id)

    def get_target_probe_days(self, candidate_id: str) -> List[int]:
        """
        Identify candidate-specific priority curriculum days for interview probing.
        Prioritizes:
        1. Days where missions required multiple attempts (>= 2 attempts)
        2. Days where missions were skipped
        3. Core capstone/advanced days (e.g. Day 22 Multi-Agent, Day 23 MCP, Day 31 Capstone)

        Args:
            candidate_id (str): Candidate ID.

        Returns:
            List[int]: Recommended day numbers to probe.
        """
        stats = self.get_learning_analytics(candidate_id)
        if not stats:
            return [7, 12, 22, 31]

        probe_days = []
        # Multi-attempt struggled days
        for day in stats.get("struggledDays", []):
            if day not in probe_days:
                probe_days.append(day)

        # Skipped days
        for day in stats.get("skippedDays", []):
            if day not in probe_days:
                probe_days.append(day)

        # Ensure at least 4 days are available
        default_anchor_days = [7, 12, 16, 22, 23, 28, 31]
        for anchor in default_anchor_days:
            if anchor not in probe_days:
                probe_days.append(anchor)

        return probe_days[:8]


_candidate_repo_instance: Optional[CandidateRepository] = None


def get_candidate_repository() -> CandidateRepository:
    """Dependency injection helper returning singleton CandidateRepository."""
    global _candidate_repo_instance
    if _candidate_repo_instance is None:
        _candidate_repo_instance = CandidateRepository()
    return _candidate_repo_instance
