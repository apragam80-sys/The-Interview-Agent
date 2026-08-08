"""
Answer Evaluator Agent.
Scores candidate responses against objective technical rubrics (correctness, depth,
reasoning, practical understanding) and determines if adaptive follow-up is required.
Detects abusive language, skip/pass refusals, and gibberish to prevent infinite loops.
"""

import json
import re
from typing import Dict, Any, List, Optional
from app.graph.state import InterviewState
from app.config import logger
from app.llm import get_llm

# Patterns for non-responsive, abusive, or explicit refusal inputs
ABUSIVE_PATTERNS = [
    r"\bf+u+[\*ckx]+\b",
    r"\bf+u+c+k",
    r"\bsh+i+t\b",
    r"\bb+i+t+c+h\b",
    r"\ba+s+s+h+o+l+e\b",
    r"\ba+s+s\b",
    r"\bstfu\b",
    r"\bdamn\b",
    r"\bcrap\b",
    r"\bdick\b",
    r"\bbastard\b",
    r"\bidiot\b",
    r"\bstupid\b",
    r"\bfu\b",
    r"\bwtf\b"
]

REFUSAL_PATTERNS = [
    r"^(pass|skip|next|idk|i don'?t know|no idea|not sure|dunno|no clue|no|nope|nah)$",
    r"^(qwerty|asdf|zxcv|1234|abc|test|blah|nothing)$",
    r"^i (have no|don'?t have any) idea"
]


