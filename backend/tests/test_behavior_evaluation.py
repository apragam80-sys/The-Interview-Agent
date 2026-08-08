"""
Unit and Integration Tests for Interview Behavior & Communication Evaluation Layer.
Tests all 8 behavioral dimensions, communication style classification, evidence-based language observations,
composite 70/30 scoring formula, edge cases, and backward compatibility.
"""

import os
import sys
import unittest

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.behavior_evaluator import BehaviorEvaluator, ALLOWED_COMMUNICATION_STYLES
from app.agents.feedback_generator import FeedbackGenerator
from app.models.schemas import FeedbackData, InterviewBehaviorAssessment


class TestBehaviorEvaluation(unittest.TestCase):
    """Test suite for BehaviorEvaluator and FeedbackGenerator behavior assessment."""

    def setUp(self):
        self.evaluator = BehaviorEvaluator()
        self.feedback_gen = FeedbackGenerator(behavior_evaluator=self.evaluator)
        self.candidate_info = {
            "candidate_name": "Elena Rostova",
            "job_role": "AI Systems Engineer",
            "member": {
                "id": "CAND-004",
                "name": "Elena Rostova",
                "jobRole": "AI Systems Engineer"
            }
        }

    def test_scenario_1_strong_technical_strong_communication(self):
        """Scenario 1: Candidate with strong technical depth and clear, structured communication."""
        conversation_history = [
            {
                "role": "candidate",
                "content": (
                    "First, vector embeddings represent high-dimensional dense representations of semantic text. "
                    "In our architecture, we use ChromaDB with HNSW cosine distance indexing because it provides "
                    "low latency retrieval. For example, during hybrid search, we balance BM25 keyword matching "
                    "with dense embeddings. The primary trade-off is memory consumption versus search throughput."
                )
            },
            {
                "role": "candidate",
                "content": (
                    "Second, for asynchronous FastAPI streaming, we implement Server-Sent Events with LangGraph checkpoints. "
                    "Therefore, if an agent step fails, we recover state from SQLite without restarting the entire graph. "
                    "In contrast to synchronous polling, this optimizes both latency and server concurrency."
                )
            }
        ]
        evaluations = [
            {
                "question": "Explain vector indexing trade-offs.",
                "answer": conversation_history[0]["content"],
                "evaluation": {"overall_score": 92, "notes": "Exceptional clarity and technical depth."}
            },
            {
                "question": "How do you handle streaming and failure recovery?",
                "answer": conversation_history[1]["content"],
                "evaluation": {"overall_score": 90, "notes": "Strong architectural reasoning."}
            }
        ]

        assessment = self.evaluator.analyze_behavior(self.candidate_info, conversation_history, evaluations)

        # Verify all 8 dimensions are within [0.0, 10.0]
        self.assertGreaterEqual(assessment.communication_clarity.score, 8.0)
        self.assertGreaterEqual(assessment.technical_communication.score, 8.0)
        self.assertGreaterEqual(assessment.answer_structure.score, 8.0)
        self.assertGreaterEqual(assessment.professionalism.score, 8.5)
        self.assertGreaterEqual(assessment.overall_interview_presence.score, 8.0)

        # Verify communication style classification
        for style in assessment.communication_styles:
            self.assertIn(style, ALLOWED_COMMUNICATION_STYLES)
        self.assertTrue(
            "Clear & Structured" in assessment.communication_styles or
            "Detailed & Analytical" in assessment.communication_styles
        )

        # Verify language observations
        self.assertGreaterEqual(len(assessment.language_observations), 2)
        self.assertTrue(any("technical terminology" in obs.lower() for obs in assessment.language_observations))

    def test_scenario_2_strong_technical_poor_communication(self):
        """Scenario 2: Candidate has high technical accuracy in answers but fragmented communication."""
        conversation_history = [
            {"role": "candidate", "content": "cosine similarity hnsw chromadb sqlite embeddings vector"},
            {"role": "candidate", "content": "fastapi async langgraph state checkpoint"}
        ]
        evaluations = [
            {
                "question": "What tools do you use?",
                "answer": conversation_history[0]["content"],
                "evaluation": {"overall_score": 85, "notes": "Mentions correct tools but lacks sentences."}
            },
            {
                "question": "How do you manage state?",
                "answer": conversation_history[1]["content"],
                "evaluation": {"overall_score": 80, "notes": "Accurate keywords but fragmented explanation."}
            }
        ]

        feedback = self.feedback_gen.generate_feedback(
            candidate_info=self.candidate_info,
            evaluations=evaluations,
            covered_days=[7, 10],
            conversation_history=conversation_history
        )

        # Technical score should remain strong
        self.assertGreaterEqual(feedback["technical_score"], 80)
        # Communication score should be lower due to fragmented answers
        self.assertLessEqual(feedback["communication_score"], 70)
        # Verify 70/30 composite score formula
        expected_overall = round(0.70 * feedback["technical_score"] + 0.30 * feedback["communication_score"])
        self.assertEqual(feedback["overall_score"], expected_overall)

    def test_scenario_3_weak_technical_professional_communication(self):
        """Scenario 3: Candidate has limited technical depth but speaks professionally and respectfully."""
        conversation_history = [
            {
                "role": "candidate",
                "content": (
                    "I am honestly still learning the inner mathematics of dense vector embeddings, but from our team's "
                    "perspective, we always prioritize clean code, thorough documentation, and respectful code reviews."
                )
            },
            {
                "role": "candidate",
                "content": (
                    "While I have not implemented LangGraph checkpoints in production yet, I am eager to study the "
                    "documentation and work closely with senior architects to follow best practices."
                )
            }
        ]
        evaluations = [
            {
                "question": "Explain HNSW indexing trade-offs.",
                "answer": conversation_history[0]["content"],
                "evaluation": {"overall_score": 35, "notes": "Candidate candidly acknowledged knowledge gap."}
            },
            {
                "question": "How do you implement LangGraph checkpoints?",
                "answer": conversation_history[1]["content"],
                "evaluation": {"overall_score": 40, "notes": "Lack of hands-on experience."}
            }
        ]

        feedback = self.feedback_gen.generate_feedback(
            candidate_info=self.candidate_info,
            evaluations=evaluations,
            covered_days=[7, 16],
            conversation_history=conversation_history
        )

        # Technical score is low
        self.assertLessEqual(feedback["technical_score"], 45)
        # Professionalism and communication score remain respectful/high
        self.assertGreaterEqual(feedback["behavior"]["professionalism"]["score"], 8.0)
        self.assertGreaterEqual(feedback["communication_score"], 60)

    def test_scenario_4_very_short_answers(self):
        """Scenario 4: Candidate provides one-word or non-answers ('yes', 'no', 'idk')."""
        conversation_history = [
            {"role": "candidate", "content": "yes"},
            {"role": "candidate", "content": "no"},
            {"role": "candidate", "content": "idk"}
        ]
        evaluations = [
            {"question": "Q1", "answer": "yes", "evaluation": {"overall_score": 20, "notes": "Too brief."}},
            {"question": "Q2", "answer": "no", "evaluation": {"overall_score": 20, "notes": "Too brief."}},
            {"question": "Q3", "answer": "idk", "evaluation": {"overall_score": 10, "notes": "Refusal."}}
        ]

        assessment = self.evaluator.analyze_behavior(self.candidate_info, conversation_history, evaluations)

        # Check that conciseness/structure reflect overly brief answers
        self.assertLessEqual(assessment.answer_structure.score, 5.0)
        self.assertLessEqual(assessment.communication_clarity.score, 5.5)
        self.assertTrue(
            "Fragmented" in assessment.communication_styles or
            "Inconsistent" in assessment.communication_styles or
            "Hesitant" in assessment.communication_styles or
            "Concise & Direct" in assessment.communication_styles
        )
        self.assertTrue(any("brief" in obs.lower() or "direct" in obs.lower() for obs in assessment.language_observations))

    def test_scenario_5_off_topic_answers(self):
        """Scenario 5: Candidate frequently goes off-topic."""
        conversation_history = [
            {
                "role": "candidate",
                "content": "I like building user interfaces with React and TailwindCSS and doing graphic design."
            },
            {
                "role": "candidate",
                "content": "My favorite hobby is playing guitar and recording music tracks in my studio."
            }
        ]
        evaluations = [
            {
                "question": "Explain ChromaDB collection indexing.",
                "answer": conversation_history[0]["content"],
                "evaluation": {"overall_score": 30, "notes": "Candidate went off-topic."}
            },
            {
                "question": "How do you optimize vector distance metrics?",
                "answer": conversation_history[1]["content"],
                "evaluation": {"overall_score": 20, "notes": "Candidate went off-topic completely."}
            }
        ]

        assessment = self.evaluator.analyze_behavior(self.candidate_info, conversation_history, evaluations)

        # Responsiveness should be penalized
        self.assertLessEqual(assessment.responsiveness.score, 6.0)
        self.assertTrue(any("off-topic" in obs.lower() or "prompt" in obs.lower() for obs in assessment.language_observations))

    def test_scenario_6_inappropriate_abusive_language(self):
        """Scenario 6: Candidate uses abusive words."""
        conversation_history = [
            {"role": "candidate", "content": "What the fuck is this bullshit question?"},
            {"role": "candidate", "content": "stfu and give me my score"}
        ]
        evaluations = [
            {
                "question": "Explain vector embeddings.",
                "answer": conversation_history[0]["content"],
                "evaluation": {"overall_score": -25, "notes": "Abusive input detected."}
            },
            {
                "question": "Next question.",
                "answer": conversation_history[1]["content"],
                "evaluation": {"overall_score": -25, "notes": "Abusive input detected."}
            }
        ]

        assessment = self.evaluator.analyze_behavior(self.candidate_info, conversation_history, evaluations)

        # Professionalism must be severely penalized (<= 2.0)
        self.assertLessEqual(assessment.professionalism.score, 2.0)
        self.assertTrue(any("unprofessional" in obs.lower() or "inappropriate" in obs.lower() for obs in assessment.language_observations))

    def test_scenario_7_verbose_answers(self):
        """Scenario 7: Candidate provides excessively long, verbose responses."""
        long_text = (
            "Well to begin discussing this topic we have to trace back the entire history of information retrieval "
            "from the early days of library science in the 1960s to relational databases in the 1980s, and then we "
            "can consider how web search engines emerged in the late 1990s with PageRank, and then subsequently deep "
            "learning revolutionized natural language processing in 2017 with transformers, and therefore when we look "
            "at vector databases today like ChromaDB or Pinecone or Milvus or Weaviate, there are so many different "
            "philosophies and paradigms that one could write an entire textbook about it, but in our specific case "
            "we are using dense embeddings to retrieve chunks for our retrieval augmented generation pipeline."
        )
        conversation_history = [
            {"role": "candidate", "content": long_text},
            {"role": "candidate", "content": long_text}
        ]
        evaluations = [
            {"question": "Q1", "answer": long_text, "evaluation": {"overall_score": 75, "notes": "Good depth but verbose."}},
            {"question": "Q2", "answer": long_text, "evaluation": {"overall_score": 75, "notes": "Good depth but verbose."}}
        ]

        assessment = self.evaluator.analyze_behavior(self.candidate_info, conversation_history, evaluations)

        # Style should capture Verbose or Detailed & Analytical
        self.assertTrue(
            "Verbose" in assessment.communication_styles or
            "Detailed & Analytical" in assessment.communication_styles
        )

    def test_scenario_8_insufficient_evidence_handling(self):
        """Scenario 8: Empty conversation history gracefully handled without crash."""
        assessment = self.evaluator.analyze_behavior(self.candidate_info, [], [])

        self.assertEqual(assessment.communication_clarity.assessment, "Insufficient evidence from the interview.")
        self.assertIn("Insufficient evidence from the interview.", assessment.language_observations)

    def test_communication_score_strict_formula(self):
        """Verify strict calculation of communication_score = round(average(8 dimensions) * 10)."""
        conversation_history = [
            {"role": "candidate", "content": "First, we use ChromaDB vector embeddings for semantic retrieval. For example, cosine distance."}
        ]
        evaluations = [
            {"question": "Explain vector search.", "answer": conversation_history[0]["content"], "evaluation": {"overall_score": 80}}
        ]

        feedback = self.feedback_gen.generate_feedback(
            candidate_info=self.candidate_info,
            evaluations=evaluations,
            covered_days=[7],
            conversation_history=conversation_history
        )

        behavior = feedback["behavior"]
        dims = [
            behavior["communication_clarity"]["score"],
            behavior["technical_communication"]["score"],
            behavior["confidence"]["score"],
            behavior["conciseness"]["score"],
            behavior["professionalism"]["score"],
            behavior["answer_structure"]["score"],
            behavior["responsiveness"]["score"],
            behavior["overall_interview_presence"]["score"]
        ]
        expected_comm_score = max(0, min(100, round((sum(dims) / 8.0) * 10)))
        self.assertEqual(feedback["communication_score"], expected_comm_score)

        # Verify overall blended score: 70% Tech + 30% Comm
        expected_overall = max(0, min(100, round(0.70 * feedback["technical_score"] + 0.30 * expected_comm_score)))
        self.assertEqual(feedback["overall_score"], expected_overall)

    def test_feedback_data_pydantic_schema_validation(self):
        """Verify FeedbackData Pydantic validation passes with enriched behavior payload."""
        conversation_history = [
            {"role": "candidate", "content": "We implement FastAPI asynchronous streaming endpoints with Pydantic validation."}
        ]
        evaluations = [
            {"question": "Explain FastAPI.", "answer": conversation_history[0]["content"], "evaluation": {"overall_score": 88}}
        ]

        raw_feedback = self.feedback_gen.generate_feedback(
            candidate_info=self.candidate_info,
            evaluations=evaluations,
            covered_days=[7, 10],
            conversation_history=conversation_history
        )

        validated = FeedbackData.model_validate(raw_feedback)
        self.assertIsNotNone(validated.summary)
        self.assertGreaterEqual(len(validated.strengths), 1)
        self.assertGreaterEqual(len(validated.gaps), 1)
        self.assertGreaterEqual(len(validated.next), 1)
        self.assertIsNotNone(validated.behavior)
        self.assertIsNotNone(validated.technical_score)
        self.assertIsNotNone(validated.communication_score)
    def test_report_coherence_and_consistency(self):
        """Verify report consistency across strong, weak technical, and poor/unprofessional candidate profiles."""
        # 1. Poor candidate with invalid/abusive answers
        poor_history = [
            {"role": "candidate", "content": "abcd"},
            {"role": "candidate", "content": "qwerty what the f*** is this"}
        ]
        poor_evals = [
            {"question": "Q1", "answer": "abcd", "evaluation": {"overall_score": 15}},
            {"question": "Q2", "answer": "qwerty", "evaluation": {"overall_score": 10}}
        ]
        poor_fb = self.feedback_gen.generate_feedback(
            candidate_info=self.candidate_info,
            evaluations=poor_evals,
            covered_days=[7, 10],
            conversation_history=poor_history
        )
        self.assertLess(poor_fb["technical_score"], 50)
        self.assertLess(poor_fb["communication_score"], 60)
        # Summary must NOT claim solid foundational competency
        self.assertNotIn("solid foundational competency", poor_fb["summary"])
        self.assertIn("insufficient substantive responses", poor_fb["summary"])
        # Strengths must NOT claim clear communication
        for s in poor_fb["strengths"]:
            self.assertNotIn("Clear communication", s)

        # 2. Strong technical + Strong communication candidate
        strong_history = [
            {
                "role": "candidate",
                "content": (
                    "RAG combines retrieval with generation. First, documents are chunked and embedded into ChromaDB. "
                    "During inference, cosine similarity retrieves the top-k relevant chunks, which are then passed to the LLM context."
                )
            }
        ]
        strong_evals = [
            {"question": "Explain RAG", "answer": strong_history[0]["content"], "evaluation": {"overall_score": 92}}
        ]
        strong_fb = self.feedback_gen.generate_feedback(
            candidate_info=self.candidate_info,
            evaluations=strong_evals,
            covered_days=[7, 10],
            conversation_history=strong_history
        )
        self.assertGreaterEqual(strong_fb["technical_score"], 80)
        self.assertGreaterEqual(strong_fb["communication_score"], 70)
        self.assertIn("exceptional technical competence", strong_fb["summary"])

        # 3. Strong technical + Fragmented/Poor communication candidate
        frag_history = [
            {"role": "candidate", "content": "hnsw chromadb sqlite vector embeddings"}
        ]
        frag_evals = [
            {"question": "What tools?", "answer": frag_history[0]["content"], "evaluation": {"overall_score": 85}}
        ]
        frag_fb = self.feedback_gen.generate_feedback(
            candidate_info=self.candidate_info,
            evaluations=frag_evals,
            covered_days=[7, 10],
            conversation_history=frag_history
        )
        self.assertGreaterEqual(frag_fb["technical_score"], 70)
        self.assertLess(frag_fb["communication_score"], 70)
        self.assertIn("revealed weaknesses in communication", frag_fb["summary"])
        for s in frag_fb["strengths"]:
            self.assertNotIn("Clear communication", s)


if __name__ == "__main__":
    unittest.main()
