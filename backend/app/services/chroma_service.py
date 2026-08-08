"""
ChromaDB Vector Store Integration Service.
Indexes curriculum chunks, computes vector embeddings, and performs semantic search
for targeted technical objectives, tools, and topics.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from app.config import CHROMA_PERSIST_DIR, logger
from app.models.schemas import CurriculumChunk
from app.loaders.curriculum_loader import CurriculumLoader
from app.services.embedding_service import EmbeddingService, get_embedding_service


class ChromaService:
    """
    Service for managing ChromaDB collection and vector search over the curriculum.
    """

    COLLECTION_NAME = "curriculum_knowledge_base"

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize ChromaDB Vector Service.

        Args:
            persist_directory (Optional[Path]): Directory where ChromaDB indexes are saved.
            embedding_service (Optional[EmbeddingService]): Embedding generator service.
        """
        self.persist_directory = Path(persist_directory) if persist_directory else CHROMA_PERSIST_DIR
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.embedding_service = embedding_service or get_embedding_service()
        
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "31-Day AI Curriculum Knowledge Base"}
        )
        
        # Ensure collection is indexed on initialization
        if self.collection.count() == 0:
            self.index_curriculum()

    def index_curriculum(self, force_reindex: bool = False) -> int:
        """
        Chunk and index the entire 31-day curriculum into ChromaDB.

        Args:
            force_reindex (bool): Whether to wipe and re-index existing embeddings.

        Returns:
            int: Number of chunks indexed.
        """
        if force_reindex:
            try:
                self.client.delete_collection(self.COLLECTION_NAME)
                self.collection = self.client.create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"description": "31-Day AI Curriculum Knowledge Base"}
                )
                logger.info("Deleted and recreated ChromaDB collection for clean re-indexing.")
            except Exception as e:
                logger.warning(f"Could not reset collection: {e}")

        existing_count = self.collection.count()
        if existing_count >= 31 and not force_reindex:
            logger.info(f"ChromaDB curriculum collection already indexed with {existing_count} records.")
            return existing_count

        loader = CurriculumLoader()
        chunks: List[CurriculumChunk] = loader.generate_chunks()

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text_content for chunk in chunks]
        metadatas = [
            {
                "day": chunk.day,
                "module_n": chunk.module_n,
                "module_title": chunk.module_title,
                "day_title": chunk.day_title,
                "day_type": chunk.day_type,
                "tools_csv": ", ".join(chunk.tools),
                "objectives_json": json.dumps(chunk.objectives)
            }
            for chunk in chunks
        ]

        logger.info(f"Generating embeddings for {len(documents)} curriculum chunks...")
        embeddings = self.embedding_service.embed_documents(documents)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        total = self.collection.count()
        logger.info(f"ChromaDB curriculum indexing complete. Total indexed: {total}")
        return total

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search over indexed curriculum days.

        Args:
            query (str): Technical query or candidate answer.
            k (int): Number of top results to retrieve.
            filter_dict (Optional[Dict[str, Any]]): Metadata filters (e.g. {"day": 7}).

        Returns:
            List[Dict[str, Any]]: List of matching results with score, document, and metadata.
        """
        if not query.strip():
            return []

        query_vector = self.embedding_service.embed_query(query)
        
        where_clause = filter_dict if filter_dict else None
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where_clause
        )

        formatted_results: List[Dict[str, Any]] = []
        if results and "ids" in results and results["ids"]:
            ids = results["ids"][0]
            docs = results["documents"][0] if "documents" in results else []
            metas = results["metadatas"][0] if "metadatas" in results else []
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)

            for i in range(len(ids)):
                meta = metas[i] if i < len(metas) else {}
                obj_list = json.loads(meta.get("objectives_json", "[]")) if "objectives_json" in meta else []
                formatted_results.append({
                    "id": ids[i],
                    "day": meta.get("day"),
                    "module_n": meta.get("module_n"),
                    "module_title": meta.get("module_title"),
                    "day_title": meta.get("day_title"),
                    "day_type": meta.get("day_type"),
                    "tools": meta.get("tools_csv", "").split(", ") if meta.get("tools_csv") else [],
                    "objectives": obj_list,
                    "document": docs[i] if i < len(docs) else "",
                    "distance": float(distances[i]) if i < len(distances) else 0.0,
                    "similarity": round(1.0 - float(distances[i]), 4) if i < len(distances) else 1.0
                })

        return formatted_results

    def get_by_day(self, day: int) -> Optional[Dict[str, Any]]:
        """
        Fetch indexed curriculum entry for a specific day.

        Args:
            day (int): Day number (1-31).

        Returns:
            Optional[Dict[str, Any]]: Chunk record if found.
        """
        results = self.collection.get(
            ids=[f"curriculum-day-{day}"],
            include=["documents", "metadatas"]
        )
        if results and results["ids"]:
            meta = results["metadatas"][0]
            obj_list = json.loads(meta.get("objectives_json", "[]")) if "objectives_json" in meta else []
            return {
                "id": results["ids"][0],
                "day": meta.get("day"),
                "module_n": meta.get("module_n"),
                "module_title": meta.get("module_title"),
                "day_title": meta.get("day_title"),
                "day_type": meta.get("day_type"),
                "tools": meta.get("tools_csv", "").split(", ") if meta.get("tools_csv") else [],
                "objectives": obj_list,
                "document": results["documents"][0]
            }
        return None

    def get_by_module(self, module_n: int) -> List[Dict[str, Any]]:
        """
        Fetch all indexed curriculum entries for a specific module number.

        Args:
            module_n (int): Module number (1-8).

        Returns:
            List[Dict[str, Any]]: List of day chunks in that module.
        """
        results = self.collection.get(
            where={"module_n": module_n},
            include=["documents", "metadatas"]
        )
        output = []
        if results and results["ids"]:
            for i in range(len(results["ids"])):
                meta = results["metadatas"][i]
                obj_list = json.loads(meta.get("objectives_json", "[]")) if "objectives_json" in meta else []
                output.append({
                    "id": results["ids"][i],
                    "day": meta.get("day"),
                    "module_n": meta.get("module_n"),
                    "module_title": meta.get("module_title"),
                    "day_title": meta.get("day_title"),
                    "day_type": meta.get("day_type"),
                    "tools": meta.get("tools_csv", "").split(", ") if meta.get("tools_csv") else [],
                    "objectives": obj_list,
                    "document": results["documents"][i]
                })
        return output


# Global singleton instance
_chroma_service_instance: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    """Dependency injection helper returning singleton ChromaService."""
    global _chroma_service_instance
    if _chroma_service_instance is None:
        _chroma_service_instance = ChromaService()
    return _chroma_service_instance
