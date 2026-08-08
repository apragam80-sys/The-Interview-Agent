"""
LangGraph Multi-Agent Orchestration Package.
"""
from app.graph.state import InterviewState


def get_compiled_graph():
    from app.graph.workflow import get_compiled_graph as _get
    return _get()


def build_interview_graph():
    from app.graph.workflow import build_interview_graph as _build
    return _build()


__all__ = [
    "InterviewState",
    "build_interview_graph",
    "get_compiled_graph",
]

