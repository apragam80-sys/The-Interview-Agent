"""
Session Repository.
Provides high-level abstraction over SQLite session persistence, turn history,
and state synchronization for the LangGraph orchestrator.
"""

from typing import List, Optional, Dict, Any
from app.models.schemas import SessionRecord, TurnRecord
from app.db.database import (
    save_session,
    get_session,
    list_sessions,
    delete_session,
    record_turn,
    get_session_turns,
    get_turn_count,
    get_last_turn
)
from app.config import logger


class SessionRepository:
    """
    Repository for managing interview session records and turn histories.
    """

    def save(
        self,
        session_id: str,
        candidate_id: str,
        candidate_name: str,
        job_role: str,
        status: str,
        difficulty_level: str,
        total_questions: int,
        covered_days: List[int],
        state_dict: Dict[str, Any]
    ) -> None:
        """
        Upsert an interview session state record.
        """
        save_session(
            session_id=session_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_role=job_role,
            status=status,
            difficulty_level=difficulty_level,
            total_questions=total_questions,
            covered_days=covered_days,
            state_dict=state_dict
        )

    def get(self, session_id: str) -> Optional[SessionRecord]:
        """
        Retrieve session record as a validated Pydantic model.

        Args:
            session_id (str): Session identifier.

        Returns:
            Optional[SessionRecord]: Validated session record or None.
        """
        raw = get_session(session_id)
        if not raw:
            return None
        return SessionRecord.model_validate(raw)

    def list_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List active and completed interview sessions."""
        return list_sessions(limit=limit)

    def delete(self, session_id: str) -> bool:
        """Delete session and associated turn history."""
        return delete_session(session_id)

    def add_turn(
        self,
        session_id: str,
        turn_index: int,
        question_text: str,
        curriculum_day: int,
        difficulty: str,
        is_follow_up: bool,
        candidate_answer: Optional[str] = None,
        evaluation_dict: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Record a turn into the session turn history.

        Returns:
            int: Inserted turn record ID.
        """
        return record_turn(
            session_id=session_id,
            turn_index=turn_index,
            question_text=question_text,
            curriculum_day=curriculum_day,
            difficulty=difficulty,
            is_follow_up=is_follow_up,
            candidate_answer=candidate_answer,
            evaluation_dict=evaluation_dict
        )

    def get_turns(self, session_id: str) -> List[TurnRecord]:
        """
        Retrieve ordered list of turns for a session.

        Returns:
            List[TurnRecord]: Sequence of turn history records.
        """
        raw_turns = get_session_turns(session_id)
        return [
            TurnRecord(
                id=t.get("id"),
                session_id=session_id,
                turn_index=t["turn_index"],
                question_text=t["question_text"],
                curriculum_day=t["curriculum_day"],
                difficulty=t["difficulty"],
                is_follow_up=t["is_follow_up"],
                candidate_answer=t.get("candidate_answer"),
                evaluation=t.get("evaluation", {}),
                created_at=t.get("created_at")
            )
            for t in raw_turns
        ]

    def get_turn_count(self, session_id: str) -> int:
        """Return total count of recorded turns."""
        return get_turn_count(session_id)

    def get_last_turn(self, session_id: str) -> Optional[TurnRecord]:
        """Retrieve most recent turn record."""
        raw = get_last_turn(session_id)
        if not raw:
            return None
        return TurnRecord(
            id=raw.get("id"),
            session_id=session_id,
            turn_index=raw["turn_index"],
            question_text=raw["question_text"],
            curriculum_day=raw["curriculum_day"],
            difficulty=raw["difficulty"],
            is_follow_up=raw["is_follow_up"],
            candidate_answer=raw.get("candidate_answer"),
            evaluation=raw.get("evaluation", {}),
            created_at=raw.get("created_at")
        )


_session_repo_instance: Optional[SessionRepository] = None


def get_session_repository() -> SessionRepository:
    """Dependency injection helper returning singleton SessionRepository."""
    global _session_repo_instance
    if _session_repo_instance is None:
        _session_repo_instance = SessionRepository()
    return _session_repo_instance
