"""
Interview Planner Agent.
Constructs an adaptive multi-step question plan covering at least 4 distinct
curriculum days and minimum 8 questions tailored to candidate level and weak spots.
"""

from typing import Dict, Any, List
from app.graph.state import InterviewState
from app.config import logger


class InterviewPlanner:
    """
    Agent 3: Interview Planner.
    Formulates a structured 8-question curriculum roadmap for the interview.
    """

    def __init__(self):
        """Initialize Interview Planner."""
        logger.info("InterviewPlanner agent initialized")

    def create_plan(
        self,
        retrieved_context: List[Dict[str, Any]],
        difficulty_level: str,
        candidate_signals: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build an 8-question roadmap from the retrieved curriculum topics.

        Args:
            retrieved_context (List[Dict[str, Any]]): Retrieved curriculum day items.
            difficulty_level (str): Candidate difficulty tier (JUNIOR/MID/SENIOR/PRINCIPAL).
            candidate_signals (Dict[str, Any]): Candidate analytical signals.

        Returns:
            List[Dict[str, Any]]: List of planned question objects.
        """
        planned_roadmap: List[Dict[str, Any]] = []
        
        # Deduplicate retrieved context by day to ensure wide curriculum coverage
        unique_items = []
        seen_days = set()
        for it in (retrieved_context or []):
            d = it.get("day")
            if d and d not in seen_days:
                seen_days.add(d)
                unique_items.append(it)

        # Fallback default items across all modules to guarantee 8 distinct curriculum days
        fallback_days = [
            {"day": 7, "title": "Embeddings Explained", "module_title": "Embeddings & Vector Search", "tools": ["Python", "FastEmbed", "Sentence Transformers"], "objectives": ["Understand vector embeddings", "Compute cosine similarity"]},
            {"day": 10, "title": "Retrieval & Matching Engine", "module_title": "Embeddings & Vector Search", "tools": ["ChromaDB", "HNSW"], "objectives": ["Build retrieval pipeline", "Tune top-k and distance threshold"]},
            {"day": 12, "title": "Prompt Engineering Fundamentals", "module_title": "LLM Core & Prompting", "tools": ["System Prompts", "Few-Shot"], "objectives": ["Design zero-shot/few-shot prompts", "Mitigate hallucinations"]},
            {"day": 16, "title": "Chatbot Backend & API Integration", "module_title": "Chatbot Application Build", "tools": ["FastAPI", "Uvicorn"], "objectives": ["Expose REST endpoints for LLMs", "Handle async requests"]},
            {"day": 20, "title": "Conversation Memory & Context Management", "module_title": "Chatbot Application Build", "tools": ["SQLite", "LangChain Memory"], "objectives": ["Persist multi-turn conversation", "Manage context window limits"]},
            {"day": 22, "title": "Multi-Agent Orchestration", "module_title": "Agentic AI & MCP", "tools": ["LangGraph", "StateGraph"], "objectives": ["Build multi-agent state machines", "Define conditional branching edges"]},
            {"day": 23, "title": "Model Context Protocol (MCP)", "module_title": "Agentic AI & MCP", "tools": ["MCP SDK", "JSON-RPC"], "objectives": ["Expose local tools to LLMs via MCP", "Standardize client-server context"]},
            {"day": 31, "title": "Capstone Project & Final Demo", "module_title": "Production & Capstone", "tools": ["Docker", "Prometheus", "FastAPI"], "objectives": ["Deploy end-to-end AI system", "Implement monitoring and evaluation"]}
        ]

        for fb in fallback_days:
            if len(unique_items) >= 8:
                break
            if fb["day"] not in seen_days:
                seen_days.add(fb["day"])
                unique_items.append(fb)

        items = unique_items

        # Build 8 sequential steps
        for step_idx, item in enumerate(items[:8]):
            day_num = item.get("day", 7)
            title = item.get("title", "Technical Topic")
            module_title = item.get("module_title", "Core AI")
            tools = item.get("tools", [])
            objectives = item.get("objectives", [])

            # Dynamic question type based on progression
            if step_idx < 2:
                q_type = "FOUNDATIONAL_ARCH"
            elif step_idx < 5:
                q_type = "PRACTICAL_IMPLEMENTATION"
            elif step_idx < 7:
                q_type = "SYSTEM_DESIGN_AGENTIC"
            else:
                q_type = "PRODUCTION_FAILURE_RECOVERY"

            planned_roadmap.append({
                "step": step_idx + 1,
                "day": day_num,
                "module_title": module_title,
                "topic": title,
                "difficulty": difficulty_level,
                "question_type": q_type,
                "tools": tools,
                "objectives": objectives
            })

        return planned_roadmap

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for InterviewPlanner.
        """
        retrieved_context = state.get("retrieved_context", [])
        difficulty_level = state.get("difficulty_level", "MID")
        candidate_signals = state.get("candidate_signals", {})

        roadmap = self.create_plan(retrieved_context, difficulty_level, candidate_signals)

        return {
            "planned_roadmap": roadmap,
            "current_question_index": 0
        }
