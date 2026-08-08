"""
LangGraph State Schema Definition for Adaptive AI Technical Interview.
Defines the shared state dictionary passed across all nodes in the state machine.
"""

from typing import TypedDict, Optional, List, Dict, Any


class InterviewState(TypedDict, total=False):
    """
    TypedDict representing the complete interview execution state in LangGraph.
    
    Fields:
        session_id (str): Unique session identifier.
        candidate_profile (Optional[Dict[str, Any]]): Ingested candidate profile from request.
        difficulty_level (str): Computed difficulty level ('JUNIOR', 'MID', 'SENIOR', 'PRINCIPAL').
        target_days (List[int]): Identified curriculum days targeted for testing.
        planned_roadmap (List[Dict[str, Any]]): Structured list of planned questions (min 8).
        current_question_index (int): Pointer to the current planned question index.
        current_question (Optional[Dict[str, Any]]): Active question metadata dictionary.
        is_follow_up (bool): True if next turn should be an adaptive probe.
        was_follow_up (bool): True if the turn just evaluated was an adaptive probe.
        follow_up_count_for_current_q (int): Number of follow-ups executed for active question.
        conversation_history (List[Dict[str, Any]]): List of conversation messages.
        evaluations (List[Dict[str, Any]]): List of evaluation objects for answers.
        latest_score (Optional[int]): Score of the most recently evaluated answer (0-100).
        average_score (Optional[int]): Running mean score across all turns (0-100).
        covered_days (List[int]): List of unique curriculum day integers tested.
        total_questions_asked (int): Cumulative counter of questions asked.
        is_complete (bool): True when interview criteria (>=8 Qs, >=4 Days) are fulfilled.
        final_feedback (Optional[Dict[str, Any]]): Structured feedback payload.
        latest_reply (str): String response to return in the HTTP payload.
        incoming_message (Optional[str]): Latest candidate answer received in request.
        candidate_signals (Optional[Dict[str, Any]]): Extracted signals and weak spots.
        retrieved_context (Optional[List[Dict[str, Any]]]): RAG context retrieved from ChromaDB.
    """
    session_id: str
    candidate_profile: Optional[Dict[str, Any]]
    difficulty_level: str
    target_days: List[int]
    planned_roadmap: List[Dict[str, Any]]
    current_question_index: int
    current_question: Optional[Dict[str, Any]]
    is_follow_up: bool
    was_follow_up: bool
    follow_up_count_for_current_q: int
    conversation_history: List[Dict[str, Any]]
    evaluations: List[Dict[str, Any]]
    latest_score: Optional[int]
    average_score: Optional[int]
    covered_days: List[int]
    total_questions_asked: int
    is_complete: bool
    is_abusive: bool
    final_feedback: Optional[Dict[str, Any]]
    latest_reply: str
    incoming_message: Optional[str]
    candidate_signals: Optional[Dict[str, Any]]
    retrieved_context: Optional[List[Dict[str, Any]]]
