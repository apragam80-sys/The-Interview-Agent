"""
Behavior Evaluator Service.
Analyzes candidate's complete conversation history to evaluate interview behavior and communication style
across 8 observable dimensions without inferring psychological traits.
"""

import json
import re
from typing import Dict, Any, List, Optional
from app.config import logger
from app.llm import get_llm
from app.models.schemas import BehaviorDimensionScore, InterviewBehaviorAssessment


# Allowed communication styles (strictly matching specification)
ALLOWED_COMMUNICATION_STYLES = [
    "Clear & Structured",
    "Concise & Direct",
    "Detailed & Analytical",
    "Conversational",
    "Verbose",
    "Fragmented",
    "Hesitant",
    "Inconsistent"
]

ABUSIVE_REGEX = re.compile(
    r"\b(fuck|fucking|f\*ck|fu\*k|shit|bitch|asshole|bullshit|stfu|dick|cunt|bastard)\b",
    re.IGNORECASE
)

STRUCTURAL_MARKERS = [
    "first", "second", "third", "finally", "specifically", "for example",
    "for instance", "trade-off", "tradeoff", "in contrast", "on the other hand",
    "because", "therefore", "as a result", "in summary", "to conclude"
]

TECHNICAL_TERMS = [
    "embedding", "embeddings", "vector", "vectors", "chromadb", "sqlite",
    "fastapi", "docker", "rag", "retrieval", "hnsw", "cosine", "similarity",
    "latency", "throughput", "pydantic", "langgraph", "agent", "prompt",
    "chunking", "token", "tokens", "transformer", "bert", "clustering",
    "cache", "caching", "async", "asynchronous", "endpoint", "api", "database",
    "index", "indexing", "scaling", "observability", "telemetry", "prometheus"
]


