"""
Candidate Analyzer Agent.
Analyzes candidate profile from candidates.json, extracts learning signals,
skipped missions, and high-attempt missions, and computes baseline difficulty level.
"""

from typing import Dict, Any, List
from app.graph.state import InterviewState
from app.config import logger
from app.loaders.candidate_loader import CandidateLoader


class CandidateAnalyzer:
    """
    Agent 1: Candidate Analyzer.
    Ingests candidate profile metadata and signals to identify strengths,
    target gaps, and baseline difficulty tier.
    """

    def __init__(self, loader: CandidateLoader = None):
        """Initialize Candidate Analyzer."""
        self.loader = loader or CandidateLoader()
        logger.info("CandidateAnalyzer agent initialized")

    def analyze_profile(self, candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze candidate profile metadata, missions, and signals.

        Args:
            candidate_profile (Dict[str, Any]): Raw candidate profile dictionary.

        Returns:
            Dict[str, Any]: Analysis summary with difficulty_level, target_days, and signals.
        """
        member = candidate_profile.get("member", {})
        missions = candidate_profile.get("missions", [])
        signals = candidate_profile.get("signals", {})

        years_exp = member.get("yearsExperience", 3)
        job_role = member.get("jobRole", "Software Engineer")
        commit_days = signals.get("commitDays", 20)
        completed = signals.get("missionsCompleted", 25)
        first_try = signals.get("missionsFirstTry", 15)

        # 1. Identify struggle days and skipped days
        struggled_days: List[int] = []
        skipped_days: List[int] = []
        passed_days: List[int] = []

        for m in missions:
            day_num = m.get("day")
            if not day_num:
                continue
            if m.get("skipped"):
                skipped_days.append(day_num)
            elif m.get("passed"):
                passed_days.append(day_num)
                if m.get("attempts", 1) >= 2:
                    struggled_days.append(day_num)

        # 2. Compute baseline difficulty level
        if years_exp >= 8 or (commit_days >= 28 and first_try >= 20):
            difficulty_level = "SENIOR"
        elif years_exp >= 4 or (commit_days >= 20 and first_try >= 12):
            difficulty_level = "MID"
        else:
            difficulty_level = "JUNIOR"

        # Special role boost
        if "lead" in job_role.lower() or "principal" in job_role.lower() or years_exp >= 10:
            difficulty_level = "PRINCIPAL"

        # 3. Formulate priority target curriculum days (ensuring at least 4 unique days across 4 modules)
        target_days: List[int] = []

        # First add struggled days (to probe for mastery improvement)
        for d in struggled_days:
            if d not in target_days:
                target_days.append(d)

        # Then add skipped days (to test foundational knowledge)
        for d in skipped_days:
            if d not in target_days:
                target_days.append(d)

        # Anchor essential milestone days across modules:
        # Mod 3 (Vector/Embeddings): Day 7, 8, 10
        # Mod 4 (LLM/Prompting): Day 12, 13
        # Mod 5 (Chatbot/Backend): Day 16, 18, 20
        # Mod 6 (Agentic AI/MCP): Day 22, 23
        # Mod 7 (Security/Deployment): Day 28
        # Mod 8 (Capstone): Day 31
        anchor_days = [7, 12, 16, 22, 23, 28, 31]
        for d in anchor_days:
            if d not in target_days:
                target_days.append(d)

        # Ensure we have at least 8 target days for an 8-question interview
        target_days = target_days[:8]

        extracted_signals = {
            "candidate_id": member.get("id", "UNKNOWN"),
            "candidate_name": member.get("name", "Candidate"),
            "job_role": job_role,
            "years_experience": years_exp,
            "education": member.get("education", "CS"),
            "commit_days": commit_days,
            "missions_completed": completed,
            "missions_first_try": first_try,
            "struggled_days": struggled_days,
            "skipped_days": skipped_days,
            "passed_days": passed_days
        }

        return {
            "difficulty_level": difficulty_level,
            "target_days": target_days,
            "candidate_signals": extracted_signals
        }

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for CandidateAnalyzer.
        """
        candidate_profile = state.get("candidate_profile", {})
        analysis = self.analyze_profile(candidate_profile)

        return {
            "difficulty_level": analysis["difficulty_level"],
            "target_days": analysis["target_days"],
            "candidate_signals": analysis["candidate_signals"]
        }
