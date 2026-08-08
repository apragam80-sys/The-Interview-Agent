"""
Comprehensive unit test suite for Data Layer components:
- CurriculumLoader
- CandidateLoader
- Pydantic Schemas
- SQLite Database & CRUD
- EmbeddingService
- ChromaDB Integration
- Repositories (Curriculum, Candidate, Session)
"""

import unittest
import tempfile
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.loaders.curriculum_loader import CurriculumLoader
from app.loaders.candidate_loader import CandidateLoader
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService
from app.db.database import (
    save_session,
    get_session,
    list_sessions,
    delete_session,
    record_turn,
    get_session_turns,
    get_turn_count,
    get_last_turn
)
from app.repositories.curriculum_repository import CurriculumRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.session_repository import SessionRepository
from app.models.schemas import CandidateProfile, CurriculumDay


class TestDataLayer(unittest.TestCase):
    """Test cases for the entire Data Layer."""

    def test_01_curriculum_loader(self):
        """Verify CurriculumLoader loads 8 modules, 31 days, and generates valid chunks."""
        loader = CurriculumLoader()
        curriculum = loader.get_curriculum()
        
        self.assertEqual(len(curriculum.modules), 8, "Expected exactly 8 curriculum modules")
        self.assertEqual(len(curriculum.days), 31, "Expected exactly 31 curriculum days")
        
        day_1 = loader.get_day(1)
        self.assertIsNotNone(day_1)
        self.assertEqual(day_1.day, 1)
        self.assertIn("VS Code", day_1.tools)
        self.assertTrue(len(day_1.objectives) > 0)

        day_7 = loader.get_day(7)
        self.assertIsNotNone(day_7)
        self.assertEqual(day_7.title, "Embeddings Explained")
        
        # Test module queries
        module_1 = loader.get_module(1)
        self.assertIsNotNone(module_1)
        self.assertEqual(module_1.title, "Environment & Tooling")

        days_mod_3 = loader.get_days_by_module(3)
        self.assertEqual(len(days_mod_3), 4)  # Days 7, 8, 9, 10

        # Test chunk generation
        chunks = loader.generate_chunks()
        self.assertEqual(len(chunks), 31)
        self.assertTrue(chunks[0].chunk_id.startswith("curriculum-day-"))

    def test_02_candidate_loader(self):
        """Verify CandidateLoader parses profiles, missions, attempts, skipped tasks, and signals."""
        loader = CandidateLoader()
        candidates = loader.get_all_candidates()
        
        self.assertEqual(len(candidates), 20, "Expected exactly 20 candidate profiles")

        # Test CAND-001 (Sarah Johnson)
        cand_1 = loader.get_candidate_by_id("CAND-001")
        self.assertIsNotNone(cand_1)
        self.assertEqual(cand_1.member.name, "Sarah Johnson")
        self.assertEqual(cand_1.member.jobRole, "Senior Data Engineer")
        self.assertEqual(cand_1.signals.commitDays, 28)

        # Check skipped missions for Sarah Johnson (Day 29)
        skipped = loader.get_skipped_missions("CAND-001")
        skipped_days = [m.day for m in skipped]
        self.assertIn(29, skipped_days)

        # Check multi-attempt missions for Sarah Johnson (Day 12 had 4 attempts)
        multi = loader.get_multi_attempt_missions("CAND-001", min_attempts=2)
        multi_days = [m.day for m in multi]
        self.assertIn(12, multi_days)

        # Test analytics helper
        stats = loader.calculate_candidate_stats("CAND-001")
        self.assertEqual(stats["id"], "CAND-001")
        self.assertIn("firstTrySuccessRate", stats)

    def test_03_embedding_service(self):
        """Verify EmbeddingService generates normalized vector representations."""
        emb_service = EmbeddingService(dimension=384)
        
        query_vec = emb_service.embed_query("What is cosine similarity in vector search?")
        self.assertEqual(len(query_vec), 384)
        
        doc_vecs = emb_service.embed_documents([
            "Vector databases store embeddings for RAG systems.",
            "FastAPI provides fast asynchronous endpoints."
        ])
        self.assertEqual(len(doc_vecs), 2)
        self.assertEqual(len(doc_vecs[0]), 384)

    def test_04_chroma_service(self):
        """Verify ChromaService indexes curriculum chunks and performs semantic search."""
        chroma = ChromaService()
        count = chroma.collection.count()
        self.assertEqual(count, 31, "ChromaDB should have indexed all 31 curriculum days")

        # Search for vector embeddings
        results = chroma.similarity_search("vector search and embeddings", k=3)
        self.assertTrue(len(results) > 0)
        
        # Test get_by_day
        day_22_record = chroma.get_by_day(22)
        self.assertIsNotNone(day_22_record)
        self.assertEqual(day_22_record["day_title"], "Multi-Agent Orchestration")

    def test_05_sqlite_database_layer(self):
        """Verify SQLite database persistence, upsert, turn history, and cascade delete."""
        test_session_id = "test-sess-data-001"
        delete_session(test_session_id)
        
        # 1. Save / Upsert session
        save_session(
            session_id=test_session_id,
            candidate_id="CAND-001",
            candidate_name="Sarah Johnson",
            job_role="Senior Data Engineer",
            status="IN_PROGRESS",
            difficulty_level="HARD",
            total_questions=1,
            covered_days=[7],
            state_dict={"turn": 1, "test_key": "val"}
        )

        session = get_session(test_session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session["candidate_name"], "Sarah Johnson")
        self.assertEqual(session["covered_days"], [7])

        # 2. Record turns
        turn_id = record_turn(
            session_id=test_session_id,
            turn_index=1,
            question_text="Explain dense embeddings.",
            curriculum_day=7,
            difficulty="HARD",
            is_follow_up=False,
            candidate_answer="Embeddings represent text in high-dimensional vector space.",
            evaluation_dict={"correctness": 95, "depth": 90}
        )
        self.assertGreater(turn_id, 0)

        turns = get_session_turns(test_session_id)
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["curriculum_day"], 7)
        self.assertEqual(turns[0]["evaluation"]["correctness"], 95)

        # 3. Clean up
        deleted = delete_session(test_session_id)
        self.assertTrue(deleted)
        self.assertIsNone(get_session(test_session_id))

    def test_06_repositories(self):
        """Verify CurriculumRepository, CandidateRepository, and SessionRepository abstractions."""
        curriculum_repo = CurriculumRepository()
        self.assertEqual(len(curriculum_repo.get_all_days()), 31)
        self.assertIn("Python", curriculum_repo.get_tools_for_day(1))
        
        candidate_repo = CandidateRepository()
        self.assertIsNotNone(candidate_repo.get_candidate("CAND-002"))
        probes = candidate_repo.get_target_probe_days("CAND-002")
        self.assertTrue(len(probes) >= 4)

        session_repo = SessionRepository()
        test_session_id = "test-repo-sess-002"
        session_repo.save(
            session_id=test_session_id,
            candidate_id="CAND-002",
            candidate_name="Alex Turner",
            job_role="Backend Software Engineer",
            status="IN_PROGRESS",
            difficulty_level="MEDIUM",
            total_questions=0,
            covered_days=[],
            state_dict={}
        )
        fetched = session_repo.get(test_session_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.candidate_name, "Alex Turner")
        session_repo.delete(test_session_id)


if __name__ == "__main__":
    unittest.main()
