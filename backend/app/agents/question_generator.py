"""
Question Generator Agent.
Synthesizes scenario-driven, technical interview questions tailored to the candidate's
experience tier, curriculum objectives, and specific toolsets.
"""

from typing import Dict, Any, List
from app.graph.state import InterviewState
from app.config import logger
from app.llm import get_llm


class QuestionGenerator:
    """
    Agent 4: Question Generator.
    Generates real-world, architecture-level and implementation-level technical questions.
    """

    def __init__(self):
        """Initialize Question Generator."""
        logger.info("QuestionGenerator agent initialized")

    def generate_question(
        self,
        plan_item: Dict[str, Any],
        candidate_info: Dict[str, Any],
        previous_evaluations: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a technical interview question using LLM or structured templates.

        Args:
            plan_item (Dict[str, Any]): Roadmap item for current question.
            candidate_info (Dict[str, Any]): Candidate metadata.
            previous_evaluations (List[Dict[str, Any]]): Prior turn evaluation scores.

        Returns:
            str: Question string to present to candidate.
        """
        day_num = plan_item.get("day", 7)
        topic = plan_item.get("topic", "System Architecture")
        module_title = plan_item.get("module_title", "AI Architecture")
        difficulty = plan_item.get("difficulty", "MID")
        tools = ", ".join(plan_item.get("tools", [])) or "Standard AI stack"
        objectives = "\n".join([f"- {o}" for o in plan_item.get("objectives", [])])

        candidate_name = candidate_info.get("candidate_name", "Candidate")
        candidate_role = candidate_info.get("job_role", "Software Engineer")

        prompt = (
            f"You are a Principal AI Technical Interviewer conducting a rigorous technical interview.\n"
            f"Candidate: {candidate_name} ({candidate_role}, Tier: {difficulty})\n"
            f"Topic: Day {day_num} - {topic} ({module_title})\n"
            f"Target Tools: {tools}\n"
            f"Learning Objectives:\n{objectives}\n\n"
            f"Task: Generate a realistic, scenario-based technical question testing practical architectural understanding "
            f"and trade-offs for this topic. Keep the question direct, professional, and under 3-4 sentences without preambles or greetings."
        )

        try:
            llm = get_llm(temperature=0.4)
            response = llm.invoke(prompt)
            question_text = response.content.strip()
            if question_text and len(question_text) > 20:
                return question_text
        except Exception as e:
            logger.warning(f"LLM question generation failed: {e}. Using deterministic technical template.")

        # Robust domain-specific question templates mapped by day
        templates = {
            1: "In your development workflow with VS Code and Python virtual environments, how do you isolate dependencies across microservices and ensure reproducible runtime configurations?",
            2: "When deploying local LLMs with Ollama or Qwen, how do you handle memory quantization trade-offs (e.g. 4-bit vs 8-bit GGUF) and manage token throughput under concurrency?",
            3: "How do you structure the interface between a FastAPI backend and a React/Vite frontend to handle asynchronous streaming LLM tokens efficiently?",
            7: "When generating text embeddings for semantic search, how do cosine similarity and dot product compare in normalized vector spaces, and how do you handle high-dimensional vector degradation?",
            8: "In vector databases like ChromaDB, how does HNSW indexing balance recall vs query latency compared to flat IVF indexes when scaling to millions of embeddings?",
            10: "In a production RAG matching engine, how do you implement hybrid search (combining dense vector embeddings with sparse BM25 keyword matching) and tune the re-ranking score?",
            12: "When designing prompts for complex multi-step reasoning, how do you structure system instructions, few-shot examples, and delimiter guards to reliably mitigate hallucinations?",
            13: "How do you enforce strict schema validation for LLM function calling with Pydantic and handle malformed JSON responses when external APIs fail?",
            16: "In a production chatbot backend using FastAPI, how do you implement streaming SSE (Server-Sent Events) and manage background asynchronous task lifecycles?",
            18: "When streaming LLM responses to clients, how do you handle network backpressure, dropped socket connections, and real-time token buffering?",
            20: "How do you design conversation memory in a stateful chatbot to maintain relevant long-term context while strictly bounding token window overhead?",
            21: "When implementing LangChain agents with tool calling, how do you prevent infinite execution loops and enforce tool execution timeouts?",
            22: "In LangGraph, how do you model state checkpoints and conditional edge routing when orchestrating multi-agent collaboration with human-in-the-loop validation?",
            23: "How does the Model Context Protocol (MCP) standardize tool discovery and context delivery between AI host applications and local client servers?",
            28: "When containerizing an AI microservice with Docker and Kubernetes, what strategies do you use for health probes, GPU resource scheduling, and secret management?",
            29: "How do you instrument an LLM application with Prometheus and OpenTelemetry to track token latency, error rates, and hallucination metrics in production?",
            31: "In your end-to-end Capstone architecture, what were the primary scalability bottlenecks you encountered and how did you architect system failure recovery?"
        }

        return templates.get(
            day_num,
            f"Regarding Day {day_num} ({topic}): In a production environment using {tools}, how do you architect the core components and evaluate performance trade-offs under scale?"
        )

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for QuestionGenerator.
        """
        roadmap = state.get("planned_roadmap", [])
        q_idx = state.get("current_question_index", 0)
        candidate_info = state.get("candidate_signals", {})
        evaluations = state.get("evaluations", [])

        if not roadmap or q_idx >= len(roadmap):
            plan_item = {
                "step": q_idx + 1,
                "day": 31,
                "topic": "Capstone Architecture",
                "module_title": "Production",
                "difficulty": state.get("difficulty_level", "MID"),
                "tools": ["FastAPI", "Docker", "ChromaDB"],
                "objectives": ["System design", "Failure recovery"]
            }
        else:
            plan_item = roadmap[q_idx]

        question_text = self.generate_question(plan_item, candidate_info, evaluations)

        # If candidate previously gave an abusive or refusal response, prepend a professional transition
        is_abusive = state.get("is_abusive", False)
        if not is_abusive and evaluations:
            last_ev = evaluations[-1].get("evaluation", {})
            is_abusive = last_ev.get("is_abusive", False)

        if is_abusive:
            question_text = (
                "⚠️ Unprofessional language detected. A score deduction (-25 pts) has been recorded in your assessment.\n\n"
                f"Let's proceed to the next technical topic:\n{question_text}"
            )

        # Track covered days and question counters
        covered_days = list(state.get("covered_days", []))
        day_num = plan_item.get("day", 7)
        if day_num not in covered_days:
            covered_days.append(day_num)

        total_questions = state.get("total_questions_asked", 0) + 1

        return {
            "current_question": plan_item,
            "current_question_index": q_idx + 1,
            "latest_reply": question_text,
            "total_questions_asked": total_questions,
            "covered_days": covered_days,
            "is_follow_up": False,
            "was_follow_up": False,
            "follow_up_count_for_current_q": 0,
            "is_abusive": False
        }
