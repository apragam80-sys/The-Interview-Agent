"""
Feedback Generator Agent.
Synthesizes candidate responses and multi-rubric evaluation scores into a structured,
actionable technical feedback payload (summary, strengths, gaps, next).
"""

import json
import re
from typing import Dict, Any, List, Optional
from app.graph.state import InterviewState
from app.config import logger
from app.llm import get_llm
from app.services.behavior_evaluator import get_behavior_evaluator, BehaviorEvaluator


class FeedbackGenerator:
    """
    Agent 8: Feedback Generator.
    Produces comprehensive final feedback strictly adhering to API contract,
    enriched with behavioral/communication analysis and composite 70/30 scoring.
    """

    def __init__(self, behavior_evaluator: Optional[BehaviorEvaluator] = None):
        """Initialize Feedback Generator."""
        self.behavior_evaluator = behavior_evaluator or get_behavior_evaluator()
        logger.info("FeedbackGenerator agent initialized")

    def generate_feedback(
        self,
        candidate_info: Dict[str, Any],
        evaluations: List[Dict[str, Any]],
        covered_days: List[int],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate structured feedback payload matching API schema.

        Args:
            candidate_info (Dict[str, Any]): Candidate metadata and background signals.
            evaluations (List[Dict[str, Any]]): Collected turn evaluations.
            covered_days (List[int]): List of tested curriculum day integers.
            conversation_history (Optional[List[Dict[str, Any]]]): Complete transcript turns.

        Returns:
            Dict[str, Any]: Structured feedback matching FeedbackData schema.
        """
        name = candidate_info.get("candidate_name") or candidate_info.get("member", {}).get("name", "Candidate")
        role = candidate_info.get("job_role") or candidate_info.get("member", {}).get("jobRole", "Software Engineer")
        days_str = ", ".join([f"Day {d}" for d in sorted(set(covered_days))])

        eval_summaries = []
        tech_scores = []
        for idx, ev in enumerate(evaluations):
            q = ev.get("question", "")[:60]
            ans = ev.get("answer", "")[:60]
            res = ev.get("evaluation", {})
            score = res.get("overall_score", 70)
            # Pure Technical Competency: evaluated solely from substantive technical answers.
            # Professionalism / behavioral penalties are applied directly to the Communication score.
            if not res.get("is_abusive", False) and score >= 0:
                tech_scores.append(score)
            notes = res.get("notes", "")
            eval_summaries.append(f"Turn {idx+1} (Score {score}/100): Q: {q} | Ans: {ans} | Notes: {notes}")

        # Compute Technical Score (0-100) - uncontaminated by behavioral penalties
        if tech_scores:
            technical_score = max(0, min(100, round(sum(tech_scores) / len(tech_scores))))
        else:
            technical_score = 0

        # Run Behavior & Communication Analysis across complete conversation
        history = conversation_history or []
        behavior_assessment = self.behavior_evaluator.analyze_behavior(
            candidate_info=candidate_info,
            conversation_history=history,
            evaluations=evaluations
        )

        # Calculate strict communication score: average of the 8 dimension scores * 10
        dim_scores = [
            behavior_assessment.communication_clarity.score,
            behavior_assessment.technical_communication.score,
            behavior_assessment.confidence.score,
            behavior_assessment.conciseness.score,
            behavior_assessment.professionalism.score,
            behavior_assessment.answer_structure.score,
            behavior_assessment.responsiveness.score,
            behavior_assessment.overall_interview_presence.score,
        ]
        communication_score = max(0, min(100, round((sum(dim_scores) / len(dim_scores)) * 10)))

        # Composite overall score: 70% Technical + 30% Communication
        overall_score = max(0, min(100, round(0.70 * technical_score + 0.30 * communication_score)))

        styles_str = ", ".join(behavior_assessment.communication_styles)
        obs_str = "; ".join(behavior_assessment.language_observations)

        prompt = (
            f"You are a Principal AI Technical Hiring Manager writing the final executive evaluation report for {name} ({role}).\n"
            f"Curriculum Days Evaluated: {days_str}\n"
            f"Technical Score: {technical_score}/100\n"
            f"Communication Score: {communication_score}/100\n"
            f"Overall Blended Score: {overall_score}/100\n"
            f"Communication Styles Identified: {styles_str}\n"
            f"Language & Behavioral Observations: {obs_str}\n"
            f"Turn-by-Turn Evaluations:\n" + "\n".join(eval_summaries) + "\n\n"
            f"CRITICAL CONSISTENCY & COHERENCE RULES:\n"
            f"1. Executive Summary MUST accurately distinguish between Technical Knowledge and Interview Communication/Behavior.\n"
            f"   - If Technical Score is low (< 50) due to brief, invalid, or off-topic answers: DO NOT praise 'solid foundational competency' or 'strong practical knowledge'. State clearly that the candidate showed familiarity with some areas, but the interview contained insufficient substantive responses to reliably assess deeper technical competence.\n"
            f"   - If Communication Score is low (< 60) or unprofessional words were used: Explicitly state that weaknesses in communication structure, responsiveness, or professional language significantly affected the overall interview performance.\n"
            f"   - If Technical Score is high (>= 75) but Communication is low (< 60): Highlight strong technical domain depth (e.g., vector search, APIs) while explicitly noting communication/presentation gaps.\n"
            f"   - If both Technical and Communication are strong (>= 75): Highlight exceptional technical competence paired with clear, structured, and professional delivery.\n"
            f"2. Strengths list MUST NOT contradict the scores or behavior:\n"
            f"   - NEVER include 'clear communication' or 'structured approach' if communication score is low (< 60).\n"
            f"   - NEVER include 'strong technical depth' if technical score is low (< 50).\n"
            f"3. Return ONLY a valid JSON object matching this schema strictly:\n"
            f"{{\n"
            f'  "summary": "<3-5 sentence coherent executive summary calibrated with scores>",\n'
            f'  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],\n'
            f'  "gaps": ["<knowledge gap or communication improvement area 1>", "<gap 2>"],\n'
            f'  "next": ["<recommended next learning step 1>", "<step 2>", "<step 3>"]\n'
            f"}}"
        )

        base_feedback = None
        try:
            llm = get_llm(temperature=0.3)
            response = llm.invoke(prompt)
            raw_content = response.content.strip()
            match = re.search(r"\{.*\}", raw_content, re.DOTALL)
            if match:
                feedback = json.loads(match.group(0))
                if all(k in feedback for k in ["summary", "strengths", "gaps", "next"]):
                    if len(feedback["strengths"]) > 0 and len(feedback["gaps"]) > 0 and len(feedback["next"]) > 0:
                        base_feedback = feedback
        except Exception as e:
            logger.warning(f"LLM Feedback generation failed: {e}. Using deterministic feedback fallback.")

        if not base_feedback:
            base_feedback = self._build_calibrated_fallback(
                name=name,
                days_str=days_str,
                technical_score=technical_score,
                communication_score=communication_score,
                behavior_assessment=behavior_assessment
            )

        # Enrich feedback with behavior and composite scores
        base_feedback["behavior"] = behavior_assessment.model_dump()
        base_feedback["technical_score"] = technical_score
        base_feedback["communication_score"] = communication_score
        base_feedback["overall_score"] = overall_score

        return base_feedback

    def _build_calibrated_fallback(
        self,
        name: str,
        days_str: str,
        technical_score: int,
        communication_score: int,
        behavior_assessment: Any
    ) -> Dict[str, Any]:
        """
        Construct calibrated fallback feedback tailored to candidate score bands to avoid contradictions.
        """
        # Case A: Strong Technical + Strong Communication
        if technical_score >= 70 and communication_score >= 70:
            return {
                "summary": (
                    f"{name} demonstrated exceptional technical competence and strong domain depth across the evaluated AI curriculum modules "
                    f"({days_str}), complemented by clear, structured, and professional communication throughout the interview."
                ),
                "strengths": [
                    "Strong conceptual understanding of dense vector embeddings and semantic search pipelines",
                    "Familiarity with FastAPI backend integration and asynchronous LLM streaming protocols",
                    "Clear communication and structured approach to system architectural trade-offs"
                ],
                "gaps": [
                    "Could provide deeper mathematical rigor on vector distance metrics and index clustering trade-offs",
                    "Opportunity to demonstrate more hands-on production failure recovery and observability in multi-agent workflows"
                ],
                "next": [
                    "Deep dive into advanced LangGraph state checkpointing and human-in-the-loop validation patterns",
                    "Implement end-to-end telemetry with Prometheus and OpenTelemetry for latency and hallucination monitoring",
                    "Experiment with hybrid search tuning combining BM25 keyword matching with dense embeddings"
                ]
            }

        # Case B: Strong Technical + Poor Communication / Hesitant
        if technical_score >= 70 and communication_score < 70:
            return {
                "summary": (
                    f"{name} demonstrated strong technical understanding in several evaluated AI curriculum areas ({days_str}), "
                    f"particularly vector search and backend APIs. However, the interview revealed weaknesses in communication structure, "
                    f"responsiveness, and professional interview presentation, which significantly affected the overall interview performance."
                ),
                "strengths": [
                    "Solid conceptual familiarity with backend AI architecture and data retrieval concepts",
                    "Accurate identification of key tools and framework components across curriculum modules",
                    "Demonstrated potential for technical problem solving in core engineering areas"
                ],
                "gaps": [
                    "Answers lacked structured explanations, contextual reasoning, and systematic technical delivery",
                    "Need to develop professional interview presence, concise articulation, and direct responsiveness"
                ],
                "next": [
                    "Practice STAR (Situation, Task, Action, Result) response frameworks for technical interviews",
                    "Refine explanations of complex architectural trade-offs in structured, step-by-step formats",
                    "Implement practical multi-agent projects with documented design decisions and diagrams"
                ]
            }

        # Case C: Low Technical + Good / Professional Communication
        if technical_score < 50 and communication_score >= 60:
            return {
                "summary": (
                    f"{name} maintained a professional and courteous interview demeanor throughout the session. However, "
                    f"the candidate demonstrated limited technical depth across the evaluated AI curriculum areas ({days_str}), "
                    f"indicating substantial foundational knowledge gaps that require further study and hands-on development."
                ),
                "strengths": [
                    "Professional, polite, and receptive communication style during technical questioning",
                    "Clear articulation and willingness to acknowledge knowledge boundaries",
                    "Good conversational engagement and professional conduct"
                ],
                "gaps": [
                    "Limited hands-on technical understanding of vector indexing, embeddings, and retrieval mechanics",
                    "Gaps in backend API integration patterns and asynchronous state management workflows"
                ],
                "next": [
                    "Revisit curriculum modules focusing on hands-on labs with ChromaDB and LangGraph",
                    "Build full-stack AI prototypes with FastAPI and structured database persistence",
                    "Study distributed systems fundamentals and vector similarity mathematics"
                ]
            }

        # Case D: Low Technical + Low Communication (e.g. one-word answers, bad test responses, profanity)
        if technical_score < 50 and communication_score < 60:
            return {
                "summary": (
                    f"{name} demonstrated evidence of familiarity with several technical areas, but the interview contained "
                    f"insufficient substantive responses to reliably assess deeper technical competence across the evaluated modules ({days_str}). "
                    f"Additionally, the interview revealed notable weaknesses in communication structure, responsiveness, and interview conduct, "
                    f"which significantly impacted the overall evaluation."
                ),
                "strengths": [
                    "Basic awareness of core AI concepts and terminology",
                    "Initial exposure to modern AI engineering topics and tools",
                    "Potential for growth through structured curriculum revisitation and hands-on practice"
                ],
                "gaps": [
                    "Interview responses lacked technical substance, detail, and concrete architectural reasoning",
                    "Significant weaknesses in communication structure, responsiveness, and professional interview conduct"
                ],
                "next": [
                    "Thoroughly review the complete 31-day AI engineering curriculum from foundational concepts",
                    "Complete guided coding projects to build demonstrable hands-on engineering competence",
                    "Practice professional communication standards and structured technical articulation"
                ]
            }

        # Case E: Moderate / Intermediate performance
        return {
            "summary": (
                f"{name} demonstrated developing competency across evaluated AI curriculum modules ({days_str}). "
                f"The candidate showed general familiarity with core AI engineering concepts, with opportunities to deepen "
                f"technical precision and communication structure for senior-level execution."
            ),
            "strengths": [
                "Working familiarity with primary curriculum concepts and AI tooling ecosystems",
                "Ability to discuss high-level system flows and API integration patterns",
                "Demonstrated foundational understanding of data retrieval workflows"
            ],
            "gaps": [
                "Need deeper explanations of system trade-offs, edge cases, and optimization bottlenecks",
                "Can improve conciseness and precision in technical descriptions"
            ],
            "next": [
                "Deepen hands-on practice with vector database tuning and hybrid search patterns",
                "Implement robust error handling and observability in multi-agent LangGraph pipelines",
                "Conduct mock architectural design reviews to sharpen technical delivery"
            ]
        }

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for FeedbackGenerator.
        """
        candidate_info = state.get("candidate_signals", {}) or {}
        # Merge member info if present
        profile = state.get("candidate_profile", {}) or {}
        if profile.get("member"):
            candidate_info.setdefault("candidate_name", profile["member"].get("name"))
            candidate_info.setdefault("job_role", profile["member"].get("jobRole"))

        evaluations = state.get("evaluations", [])
        covered_days = state.get("covered_days", [])
        history = state.get("conversation_history", [])

        feedback = self.generate_feedback(
            candidate_info=candidate_info,
            evaluations=evaluations,
            covered_days=covered_days,
            conversation_history=history
        )

        closing_reply = (
            "Thank you for completing the technical interview! Your interview is now finished. "
            "A structured evaluation report detailing your strengths, technical gaps, communication style, and recommended next steps has been generated."
        )

        return {
            "final_feedback": feedback,
            "latest_reply": closing_reply,
            "is_complete": True
        }
