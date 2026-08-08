"""
Memory Manager Agent.
Manages multi-turn conversation state, synchronizes turn history to SQLite,
and tracks completion metrics (total questions asked >= 8, covered days >= 4).
"""

from typing import Dict, Any, List
from app.graph.state import InterviewState
from app.config import logger
from app.repositories.session_repository import SessionRepository, get_session_repository


class MemoryManager:
    """
    Agent 7: Memory Manager.
    Records turns into persistent SQLite storage, updates conversation context,
    and increments interview progression indexes.
    """

    def __init__(self, session_repo: SessionRepository = None):
        """Initialize Memory Manager."""
        self.session_repo = session_repo or get_session_repository()
        logger.info("MemoryManager agent initialized")

    def sync_turn(
        self,
        session_id: str,
        turn_index: int,
        question_text: str,
        candidate_answer: str,
        curriculum_day: int,
        difficulty: str,
        is_follow_up: bool,
        evaluation_dict: Dict[str, Any]
    ) -> None:
        """
        Record the completed turn into SQLite.
        """
        try:
            self.session_repo.add_turn(
                session_id=session_id,
                turn_index=turn_index,
                question_text=question_text,
                curriculum_day=curriculum_day,
                difficulty=difficulty,
                is_follow_up=is_follow_up,
                candidate_answer=candidate_answer,
                evaluation_dict=evaluation_dict
            )
        except Exception as e:
            logger.error(f"Failed to record turn in SQLite: {e}")

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for MemoryManager.
        """
        session_id = state.get("session_id", "default_session")
        incoming_msg = state.get("incoming_message", "")
        last_question = state.get("latest_reply", "")
        history = list(state.get("conversation_history", []))
        
        current_q = state.get("current_question", {})
        day_num = current_q.get("day", 7)
        difficulty = state.get("difficulty_level", "MID")
        was_follow_up = state.get("is_follow_up", False) or state.get("was_follow_up", False)
        
        # Append candidate's message to conversation history
        if incoming_msg:
            history.append({
                "role": "candidate",
                "content": incoming_msg
            })

        turn_index = len(history)

        # Sync turn to database
        evaluations = state.get("evaluations", [])
        last_eval = evaluations[-1]["evaluation"] if evaluations else {}
        
        self.sync_turn(
            session_id=session_id,
            turn_index=turn_index,
            question_text=last_question,
            candidate_answer=incoming_msg,
            curriculum_day=day_num,
            difficulty=difficulty,
            is_follow_up=was_follow_up,
            evaluation_dict=last_eval
        )

        current_idx = state.get("current_question_index", 0)
        # Advance to next roadmap question if previous turn was a follow-up probe
        # (meaning the topic's probe has now been answered)
        new_q_idx = current_idx + 1 if was_follow_up else current_idx

        total_asked = state.get("total_questions_asked", 0)
        covered_days = list(state.get("covered_days", []))
        unique_days_count = len(set(covered_days))
        roadmap = state.get("planned_roadmap", [])

        # Strict completion criteria: >= 8 questions asked OR reached end of planned roadmap
        is_complete = (
            total_asked >= 8 or
            (roadmap and new_q_idx >= len(roadmap))
        )

        return {
            "conversation_history": history,
            "current_question_index": new_q_idx,
            "was_follow_up": was_follow_up,
            "is_complete": is_complete
        }
