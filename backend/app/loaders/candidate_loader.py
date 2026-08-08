"""
Candidate Loader and Parser.
Loads and validates candidates.json, providing query methods for profiles,
missions, attempts, skipped tasks, and commitment learning signals.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import CANDIDATES_PATH, logger
from app.models.schemas import (
    CandidateCollection,
    CandidateProfile,
    CandidateMission,
    CandidateSignals,
    CandidateMember
)


class CandidateLoader:
    """
    Service for loading, validating, and querying candidate profiles and signals.
    """

    def __init__(self, file_path: Optional[Path] = None):
        """
        Initialize candidate loader with path to candidates.json.

        Args:
            file_path (Optional[Path]): Override path for candidates.json.
        """
        self.file_path = Path(file_path) if file_path else CANDIDATES_PATH
        self._collection: Optional[CandidateCollection] = None
        self._candidate_map: Dict[str, CandidateProfile] = {}
        self._name_map: Dict[str, CandidateProfile] = {}
        self.load()

    def load(self) -> CandidateCollection:
        """
        Load, parse, and validate candidates.json using Pydantic.

        Returns:
            CandidateCollection: Validated candidate dataset container.

        Raises:
            FileNotFoundError: If candidates.json is missing.
            ValueError: If JSON schema validation fails.
        """
        if not self.file_path.exists():
            error_msg = f"Candidates file not found at: {self.file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            self._collection = CandidateCollection.model_validate(raw_data)
            
            # Build fast lookup indexes
            self._candidate_map = {c.member.id: c for c in self._collection.candidates}
            self._name_map = {c.member.name.lower(): c for c in self._collection.candidates}

            logger.info(f"Candidates loaded successfully: {len(self._collection.candidates)} profiles.")
            return self._collection

        except Exception as e:
            logger.error(f"Failed to load/validate candidates from {self.file_path}: {e}")
            raise ValueError(f"Candidate validation error: {e}") from e

    def get_all_candidates(self) -> List[CandidateProfile]:
        """Return all parsed candidate profiles."""
        if self._collection is None:
            self.load()
        return self._collection.candidates

    def get_candidate_by_id(self, candidate_id: str) -> Optional[CandidateProfile]:
        """
        Retrieve candidate profile by ID (e.g. CAND-001).

        Args:
            candidate_id (str): Candidate identifier.

        Returns:
            Optional[CandidateProfile]: Candidate profile if found.
        """
        if not self._candidate_map:
            self.load()
        return self._candidate_map.get(candidate_id)

    def get_candidate_by_name(self, name: str) -> Optional[CandidateProfile]:
        """
        Retrieve candidate profile by case-insensitive name.

        Args:
            name (str): Full or partial candidate name.

        Returns:
            Optional[CandidateProfile]: Candidate profile if found.
        """
        if not self._name_map:
            self.load()
        return self._name_map.get(name.strip().lower())

    def get_passed_missions(self, candidate_id: str) -> List[CandidateMission]:
        """Return list of missions marked as passed for a candidate."""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            return []
        return [m for m in candidate.missions if m.passed is True]

    def get_skipped_missions(self, candidate_id: str) -> List[CandidateMission]:
        """Return list of missions skipped by a candidate."""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            return []
        return [m for m in candidate.missions if m.skipped is True]

    def get_multi_attempt_missions(self, candidate_id: str, min_attempts: int = 2) -> List[CandidateMission]:
        """
        Return missions requiring multiple attempts (indicating initial struggle / perseverance).

        Args:
            candidate_id (str): Candidate ID.
            min_attempts (int): Threshold for attempts (default 2).

        Returns:
            List[CandidateMission]: List of challenging missions for candidate.
        """
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            return []
        return [m for m in candidate.missions if (m.attempts or 1) >= min_attempts]

    def get_signals(self, candidate_id: str) -> Optional[CandidateSignals]:
        """Retrieve commitment and performance signals for a candidate."""
        candidate = self.get_candidate_by_id(candidate_id)
        return candidate.signals if candidate else None

    def calculate_candidate_stats(self, candidate_id: str) -> Dict[str, Any]:
        """
        Compute rich analytical statistics for a candidate's background and learning record.

        Args:
            candidate_id (str): Candidate ID.

        Returns:
            Dict[str, Any]: Aggregated stats for candidate analyzer and interview planning.
        """
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            return {}

        total_missions = len(candidate.missions)
        passed_missions = self.get_passed_missions(candidate_id)
        skipped_missions = self.get_skipped_missions(candidate_id)
        multi_attempt = self.get_multi_attempt_missions(candidate_id, min_attempts=2)

        first_try_rate = (
            (candidate.signals.missionsFirstTry / candidate.signals.missionsCompleted * 100)
            if candidate.signals.missionsCompleted > 0 else 0.0
        )

        struggled_days = [m.day for m in multi_attempt]
        skipped_days = [m.day for m in skipped_missions]

        return {
            "id": candidate.member.id,
            "name": candidate.member.name,
            "jobRole": candidate.member.jobRole,
            "yearsExperience": candidate.member.yearsExperience,
            "education": candidate.member.education,
            "commitDays": candidate.signals.commitDays,
            "missionsCompleted": candidate.signals.missionsCompleted,
            "missionsFirstTry": candidate.signals.missionsFirstTry,
            "firstTrySuccessRate": round(first_try_rate, 1),
            "struggledDays": struggled_days,
            "skippedDays": skipped_days,
            "totalMissionsRecorded": total_missions,
            "passedMissionsCount": len(passed_missions),
            "skippedMissionsCount": len(skipped_missions)
        }
