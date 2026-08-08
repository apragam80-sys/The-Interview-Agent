"""
LangGraph Multi-Agent Orchestration StateMachine for Adaptive AI Interview Platform.
Assembles the 8 specialized agents into a deterministic, stateful execution graph.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from app.graph.state import InterviewState
from app.config import logger

# Import agent classes
from app.agents.candidate_analyzer import CandidateAnalyzer
from app.agents.curriculum_retriever import CurriculumRetriever
from app.agents.interview_planner import InterviewPlanner
from app.agents.memory_manager import MemoryManager
from app.agents.answer_evaluator import AnswerEvaluator
from app.agents.adaptive_follow_up import AdaptiveFollowUp
from app.agents.question_generator import QuestionGenerator
from app.agents.feedback_generator import FeedbackGenerator

# Singleton agent instances
_candidate_analyzer = CandidateAnalyzer()
_curriculum_retriever = CurriculumRetriever()
_interview_planner = InterviewPlanner()
_memory_manager = MemoryManager()
_answer_evaluator = AnswerEvaluator()
_adaptive_followup = AdaptiveFollowUp()
_question_generator = QuestionGenerator()
_feedback_generator = FeedbackGenerator()


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------
def session_router_node(state: InterviewState) -> Dict[str, Any]:
    """
    Entry Router Node: Evaluates whether incoming request is Turn 1 (init) or Turn N (message).
    """
    logger.info(f"Executing Session Router Node for session: {state.get('session_id')}")
    return {}


def candidate_analyzer_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 1: Candidate Analyzer Agent.
    Ingests candidate profile, extracts signals, and computes baseline difficulty.
    """
    logger.info("Executing Candidate Analyzer Node")
    return _candidate_analyzer(state)


def curriculum_retriever_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 2: Curriculum Retriever Agent (RAG).
    Queries ChromaDB and curriculum JSON for targeted day objectives and tools.
    """
    logger.info("Executing Curriculum Retriever Node")
    return _curriculum_retriever(state)


def interview_planner_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 3: Interview Planner Agent.
    Generates a structured roadmap guaranteeing >=8 questions and >=4 curriculum days.
    """
    logger.info("Executing Interview Planner Node")
    return _interview_planner(state)


def memory_manager_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 4: Memory Manager Agent.
    Synchronizes conversation history, turn sequence, and SQLite persistence.
    """
    logger.info("Executing Memory Manager Node")
    return _memory_manager(state)


def answer_evaluator_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 5: Answer Evaluator Agent.
    Evaluates candidate responses across the 6 core rubrics.
    """
    logger.info("Executing Answer Evaluator Node")
    return _answer_evaluator(state)


def adaptive_followup_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 6: Adaptive Follow-up Agent.
    Generates dynamic follow-up probes for ambiguous or shallow responses.
    """
    logger.info("Executing Adaptive Follow-up Node")
    return _adaptive_followup(state)


def question_generator_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 7: Question Generator Agent.
    Synthesizes technical questions grounded in curriculum objectives.
    """
    logger.info("Executing Question Generator Node")
    return _question_generator(state)


def feedback_generator_node(state: InterviewState) -> Dict[str, Any]:
    """
    Node 8: Feedback Generator Agent.
    Synthesizes full session performance into the strict JSON schema.
    """
    logger.info("Executing Feedback Generator Node")
    return _feedback_generator(state)


# ---------------------------------------------------------------------------
# Conditional Edge Routers
# ---------------------------------------------------------------------------
def route_session_type(state: InterviewState) -> Literal["candidate_analyzer", "memory_manager"]:
    """
    Route Turn 1 requests with candidate profile to candidate_analyzer,
    and Turn N requests with candidate message to memory_manager.
    """
    if state.get("candidate_profile"):
        return "candidate_analyzer"
    return "memory_manager"


def route_turn_action(state: InterviewState) -> Literal["adaptive_followup", "question_generator", "feedback_generator"]:
    """
    Conditional routing logic evaluating completion criteria and follow-up conditions.

    Criteria:
        - If is_complete (total_questions_asked >= 8 and len(covered_days) >= 4 and not is_follow_up) -> 'feedback_generator'
        - If follow-up probe is warranted (and not abusive) -> 'adaptive_followup'
        - Otherwise -> 'question_generator'
    """
    total_q = state.get("total_questions_asked", 0)
    covered_days = set(state.get("covered_days", []))
    is_follow_up = state.get("is_follow_up", False)
    is_complete = state.get("is_complete", False)
    roadmap = state.get("planned_roadmap", [])
    q_idx = state.get("current_question_index", 0)

    # Enforce strict completion criteria (hard cap at 8 questions or end of roadmap)
    if is_complete or total_q >= 8 or (roadmap and q_idx >= len(roadmap)):
        return "feedback_generator"
    
    if is_follow_up and not state.get("is_abusive", False):
        return "adaptive_followup"
        
    return "question_generator"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------
def build_interview_graph() -> StateGraph:
    """
    Construct the LangGraph StateGraph connecting all 8 agent nodes and conditional edges.

    Returns:
        StateGraph: Configured StateGraph instance.
    """
    graph = StateGraph(InterviewState)

    # Register Nodes
    graph.add_node("session_router", session_router_node)
    graph.add_node("candidate_analyzer", candidate_analyzer_node)
    graph.add_node("curriculum_retriever", curriculum_retriever_node)
    graph.add_node("interview_planner", interview_planner_node)
    graph.add_node("memory_manager", memory_manager_node)
    graph.add_node("answer_evaluator", answer_evaluator_node)
    graph.add_node("adaptive_followup", adaptive_followup_node)
    graph.add_node("question_generator", question_generator_node)
    graph.add_node("feedback_generator", feedback_generator_node)

    # Entry point edge from START to session_router
    graph.add_edge(START, "session_router")
    graph.add_conditional_edges(
        "session_router",
        route_session_type,
        {
            "candidate_analyzer": "candidate_analyzer",
            "memory_manager": "memory_manager"
        }
    )

    # Phase 1: Initialization Turn
    graph.add_edge("candidate_analyzer", "curriculum_retriever")
    graph.add_edge("curriculum_retriever", "interview_planner")
    graph.add_edge("interview_planner", "question_generator")
    graph.add_edge("question_generator", END)

    # Phase 2: Conversation Turn Loop
    graph.add_edge("memory_manager", "answer_evaluator")
    graph.add_conditional_edges(
        "answer_evaluator",
        route_turn_action,
        {
            "adaptive_followup": "adaptive_followup",
            "question_generator": "question_generator",
            "feedback_generator": "feedback_generator"
        }
    )
    graph.add_edge("adaptive_followup", END)
    graph.add_edge("feedback_generator", END)

    return graph


_compiled_graph = None


def get_compiled_graph():
    """
    Compile and return the executable LangGraph runnable.
    """
    global _compiled_graph
    if _compiled_graph is None:
        builder = build_interview_graph()
        _compiled_graph = builder.compile()
    return _compiled_graph