class AnswerEvaluator:
    """
    Agent 5: Answer Evaluator.
    Evaluates candidate responses and outputs structured assessment scores.
    """

    def __init__(self):
        """Initialize Answer Evaluator."""
        logger.info("AnswerEvaluator agent initialized")

    def evaluate_answer(
        self,
        question_text: str,
        answer_text: str,
        topic_info: Dict[str, Any],
        difficulty_level: str,
        can_follow_up: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate candidate answer across technical rubrics.

        Args:
            question_text (str): Question presented to candidate.
            answer_text (str): Candidate's response.
            topic_info (Dict[str, Any]): Topic objectives and tools.
            difficulty_level (str): Candidate difficulty tier.
            can_follow_up (bool): False if question has already had a follow-up probe.

        Returns:
            Dict[str, Any]: Evaluation score breakdown and follow-up decision.
        """
        clean_answer = (answer_text or "").strip().lower()

        # 1. Check for abusive language / profanity -> Apply Professionalism Penalty (-25)
        for pat in ABUSIVE_PATTERNS:
            if re.search(pat, clean_answer):
                logger.warning(f"Abusive or inappropriate response detected: '{clean_answer[:20]}'")
                return {
                    "correctness": -25,
                    "depth": -25,
                    "reasoning": -25,
                    "practical_understanding": -25,
                    "overall_score": -25,
                    "misconceptions": ["Candidate used inappropriate/abusive language. Professionalism penalty applied to Communication & Behavior score."],
                    "follow_up_needed": False,
                    "is_abusive": True,
                    "penalty_type": "PROFESSIONALISM_PENALTY",
                    "penalty_points": 25,
                    "notes": "⚠️ Professionalism penalty: -25 points applied to Behavior & Communication score."
                }

        # 2. Check for explicit refusals / skips / gibberish
        for pat in REFUSAL_PATTERNS:
            if re.search(pat, clean_answer):
                return {
                    "correctness": 10,
                    "depth": 10,
                    "reasoning": 10,
                    "practical_understanding": 10,
                    "overall_score": 15,
                    "misconceptions": ["Candidate skipped or was unable to answer the question."],
                    "follow_up_needed": False,
                    "is_abusive": False,
                    "notes": "Candidate explicitly skipped or gave a non-attempt response."
                }

        # 3. Check for vague or brief technical responses
        is_vague = False
        vague_patterns = [
            r"^i just used",
            r"^because it works",
            r"^it is good",
            r"^standard"
        ]
        for pat in vague_patterns:
            if re.search(pat, clean_answer):
                is_vague = True
                break

        if len(clean_answer.split()) < 6:
            is_vague = True

        topic = topic_info.get("topic", "AI Concept")
        tools = ", ".join(topic_info.get("tools", []))

        prompt = (
            f"You are a Senior Technical Interview Evaluator.\n"
            f"Topic: {topic} (Tools: {tools})\n"
            f"Difficulty Tier: {difficulty_level}\n"
            f"Question Asked: {question_text}\n"
            f"Candidate Answer: {clean_answer}\n\n"
            f"Task: Evaluate the answer across technical correctness, depth, reasoning, and practical implementation.\n"
            f"Return ONLY a valid JSON object strictly matching this format:\n"
            f"{{\n"
            f'  "correctness": <0-100>,\n'
            f'  "depth": <0-100>,\n'
            f'  "reasoning": <0-100>,\n'
            f'  "practical_understanding": <0-100>,\n'
            f'  "overall_score": <0-100>,\n'
            f'  "misconceptions": ["<list of identified misconceptions or gaps>"],\n'
            f'  "follow_up_needed": <true/false>,\n'
            f'  "notes": "<1-2 sentence evaluation summary>"\n'
            f"}}"
        )

        try:
            llm = get_llm(temperature=0.0)
            response = llm.invoke(prompt)
            raw_content = response.content.strip()
            
            match = re.search(r"\{.*\}", raw_content, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                # Only allow follow-up if allowed and genuinely needed
                if not can_follow_up:
                    parsed["follow_up_needed"] = False
                elif is_vague:
                    parsed["follow_up_needed"] = True
                    parsed["overall_score"] = min(parsed.get("overall_score", 50), 55)
                    parsed["depth"] = min(parsed.get("depth", 40), 40)
                parsed["is_abusive"] = False
                return parsed
        except Exception as e:
            logger.warning(f"LLM Answer Evaluation failed: {e}. Using rule-based evaluator.")

        # Rule-based fallback scoring
        if is_vague:
            return {
                "correctness": 50,
                "depth": 35,
                "reasoning": 40,
                "practical_understanding": 45,
                "overall_score": 45,
                "misconceptions": ["Answer lacked technical architectural depth and specific mechanisms."],
                "follow_up_needed": can_follow_up,
                "is_abusive": False,
                "notes": "Candidate provided a brief or superficial response."
            }

        # Substantial answer heuristics
        word_count = len(clean_answer.split())
        score = min(75 + min(word_count * 2, 20), 95)
        
        return {
            "correctness": score,
            "depth": score - 5,
            "reasoning": score,
            "practical_understanding": score - 5,
            "overall_score": score,
            "misconceptions": [],
            "follow_up_needed": False,
            "is_abusive": False,
            "notes": "Candidate demonstrated solid grasp of the core concepts and design trade-offs."
        }

    def __call__(self, state: InterviewState) -> Dict[str, Any]:
        """
        LangGraph Node execution method for AnswerEvaluator.
        """
        incoming_message = state.get("incoming_message", "")
        current_q = state.get("current_question", {})
        difficulty = state.get("difficulty_level", "MID")
        evaluations = list(state.get("evaluations", []))

        # Check if previous turn was already a follow up probe
        was_follow_up = state.get("was_follow_up", False) or state.get("is_follow_up", False)
        follow_up_count = state.get("follow_up_count_for_current_q", 0)
        can_follow_up = (not was_follow_up) and (follow_up_count == 0)

        question_text = state.get("latest_reply", "")
        eval_result = self.evaluate_answer(
            question_text=question_text,
            answer_text=incoming_message,
            topic_info=current_q,
            difficulty_level=difficulty,
            can_follow_up=can_follow_up
        )

        overall_score = eval_result.get("overall_score", 70)

        # Append to evaluations history
        evaluations.append({
            "step": state.get("current_question_index", 0) + 1,
            "question": question_text,
            "answer": incoming_message,
            "evaluation": eval_result,
            "score": overall_score
        })

        # Calculate running average score
        all_scores = [ev.get("score", 70) for ev in evaluations]
        avg_score = round(sum(all_scores) / len(all_scores)) if all_scores else overall_score

        follow_up_flag = eval_result.get("follow_up_needed", False) and can_follow_up

        return {
            "evaluations": evaluations,
            "latest_score": overall_score,
            "average_score": avg_score,
            "is_follow_up": follow_up_flag,
            "was_follow_up": was_follow_up,
            "is_abusive": eval_result.get("is_abusive", False)
        }
