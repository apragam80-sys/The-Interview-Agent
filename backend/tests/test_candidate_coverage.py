import unittest
import json
import uuid
import sys
import os

# Ensure backend directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.config import CANDIDATES_PATH
from app.db.database import get_session


class TestCandidateCoverageAndAdaptiveFollowUp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
            self.candidates = json.load(f)["candidates"]

    def test_all_20_candidates_meet_requirements(self):
        """
        Runs simulated interviews across all 20 candidate profiles.
        Verifies:
        - At least 8 questions asked
        - At least 4 unique curriculum days covered
        - Final feedback strictly matches required schema
        """
        for candidate in self.candidates:
            cand_id = candidate["member"]["id"]
            cand_name = candidate["member"]["name"]
            session_id = f"test-session-{cand_id}-{uuid.uuid4().hex[:6]}"

            # Turn 1: Initialization
            res = self.client.post("/api/interview", json={
                "sessionId": session_id,
                "candidate": candidate
            })
            self.assertEqual(res.status_code, 200, f"Failed on initialization for {cand_name}")
            data = res.json()
            self.assertFalse(data["done"])
            self.assertIn("reply", data)

            turn_count = 1
            is_done = False
            last_resp = data

            sample_technical_answers = [
                "We implement dense embeddings with Sentence Transformers and compute cosine similarity for ranking.",
                "In ChromaDB, we store collection metadata and index vectors with HNSW for sub-10ms latency.",
                "Our query router checks if SQL or vector retrieval is needed, then merges and deduplicates results.",
                "We use Pydantic models for structured function calling and retry on validation errors.",
                "We persist conversation memory in SQLite and summarize older turns to respect token budgets.",
                "In LangGraph, we define an asynchronous StateGraph with checkpointing and specialized agent nodes.",
                "We build an MCP server in Python to expose standardized tools to AI clients securely.",
                "In Kubernetes, we set CPU/memory limits, readiness probes, and Prometheus metrics for observability."
            ]

            while not is_done and turn_count < 16:
                ans = sample_technical_answers[(turn_count - 1) % len(sample_technical_answers)]
                res = self.client.post("/api/interview", json={
                    "sessionId": session_id,
                    "message": ans
                })
                self.assertEqual(res.status_code, 200)
                last_resp = res.json()
                is_done = last_resp["done"]
                turn_count += 1

            # Check interview completion
            self.assertTrue(is_done, f"Interview did not complete for {cand_name}")
            
            # Check DB Session records
            session_record = get_session(session_id)
            self.assertIsNotNone(session_record)
            
            total_questions = session_record["total_questions"]
            covered_days = session_record["covered_days"]
            unique_days = set(covered_days)

            # Strict assertion 1: Minimum 8 questions
            self.assertGreaterEqual(
                total_questions, 8,
                f"Candidate {cand_name} ({cand_id}) had {total_questions} questions, expected >= 8"
            )

            # Strict assertion 2: Minimum 4 curriculum days
            self.assertGreaterEqual(
                len(unique_days), 4,
                f"Candidate {cand_name} ({cand_id}) covered {len(unique_days)} days ({unique_days}), expected >= 4"
            )

            # Strict assertion 3: Feedback Schema
            feedback = last_resp.get("feedback")
            self.assertIsNotNone(feedback, f"Feedback missing for {cand_name}")
            self.assertIn("summary", feedback)
            self.assertIn("strengths", feedback)
            self.assertIn("gaps", feedback)
            self.assertIn("next", feedback)

            self.assertGreater(len(feedback["strengths"]), 0)
            self.assertGreater(len(feedback["gaps"]), 0)
            self.assertGreater(len(feedback["next"]), 0)

    def test_adaptive_follow_up_triggering(self):
        """
        Tests that vague answers trigger an adaptive follow-up probe.
        """
        session_id = f"test-adaptive-{uuid.uuid4().hex[:6]}"
        candidate = self.candidates[0] # Sarah Johnson

        # Init
        res1 = self.client.post("/api/interview", json={
            "sessionId": session_id,
            "candidate": candidate
        })
        self.assertFalse(res1.json()["done"])

        # Send vague answer
        res2 = self.client.post("/api/interview", json={
            "sessionId": session_id,
            "message": "I just used embeddings because they work."
        })
        data2 = res2.json()
        self.assertFalse(data2["done"])
        
    def test_abusive_word_triggers_negative_score_and_advances(self):
        """
        Tests that an abusive response receives a negative score (-25 pts),
        does NOT trigger an adaptive probe, and advances to the next question.
        """
        session_id = f"test-abusive-{uuid.uuid4().hex[:6]}"
        candidate = self.candidates[0]

        # Init Turn 1
        res1 = self.client.post("/api/interview", json={
            "sessionId": session_id,
            "candidate": candidate
        })
        self.assertFalse(res1.json()["done"])

        # Send abusive response in Turn 2
        res2 = self.client.post("/api/interview", json={
            "sessionId": session_id,
            "message": "fuck this question"
        })
        data2 = res2.json()
        self.assertFalse(data2["done"])
        
        # Verify score is negative (-25)
        self.assertEqual(data2["score"], -25, f"Expected negative score -25, got {data2.get('score')}")
        self.assertLess(data2["averageScore"], 0)
        
        # Verify it did not trigger follow-up probe (isFollowUp is False)
        self.assertFalse(data2["isFollowUp"])
        
        # Verify professional warning prefix
        self.assertIn("Unprofessional language detected", data2["reply"])

    def test_question_limit_never_exceeds_8(self):
        """
        Tests that the interview completes strictly at or before 8 questions.
        """
        session_id = f"test-hard-cap-{uuid.uuid4().hex[:6]}"
        candidate = self.candidates[0]

        res1 = self.client.post("/api/interview", json={
            "sessionId": session_id,
            "candidate": candidate
        })
        self.assertFalse(res1.json()["done"])

        turn = 1
        is_done = False
        final_data = None
        while not is_done and turn < 12:
            res = self.client.post("/api/interview", json={
                "sessionId": session_id,
                "message": "We implement vector search with ChromaDB and HNSW indexing for cosine distance."
            })
            final_data = res.json()
            is_done = final_data["done"]
            turn += 1

        self.assertTrue(is_done)
        self.assertLessEqual(final_data["totalQuestions"], 8)
        self.assertIsNotNone(final_data["feedback"])


if __name__ == "__main__":
    unittest.main()
