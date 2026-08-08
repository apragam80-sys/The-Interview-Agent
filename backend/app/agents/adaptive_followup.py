"""
Adaptive Follow-up Agent.
Generates focused follow-up probe questions when a candidate gives a shallow,
incomplete, or ambiguous response, or to test edge cases.
"""

from typing import Dict, Any, Optional
from app.graph.state import InterviewState
from app.config import logger


class AdaptiveFollowUp:
    """
    Agent 6: Adaptive Follow-up.
    Synthesizes targeted follow-up probe questions to test depth and clarify misconceptions.
    """

    def __init__(self):
        """Initialize Adaptive Follow-up Agent."""
        logger.info("Initializing AdaptiveFollowUp agent template")

    def generate_probe(
        self,
        question_text: str,
        candidate_answer: str,
        evaluation_notes: str,
        curriculum_context: Dict[str, Any]
    ) -> str:
        """
        Synthesize a targeted follow-up probe question.

        Args:
            question_text (str): Previous question text.
            candidate_answer (str): Candidate's response.
            evaluation_notes (str): Identified gaps or unaddressed aspects.
            curriculum_context (Dict[str, Any]): Curriculum day objectives.

        Returns:
            str: Follow-up probe question string.
        """
        # TODO: Construct LLM prompt for adaptive follow-up probing:
        #       - Reference candidate's specific statement
        #       - Challenge an unaddressed trade-off, edge case, or failure mode
        #       - Maintain conversational professional tone
        return "Could you elaborate on how you would handle failure recovery and edge-case exceptions in that design?"

    def process(self, state: InterviewState) -> Dict[str, Any]:
        """
        Process function for LangGraph node execution.

        Args:
            state (InterviewState): Current interview state.

        Returns:
            Dict[str, Any]: State updates with latest_reply and total_questions_asked increment.
        """
        # TODO: Extract last question, answer, and latest evaluation notes
        # TODO: Call generate_probe() and update latest_reply in state
        current_question = state.get("current_question") or {}
        incoming_message = state.get("incoming_message", "")
        evaluations = state.get("evaluations", [])
        latest_eval = evaluations[-1] if evaluations else {}

        probe_text = self.generate_probe(
            question_text=current_question.get("topic", "Previous Question"),
            candidate_answer=incoming_message,
            evaluation_notes=latest_eval.get("notes", ""),
            curriculum_context=current_question
        )

        total_questions = state.get("total_questions_asked", 0) + 1
        history = list(state.get("conversation_history", []))
        history.append({
            "role": "assistant",
            "content": probe_text
        })

        return {
            "latest_reply": probe_text,
            "total_questions_asked": total_questions,
            "is_follow_up": False,  # Reset follow-up flag after generating probe
            "conversation_history": history,
        }
