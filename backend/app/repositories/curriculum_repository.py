"""
Curriculum Repository.
Combines static structured curriculum metadata with ChromaDB vector search to provide
a unified data access layer for interview planning, question generation, and evaluation.
"""

from typing import List, Optional, Dict, Any
from app.models.schemas import CurriculumDay, CurriculumModule, CurriculumSchema
from app.loaders.curriculum_loader import CurriculumLoader
from app.services.chroma_service import ChromaService, get_chroma_service
from app.config import logger


class CurriculumRepository:
    """
    Repository for querying curriculum modules, day objectives, tools,
    and performing semantic retrieval over curriculum knowledge chunks.
    """

    def __init__(
        self,
        loader: Optional[CurriculumLoader] = None,
        chroma_service: Optional[ChromaService] = None
    ):
        """
        Initialize Curriculum Repository with loader and vector service.
        """
        self.loader = loader or CurriculumLoader()
        self.chroma_service = chroma_service or get_chroma_service()

    def get_curriculum(self) -> CurriculumSchema:
        """Return the full validated curriculum schema."""
        return self.loader.get_curriculum()

    def get_all_days(self) -> List[CurriculumDay]:
        """Return all 31 curriculum days."""
        return self.loader.get_all_days()

    def get_day(self, day_number: int) -> Optional[CurriculumDay]:
        """Return structured day specification for a given day."""
        return self.loader.get_day(day_number)

    def get_all_modules(self) -> List[CurriculumModule]:
        """Return all 8 curriculum modules."""
        return self.loader.get_all_modules()

    def get_module(self, module_number: int) -> Optional[CurriculumModule]:
        """Return module specification by module number (1-8)."""
        return self.loader.get_module(module_number)

    def get_module_for_day(self, day_number: int) -> Optional[CurriculumModule]:
        """Return the parent module specification for a given day."""
        return self.loader.get_module_for_day(day_number)

    def get_tools_for_day(self, day_number: int) -> List[str]:
        """Return list of technologies and tools taught on a day."""
        return self.loader.get_tools_for_day(day_number)

    def get_objectives_for_day(self, day_number: int) -> List[str]:
        """Return key learning objectives for a day."""
        return self.loader.get_objectives_for_day(day_number)

    def search_curriculum(
        self,
        query: str,
        k: int = 4,
        filter_day: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search over curriculum knowledge base.

        Args:
            query (str): Technical query or candidate answer.
            k (int): Number of nearest neighbors to retrieve.
            filter_day (Optional[int]): Restrict search to a specific day.

        Returns:
            List[Dict[str, Any]]: Ranked list of matching curriculum chunks.
        """
        filter_dict = {"day": filter_day} if filter_day else None
        return self.chroma_service.similarity_search(query=query, k=k, filter_dict=filter_dict)

    def get_context_for_days(self, days: List[int]) -> str:
        """
        Build a consolidated markdown context block describing the selected curriculum days.

        Args:
            days (List[int]): List of day numbers.

        Returns:
            str: Markdown formatted context string.
        """
        context_blocks = []
        for d_num in sorted(set(days)):
            day = self.get_day(d_num)
            if day:
                module = self.get_module_for_day(d_num)
                module_title = module.title if module else "General"
                tools_str = ", ".join(day.tools) if day.tools else "None"
                objs = "\n".join([f"  - {obj}" for obj in day.objectives])
                context_blocks.append(
                    f"### Day {day.day}: {day.title} (Module: {module_title})\n"
                    f"- **Type**: {day.type}\n"
                    f"- **Tools**: {tools_str}\n"
                    f"- **Objectives**:\n{objs}"
                )
        return "\n\n".join(context_blocks)


_curriculum_repo_instance: Optional[CurriculumRepository] = None


def get_curriculum_repository() -> CurriculumRepository:
    """Dependency injection helper returning singleton CurriculumRepository."""
    global _curriculum_repo_instance
    if _curriculum_repo_instance is None:
        _curriculum_repo_instance = CurriculumRepository()
    return _curriculum_repo_instance
