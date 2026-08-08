from typing import Dict, Any, List, Optional
from app.db.database import save_session, get_session, record_turn
import logging

logger = logging.getLogger(__name__)


class InterviewStateManager:
    """
    Interview State Manager Agent:
    Maintains session state, covered curriculum days, roadmap progression,
    score history, and synchronizes persistence in SQLite.
    """
    @staticmethod
    def load_or_init_state(session_id: str, candidate_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Loads state from SQLite or initializes a new session state."""
        existing_session = get_session(session_id)
        if existing_session and "state" in existing_session:
            return existing_session["state"]
        
        # New State initialization
        return {
            "session_id": session_id,
            "candidate_profile": candidate_profile or {},
            "difficulty_level": "Mid",
            "weak_topics": [],
            "strong_topics": [],
            "target_days": [],
            "planned_roadmap": [],
            "current_question_index": 0,
            "current_question": None,
            "is_follow_up": False,
            "conversation_history": [],
            "evaluations": [],
            "covered_days": [],
            "total_questions_asked": 0,
            "is_complete": False,
            "final_feedback": None,
            "latest_reply": ""
        }

    @staticmethod
    def persist_state(state: Dict[str, Any]):
        """Persists state back to SQLite database."""
        session_id = state.get("session_id", "")
        candidate = state.get("candidate_profile", {})
        member = candidate.get("member", {})
        
        candidate_id = member.get("id", "UNKNOWN")
        candidate_name = member.get("name", "Unknown Candidate")
        job_role = member.get("jobRole", "Developer")
        status = "COMPLETED" if state.get("is_complete", False) else "IN_PROGRESS"
        difficulty = state.get("difficulty_level", "Mid")
        total_questions = state.get("total_questions_asked", 0)
        covered_days = state.get("covered_days", [])

        save_session(
            session_id=session_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_role=job_role,
            status=status,
            difficulty_level=difficulty,
            total_questions=total_questions,
            covered_days=covered_days,
            state_dict=state
        )

    @staticmethod
    def record_turn_history(
        session_id: str,
        turn_index: int,
        question_text: str,
        curriculum_day: int,
        difficulty: str,
        is_follow_up: bool,
        candidate_answer: Optional[str],
        evaluation_dict: Optional[Dict[str, Any]]
    ):
        """Records a single conversation turn in SQLite."""
        record_turn(
            session_id=session_id,
            turn_index=turn_index,
            question_text=question_text,
            curriculum_day=curriculum_day,
            difficulty=difficulty,
            is_follow_up=is_follow_up,
            candidate_answer=candidate_answer,
            evaluation_dict=evaluation_dict
        )