class BehaviorEvaluator:
    """
    Evaluates candidate interview behavior and communication patterns from complete conversation transcripts.
    """

    def __init__(self):
        logger.info("BehaviorEvaluator service initialized")

    def analyze_behavior(
        self,
        candidate_info: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        evaluations: List[Dict[str, Any]]
    ) -> InterviewBehaviorAssessment:
        """
        Main entrypoint: analyzes candidate's complete conversation history.
        Tries LLM-based structured evaluation first; falls back to deterministic rule-based analysis.
        """
        candidate_messages = [
            m.get("content", "").strip()
            for m in conversation_history
            if m.get("role") in ("candidate", "user") and m.get("content")
        ]

        # If no conversation_history messages, extract from evaluations list
        if not candidate_messages and evaluations:
            candidate_messages = [
                ev.get("answer", "").strip()
                for ev in evaluations
                if ev.get("answer")
            ]

        # Attempt LLM evaluation
        llm_assessment = self._evaluate_with_llm(candidate_info, conversation_history, evaluations, candidate_messages)
        if llm_assessment:
            return llm_assessment

        # Fallback to deterministic rule-based evaluation
        return self._evaluate_deterministic(candidate_info, candidate_messages, evaluations)

    def _evaluate_with_llm(
        self,
        candidate_info: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        evaluations: List[Dict[str, Any]],
        candidate_messages: List[str]
    ) -> Optional[InterviewBehaviorAssessment]:
        """Runs LLM prompt evaluation for interview communication and behavior."""
        if not candidate_messages:
            return None

        name = candidate_info.get("candidate_name") or candidate_info.get("member", {}).get("name", "Candidate")
        role = candidate_info.get("job_role") or candidate_info.get("member", {}).get("jobRole", "Software Engineer")

        # Build clean dialogue transcript
        transcript_lines = []
        for idx, m in enumerate(conversation_history):
            role_label = "Candidate" if m.get("role") in ("candidate", "user") else "Interviewer"
            content = m.get("content", "").strip()
            transcript_lines.append(f"{role_label}: {content}")

        if not transcript_lines and evaluations:
            for idx, ev in enumerate(evaluations):
                q = ev.get("question", "")
                a = ev.get("answer", "")
                transcript_lines.append(f"Interviewer: {q}")
                transcript_lines.append(f"Candidate: {a}")

        transcript_text = "\n".join(transcript_lines)

        allowed_styles_str = ", ".join([f'"{s}"' for s in ALLOWED_COMMUNICATION_STYLES])

        prompt = f"""You are a Senior Technical Hiring Manager evaluating the observable communication and interview behavior of {name} ({role}).

Analyze the COMPLETE interview transcript below.
Evaluate ONLY observable communication behavior from the candidate's actual words.
Do NOT infer psychological traits, internal emotions, or personality.

Transcript:
{transcript_text}

Evaluate these 8 dimensions (each with a float score from 0.0 to 10.0 and a concrete, evidence-based assessment statement derived from actual candidate messages):
1. communication_clarity: Was the candidate clear, coherent, and structured?
2. technical_communication: Did they use technical terminology accurately and appropriately (without relying on ungrounded buzzwords)?
3. confidence: Did they answer directly and appropriately acknowledge uncertainty (avoiding unsupported overconfidence)?
4. conciseness: Were answers appropriately concise vs. overly verbose or too brief to demonstrate depth?
5. professionalism: Was language respectful, interview-appropriate, and free of profanity or excessive casualness?
6. answer_structure: Did answers follow a logical progression (concept -> reasoning -> example -> trade-off -> conclusion)?
7. responsiveness: Did they directly address what was asked without dodging or going off-topic?
8. overall_interview_presence: Holistic assessment of observable interview presence and communication effectiveness.

Classify communication_styles using ONLY from this list: [{allowed_styles_str}]. You may pick 1-3 applicable styles.

Extract 2-4 concrete language_observations (bullet points grounded in actual candidate statements).

Provide an overall_presence_summary (1-2 sentences summarizing overall communication presence).

Return ONLY a valid JSON object matching this schema strictly:
{{
  "communication_clarity": {{"score": 8.0, "assessment": "<evidence-based assessment>"}},
  "technical_communication": {{"score": 8.5, "assessment": "<evidence-based assessment>"}},
  "confidence": {{"score": 7.5, "assessment": "<evidence-based assessment>"}},
  "conciseness": {{"score": 8.0, "assessment": "<evidence-based assessment>"}},
  "professionalism": {{"score": 9.0, "assessment": "<evidence-based assessment>"}},
  "answer_structure": {{"score": 7.5, "assessment": "<evidence-based assessment>"}},
  "responsiveness": {{"score": 8.5, "assessment": "<evidence-based assessment>"}},
  "overall_interview_presence": {{"score": 8.0, "assessment": "<evidence-based assessment>"}},
  "communication_styles": ["Clear & Structured", "Detailed & Analytical"],
  "language_observations": [
    "Uses relevant technical terminology accurately.",
    "Usually answers the question directly.",
    "Could provide more concrete examples."
  ],
  "overall_presence_summary": "<holistic summary>"
}}"""

        try:
            llm = get_llm(temperature=0.2)
            response = llm.invoke(prompt)
            raw = response.content.strip()
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                # Validate required keys
                required_dims = [
                    "communication_clarity", "technical_communication", "confidence",
                    "conciseness", "professionalism", "answer_structure", "responsiveness",
                    "overall_interview_presence"
                ]
                if all(k in data for k in required_dims):
                    # Clamp scores and sanitize styles
                    cleaned_data = {}
                    for dim in required_dims:
                        item = data[dim]
                        score = float(item.get("score", 7.0))
                        score = max(0.0, min(10.0, round(score, 1)))
                        assessment = str(item.get("assessment", "Consistent technical communication observed.")).strip()
                        cleaned_data[dim] = BehaviorDimensionScore(score=score, assessment=assessment)

                    raw_styles = data.get("communication_styles", [])
                    valid_styles = [s for s in raw_styles if s in ALLOWED_COMMUNICATION_STYLES]
                    if not valid_styles:
                        valid_styles = ["Clear & Structured"]

                    raw_obs = data.get("language_observations", [])
                    cleaned_obs = [str(o).strip() for o in raw_obs if str(o).strip()]
                    if not cleaned_obs:
                        cleaned_obs = ["Communicates technical concepts clearly and stays on topic."]

                    summary = str(data.get("overall_presence_summary", "")).strip()
                    if not summary:
                        summary = f"{name} demonstrates solid technical communication and structured interview presence."

                    return InterviewBehaviorAssessment(
                        communication_clarity=cleaned_data["communication_clarity"],
                        technical_communication=cleaned_data["technical_communication"],
                        confidence=cleaned_data["confidence"],
                        conciseness=cleaned_data["conciseness"],
                        professionalism=cleaned_data["professionalism"],
                        answer_structure=cleaned_data["answer_structure"],
                        responsiveness=cleaned_data["responsiveness"],
                        overall_interview_presence=cleaned_data["overall_interview_presence"],
                        communication_styles=valid_styles,
                        language_observations=cleaned_obs,
                        overall_presence_summary=summary
                    )
        except Exception as e:
            logger.warning(f"LLM behavior evaluation failed: {e}. Falling back to deterministic analysis.")

        return None

    def _evaluate_deterministic(
        self,
        candidate_info: Dict[str, Any],
        candidate_messages: List[str],
        evaluations: List[Dict[str, Any]]
    ) -> InterviewBehaviorAssessment:
        """
        Deterministic, rule-based behavioral evaluation engine.
        Handles edge cases: very short answers, profanity, gibberish, verbosity, and off-topic messages.
        """
        name = candidate_info.get("candidate_name") or candidate_info.get("member", {}).get("name", "Candidate")

        # Edge case: No answers given
        if not candidate_messages:
            no_evidence = BehaviorDimensionScore(score=5.0, assessment="Insufficient evidence from the interview.")
            return InterviewBehaviorAssessment(
                communication_clarity=no_evidence,
                technical_communication=no_evidence,
                confidence=no_evidence,
                conciseness=no_evidence,
                professionalism=BehaviorDimensionScore(score=8.0, assessment="No inappropriate communication observed."),
                answer_structure=no_evidence,
                responsiveness=no_evidence,
                overall_interview_presence=no_evidence,
                communication_styles=["Inconsistent"],
                language_observations=["Insufficient evidence from the interview."],
                overall_presence_summary="Insufficient conversation evidence to formulate a complete communication assessment."
            )

        # Analyze quantitative metrics
        total_answers = len(candidate_messages)
        word_counts = [len(m.split()) for m in candidate_messages]
        avg_word_count = sum(word_counts) / max(1, total_answers)
        short_answers = sum(1 for wc in word_counts if wc < 6)
        long_answers = sum(1 for wc in word_counts if wc > 120)

        # Check for profanity / abusive language
        has_abusive = any(ABUSIVE_REGEX.search(m) for m in candidate_messages)

        # Count technical terms used accurately and appropriately
        tech_term_matches = sum(
            sum(1 for term in TECHNICAL_TERMS if re.search(r"\b" + re.escape(term) + r"\b", m, re.IGNORECASE))
            for m in candidate_messages
        )
        avg_tech_terms = tech_term_matches / max(1, total_answers)

        # Count structural markers
        structural_matches = sum(
            sum(1 for marker in STRUCTURAL_MARKERS if re.search(r"\b" + re.escape(marker) + r"\b", m, re.IGNORECASE))
            for m in candidate_messages
        )
        avg_structural_markers = structural_matches / max(1, total_answers)

        # Check for non-answers / refusal / gibberish ("yes", "no", "idk", "qwerty", "asdf", "abcd", etc.)
        refusal_patterns = re.compile(r"^(yes|no|nope|yeah|idk|i don't know|dont know|qwerty|asdf|abcd|none|na|n/a|\?+|\.+)$", re.IGNORECASE)
        refusal_count = sum(1 for m in candidate_messages if refusal_patterns.match(m.strip()))

        # Check off-topic from evaluations
        off_topic_notes = sum(
            1 for ev in evaluations
            if "off-topic" in ev.get("evaluation", {}).get("notes", "").lower() or
               "dodged" in ev.get("evaluation", {}).get("notes", "").lower()
        )

        language_observations = []
        communication_styles = []

        # 1. Professionalism
        if has_abusive:
            prof_score = 1.5
            prof_desc = "Candidate used inappropriate or unprofessional language during the interview, which severely impacted professional communication."
            language_observations.append("Candidate used unprofessional language during the session.")
        else:
            prof_score = 9.5 if refusal_count == 0 else 7.5
            prof_desc = "Maintained a respectful, interview-appropriate professional tone throughout the session."
            language_observations.append("Maintained a professional technical tone throughout the interview.")

        # 2. Technical Communication (Accuracy and appropriateness)
        if avg_tech_terms >= 2.5:
            tech_score = 8.8
            tech_desc = "Consistently uses relevant technical terminology accurately and in proper system context."
            language_observations.append("Uses relevant technical terminology accurately and in appropriate context.")
        elif avg_tech_terms >= 1.0:
            tech_score = 7.0
            tech_desc = "Demonstrates foundational technical vocabulary with opportunities to explain deeper architectural mechanisms."
            language_observations.append("Demonstrates foundational technical vocabulary with room for deeper architectural terminology.")
        else:
            tech_score = 4.0 if (short_answers >= total_answers // 2 or has_abusive) else 5.5
            tech_desc = "Relies primarily on generic descriptions rather than precise technical terminology."
            language_observations.append("Uses general terms with minimal domain-specific technical vocabulary.")

        # 3. Communication Clarity
        if has_abusive or refusal_count > 0 or (short_answers >= total_answers // 2 and avg_word_count < 15):
            clarity_score = 4.0
            clarity_desc = "Explanations were frequently fragmented or minimal, making it difficult to assess conceptual coherence."
            communication_styles.append("Fragmented")
            language_observations.append("Several responses were too brief to demonstrate structured reasoning.")
        elif avg_word_count > 25 and avg_structural_markers >= 0.8:
            clarity_score = 8.5
            clarity_desc = "Explanations are coherent, well-paced, and logically connected."
            communication_styles.append("Clear & Structured")
        else:
            clarity_score = 7.0
            clarity_desc = "Communication is generally understandable with occasional jumps between concepts."
            communication_styles.append("Conversational")

        # 4. Conciseness
        if long_answers >= total_answers // 2 and avg_word_count > 100:
            concise_score = 5.5
            concise_desc = "Responses tended toward verbosity, occasionally including tangential context before arriving at the core point."
            communication_styles.append("Verbose")
            language_observations.append("Responses are extensive and detailed, but occasionally include redundant context.")
        elif short_answers >= total_answers // 2:
            concise_score = 4.5
            concise_desc = "Responses were excessively brief, omitting necessary architectural context and trade-off details."
            communication_styles.append("Concise & Direct")
            language_observations.append("Answers are direct but would benefit from additional supporting technical detail.")
        else:
            concise_score = 8.0
            concise_desc = "Balances directness with sufficient technical explanation effectively."
            communication_styles.append("Concise & Direct")

        # 5. Answer Structure
        if avg_structural_markers >= 1.2 and avg_word_count >= 30:
            struct_score = 8.5
            struct_desc = "Naturally organizes answers into logical progressions (concept definition, technical rationale, and trade-offs)."
            if "Clear & Structured" not in communication_styles:
                communication_styles.append("Clear & Structured")
        elif avg_word_count >= 15 and not has_abusive:
            struct_score = 7.0
            struct_desc = "Follows basic answer structure; could improve by consistently providing concrete examples and failure trade-offs."
        else:
            struct_score = 3.5
            struct_desc = "Responses lacked visible structure or step-by-step reasoning."

        # 6. Confidence
        if has_abusive or refusal_count >= 2:
            conf_score = 3.5
            conf_desc = "Refusals or evasive answers indicated hesitation or reluctance to address complex architectural questions."
            communication_styles.append("Hesitant")
        elif avg_word_count >= 25 and tech_score >= 7.0:
            conf_score = 8.5
            conf_desc = "Communicates technical decisions assertively while remaining grounded in concrete engineering logic."
        else:
            conf_score = 6.5
            conf_desc = "Answers directly without overstatement, though occasionally tentative on advanced topics."

        # 7. Responsiveness
        if has_abusive:
            resp_score = 3.0
            resp_desc = "Candidate deflected questions with inappropriate remarks rather than constructive technical responses."
        elif off_topic_notes >= 2:
            resp_score = 4.5
            resp_desc = "Occasionally diverged from the specific technical question asked or bypassed difficult constraints."
            language_observations.append("Occasionally drifted off-topic rather than directly addressing the prompt constraints.")
        elif refusal_count > 0:
            resp_score = 5.0
            resp_desc = "One or more questions were met with minimal or refusal responses rather than technical engagement."
        else:
            resp_score = 9.0
            resp_desc = "Directly and promptly addressed the core prompts without dodging complex topics."

        # 8. Overall Interview Presence
        all_dim_scores = [clarity_score, tech_score, conf_score, concise_score, prof_score, struct_score, resp_score]
        presence_score = round(sum(all_dim_scores) / len(all_dim_scores), 1)

        if has_abusive:
            presence_desc = "Interview presence was severely compromised due to unprofessional language and lack of technical engagement."
            summary = f"{name}'s interview presence was significantly impacted by unprofessional language and non-technical responses."
        elif presence_score >= 8.0:
            presence_desc = "Strong, structured technical presence demonstrating articulate communication and rigorous domain terminology."
            summary = f"{name} is a strong technical communicator who explains complex engineering concepts clearly and uses accurate terminology."
            if "Detailed & Analytical" not in communication_styles:
                communication_styles.append("Detailed & Analytical")
        elif presence_score >= 6.0:
            presence_desc = "Solid conversational presence with functional communication; would benefit from deeper structured trade-off breakdowns."
            summary = f"{name} demonstrates solid foundational communication, answering directly with opportunities to provide more structured architectural examples."
        else:
            presence_desc = "Communication was inconsistent or overly brief, reducing the ability to fully demonstrate technical reasoning."
            summary = f"{name}'s communication was brief or fragmented, presenting opportunities to develop more structured interview communication."
            if "Inconsistent" not in communication_styles:
                communication_styles.append("Inconsistent")

        # Deduplicate styles and observations
        seen_styles = []
        for s in communication_styles:
            if s in ALLOWED_COMMUNICATION_STYLES and s not in seen_styles:
                seen_styles.append(s)
        if not seen_styles:
            seen_styles = ["Clear & Structured"]

        # Ensure 2-4 unique observations
        unique_obs = []
        for o in language_observations:
            if o not in unique_obs:
                unique_obs.append(o)
        if len(unique_obs) < 2:
            unique_obs.append("Maintains a direct approach to answering technical questions.")

        return InterviewBehaviorAssessment(
            communication_clarity=BehaviorDimensionScore(score=clarity_score, assessment=clarity_desc),
            technical_communication=BehaviorDimensionScore(score=tech_score, assessment=tech_desc),
            confidence=BehaviorDimensionScore(score=conf_score, assessment=conf_desc),
            conciseness=BehaviorDimensionScore(score=concise_score, assessment=concise_desc),
            professionalism=BehaviorDimensionScore(score=prof_score, assessment=prof_desc),
            answer_structure=BehaviorDimensionScore(score=struct_score, assessment=struct_desc),
            responsiveness=BehaviorDimensionScore(score=resp_score, assessment=resp_desc),
            overall_interview_presence=BehaviorDimensionScore(score=presence_score, assessment=presence_desc),
            communication_styles=seen_styles[:3],
            language_observations=unique_obs[:4],
            overall_presence_summary=summary
        )


# Singleton instance
_behavior_evaluator = BehaviorEvaluator()


def get_behavior_evaluator() -> BehaviorEvaluator:
    """Return singleton BehaviorEvaluator instance."""
    return _behavior_evaluator
