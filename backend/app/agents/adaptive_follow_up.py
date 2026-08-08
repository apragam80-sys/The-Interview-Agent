"""
Adaptive Follow-Up Agent.
Generates targeted technical follow-up probes when a candidate gives a shallow,
vague, or incomplete answer to test true depth of understanding.
"""

from typing import Dict, Any, List
from app.graph.state import InterviewState
from app.config import logger
from app.llm import get_llm


class AdaptiveFollowUp:
    """
    Agent 6: Adaptive Follow-Up.
    Probes candidate's reasoning, architectural details, and edge-case handling.
    """

    def __init__(self):
        """Initialize Adaptive Follow-Up Agent."""
        logger.info("AdaptiveFollowUp agent initialized")

    def generate_probe(
        self,
        question_text: str,
        answer_text: str,
        evaluation: Dict[str, Any],
        topic_info: Dict[str, Any]
    ) -> str:
        """
        Generate an adaptive technical follow-up probe.

        Args:
            question_text (str): Preceding interview question.
            answer_text (str): Candidate's shallow answer.
            evaluation (Dict[str, Any]): Evaluator feedback scores & misconceptions.
            topic_info (Dict[str, Any]): Topic details.

        Returns:
            str: Follow-up question string.
        """
        topic = topic_info.get("topic", "AI System")
        misconceptions = ", ".join(evaluation.get("misconceptions", [])) or "shallow explanation"

        prompt = (
            f"You are an expert AI Technical Interviewer conducting a deep-dive interview.\n"
            f"Topic: {topic}\n"
            f"Original Question: {question_text}\n"
            f"Candidate Answer: {answer_text}\n"
            f"Assessment Gaps: {misconceptions}\n\n"
            f"Task: Generate a direct, targeted follow-up probe that asks the candidate to explain the underlying "
            f"mechanisms, mathematical concepts, or concrete implementation details they omitted. "
            f"Start with a short phrase like '[Follow-up on {topic}]' or 'To go deeper on your answer:'. "
            f"Keep it strictly 1-2 sentences without generic greetings."
        )

        try:
            llm = get_llm(temperature=0.3)
            response = llm.invoke(prompt)
            probe_text = response.content.strip()
            if probe_text and len(probe_text) > 15:
                return probe_text
        except Exception as e:
            logger.warning(f"LLM Adaptive Follow-up generation failed: {e}. Using deterministic probe fallback.")

        # Fallback targeted probe templates (clearly distinct from main questions)
        day_num = topic_info.get("day", 7)
        probe_fallbacks = {
            7: f"To go deeper on Day {day_num} ({topic}): Could you elaborate specifically on the mathematical difference between Euclidean distance and cosine distance for embeddings, and when one is preferred over the other?",
            8: f"To explore further on Day {day_num} ({topic}): Can you detail how HNSW graph construction establishes connections across multi-layer graphs and handles index updates in production?",
            10: f"Follow-up on Day {day_num} ({topic}): How do you specifically configure chunk overlapping, and what exact re-ranking formula do you use when combining BM25 and vector scores?",
            12: f"To clarify your implementation on Day {day_num} ({topic}): Could you walk through a concrete example of a few-shot prompt template and describe how you handle context window overflow when user inputs are large?",
            16: f"Deep dive on Day {day_num} ({topic}): What specific async connection pooling or concurrency throttling mechanisms do you implement in FastAPI to prevent LLM timeouts from blocking worker threads?",
            22: f"To probe deeper into Day {day_num} ({topic}): In your LangGraph state graph, how do you handle state schema validation during graph transitions and rollback from invalid tool outputs?",
            23: f"Follow-up on Day {day_num} ({topic}): How does the MCP client authenticate and negotiate tool schema capabilities with the underlying MCP server protocol?"
        }

        return probe_fallbacks.get(
            day_num,
            f"To explore your answer further on {topic}: Could you explain the concrete architectural trade-offs, failure modes, or implementation details you would consider in production?"
        )

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for AdaptiveFollowUp.
        """
        incoming_message = state.get("incoming_message", "")
        current_q = state.get("current_question", {})
        evaluations = state.get("evaluations", [])
        last_eval = evaluations[-1]["evaluation"] if evaluations else {}
        question_text = state.get("latest_reply", "")
        total_q = state.get("total_questions_asked", 1) + 1

        probe = self.generate_probe(question_text, incoming_message, last_eval, current_q)

        return {
            "latest_reply": probe,
            "is_follow_up": True,
            "was_follow_up": True,
            "follow_up_count_for_current_q": 1,
            "total_questions_asked": total_q
        }
