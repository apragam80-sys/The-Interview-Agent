from typing import Dict, Any, List, Tuple
from app.config import MIN_QUESTIONS, MIN_CURRICULUM_DAYS
import logging

logger = logging.getLogger(__name__)


class InterviewPolicy:
    """
    Interview Policy Agent (Rule Engine):
    - Prevents duplicate questions / topics
    - Enforces curriculum coverage (minimum 4 days)
    - Enforces interview completion conditions (minimum 8 questions)
    - Decides next action: ADAPTIVE_FOLLOW_UP | NEXT_QUESTION | COMPLETE
    """
    @staticmethod
    def evaluate_next_step(
        total_questions_asked: int,
        covered_days: List[int],
        current_question_index: int,
        total_planned: int,
        last_evaluation: Optional[Dict[str, Any]],
        is_current_follow_up: bool
    ) -> str:
        unique_days_count = len(set(covered_days))
        
        # Check completion condition:
        # Must have asked at least 8 questions AND covered at least 4 unique days
        if total_questions_asked >= MIN_QUESTIONS and unique_days_count >= MIN_CURRICULUM_DAYS:
            # If current was already a follow-up or candidate gave a solid answer, complete!
            if is_current_follow_up or not (last_evaluation and last_evaluation.get("follow_up_needed", False)):
                return "COMPLETE"
            # If roadmap exhausted, complete
            if current_question_index >= total_planned:
                return "COMPLETE"

        # Check if adaptive follow-up is triggered (only if previous turn was NOT already a follow-up)
        if not is_current_follow_up and last_evaluation:
            score = last_evaluation.get("overall_score", 70)
            misconceptions = last_evaluation.get("misconceptions", [])
            follow_up_needed = last_evaluation.get("follow_up_needed", False)
            
            # Follow-up on ambiguous answer (35 - 65 score) or specific misconception
            if follow_up_needed or (35 <= score <= 65) or len(misconceptions) > 0:
                return "ADAPTIVE_FOLLOW_UP"

        # Otherwise, proceed to next planned curriculum question
        return "NEXT_QUESTION"

    @staticmethod
    def is_topic_already_covered(day: int, covered_days: List[int], max_per_day: int = 2) -> bool:
        """Prevents over-indexing on a single day."""
        return covered_days.count(day) >= max_per_day
