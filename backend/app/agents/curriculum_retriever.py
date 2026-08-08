"""
Curriculum Retriever Agent.
Retrieves targeted curriculum day objectives, tools, and semantic context
from ChromaDB and CurriculumRepository for the selected interview topics.
"""

from typing import Dict, Any, List
from app.graph.state import InterviewState
from app.config import logger
from app.repositories.curriculum_repository import CurriculumRepository, get_curriculum_repository


class CurriculumRetriever:
    """
    Agent 2: Curriculum Retriever.
    Queries ChromaDB and CurriculumRepository to fetch technical objectives,
    tools, and reference material for planned interview questions.
    """

    def __init__(self, repository: CurriculumRepository = None):
        """Initialize Curriculum Retriever."""
        self.repository = repository or get_curriculum_repository()
        logger.info("CurriculumRetriever agent initialized")

    def retrieve_context(self, target_days: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve structured technical objectives and tools for each targeted day.

        Args:
            target_days (List[int]): List of curriculum day numbers.

        Returns:
            List[Dict[str, Any]]: Retrieved curriculum context items.
        """
        retrieved_items = []
        for day_num in target_days:
            day_spec = self.repository.get_day(day_num)
            if not day_spec:
                continue

            module_spec = self.repository.get_module_for_day(day_num)
            module_title = module_spec.title if module_spec else "General"
            module_n = module_spec.n if module_spec else 0

            retrieved_items.append({
                "day": day_spec.day,
                "title": day_spec.title,
                "module_n": module_n,
                "module_title": module_title,
                "type": day_spec.type,
                "tools": day_spec.tools,
                "objectives": day_spec.objectives
            })

        return retrieved_items

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for CurriculumRetriever.
        """
        target_days = state.get("target_days", [])
        if not target_days:
            target_days = [7, 12, 16, 22, 23, 28, 31, 10]

        context = self.retrieve_context(target_days)
        return {
            "retrieved_context": context
        }
