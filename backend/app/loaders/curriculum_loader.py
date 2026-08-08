"""
Curriculum Loader and Parser.
Loads and validates curriculum.json, providing clean query methods for modules,
days, objectives, tools, and vector chunk preparation.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import CURRICULUM_PATH, logger
from app.models.schemas import (
    CurriculumSchema,
    CurriculumModule,
    CurriculumDay,
    CurriculumChunk
)


class CurriculumLoader:
    """
    Service for loading, validating, and querying curriculum data.
    """

    def __init__(self, file_path: Optional[Path] = None):
        """
        Initialize curriculum loader with path to curriculum.json.

        Args:
            file_path (Optional[Path]): Override path for curriculum.json.
        """
        self.file_path = Path(file_path) if file_path else CURRICULUM_PATH
        self._curriculum: Optional[CurriculumSchema] = None
        self._day_map: Dict[int, CurriculumDay] = {}
        self._module_map: Dict[int, CurriculumModule] = {}
        self._day_to_module: Dict[int, CurriculumModule] = {}
        self.load()

    def load(self) -> CurriculumSchema:
        """
        Load, parse, and validate curriculum.json using Pydantic.

        Returns:
            CurriculumSchema: Parsed and validated curriculum model.

        Raises:
            FileNotFoundError: If curriculum file does not exist.
            ValueError: If JSON schema validation fails.
        """
        if not self.file_path.exists():
            error_msg = f"Curriculum file not found at: {self.file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            self._curriculum = CurriculumSchema.model_validate(raw_data)
            
            # Build fast lookup indexes
            self._day_map = {d.day: d for d in self._curriculum.days}
            self._module_map = {m.n: m for m in self._curriculum.modules}
            
            # Map each day to its parent module
            self._day_to_module = {}
            for module in self._curriculum.modules:
                start_day = module.days[0]
                end_day = module.days[1] if len(module.days) > 1 else module.days[0]
                for day_num in range(start_day, end_day + 1):
                    self._day_to_module[day_num] = module

            logger.info(
                f"Curriculum loaded successfully: {len(self._curriculum.modules)} modules, "
                f"{len(self._curriculum.days)} days."
            )
            return self._curriculum

        except Exception as e:
            logger.error(f"Failed to load/validate curriculum from {self.file_path}: {e}")
            raise ValueError(f"Curriculum validation error: {e}") from e

    def get_curriculum(self) -> CurriculumSchema:
        """Return the loaded curriculum schema."""
        if self._curriculum is None:
            return self.load()
        return self._curriculum

    def get_all_modules(self) -> List[CurriculumModule]:
        """Return all curriculum modules."""
        return self.get_curriculum().modules

    def get_module(self, module_number: int) -> Optional[CurriculumModule]:
        """Return a specific module by module number (1-8)."""
        if not self._module_map:
            self.load()
        return self._module_map.get(module_number)

    def get_all_days(self) -> List[CurriculumDay]:
        """Return all 31 curriculum days."""
        return self.get_curriculum().days

    def get_day(self, day_number: int) -> Optional[CurriculumDay]:
        """Return a specific day by day number (1-31)."""
        if not self._day_map:
            self.load()
        return self._day_map.get(day_number)

    def get_module_for_day(self, day_number: int) -> Optional[CurriculumModule]:
        """Return the parent module for a specific day."""
        if not self._day_to_module:
            self.load()
        return self._day_to_module.get(day_number)

    def get_days_by_module(self, module_number: int) -> List[CurriculumDay]:
        """Return all days associated with a specific module."""
        module = self.get_module(module_number)
        if not module:
            return []
        start_day = module.days[0]
        end_day = module.days[1] if len(module.days) > 1 else module.days[0]
        return [self._day_map[d] for d in range(start_day, end_day + 1) if d in self._day_map]

    def get_tools_for_day(self, day_number: int) -> List[str]:
        """Return the list of tools taught on a specific day."""
        day = self.get_day(day_number)
        return day.tools if day else []

    def get_objectives_for_day(self, day_number: int) -> List[str]:
        """Return the list of learning objectives for a specific day."""
        day = self.get_day(day_number)
        return day.objectives if day else []

    def get_all_tools(self) -> List[str]:
        """Return unique list of all tools across the entire curriculum."""
        tools_set = set()
        for day in self.get_all_days():
            tools_set.update(day.tools)
        return sorted(list(tools_set))

    def generate_chunks(self) -> List[CurriculumChunk]:
        """
        Transform all curriculum days into structured vector chunks ready for embeddings.

        Returns:
            List[CurriculumChunk]: List of structured chunks with text and rich metadata.
        """
        if self._curriculum is None:
            self.load()

        chunks: List[CurriculumChunk] = []
        for day in self._curriculum.days:
            module = self.get_module_for_day(day.day)
            module_n = module.n if module else 0
            module_title = module.title if module else "General"

            tools_str = ", ".join(day.tools) if day.tools else "None"
            objectives_str = "\n".join([f"- {obj}" for obj in day.objectives])

            text_content = (
                f"Day {day.day}: {day.title}\n"
                f"Module {module_n}: {module_title}\n"
                f"Type: {day.type}\n"
                f"Tools Covered: {tools_str}\n"
                f"Learning Objectives:\n{objectives_str}"
            )

            chunk = CurriculumChunk(
                chunk_id=f"curriculum-day-{day.day}",
                day=day.day,
                module_n=module_n,
                module_title=module_title,
                day_title=day.title,
                day_type=day.type,
                tools=day.tools,
                objectives=day.objectives,
                text_content=text_content
            )
            chunks.append(chunk)

        return chunks
