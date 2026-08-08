"""
Pydantic Schemas for Adaptive AI Interview Platform.
Defines candidate profiles, curriculum structure, API contract requests/responses,
database persistence models, and internal evaluation schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Candidate Profile Schemas (Strictly matching candidates.json)
# ---------------------------------------------------------------------------
class CandidateMember(BaseModel):
    """Member identification and background metadata."""
    id: str = Field(..., description="Unique candidate ID, e.g. CAND-001")
    name: str = Field(..., description="Candidate full name")
    jobRole: str = Field(..., description="Current or target job role")
    yearsExperience: int = Field(..., description="Years of professional experience")
    education: str = Field(..., description="Educational background")
    status: str = Field(default="COMPLETED", description="Cohort status")


class CandidateMission(BaseModel):
    """Historical mission record from curriculum."""
    day: int = Field(..., description="Curriculum day number")
    title: str = Field(..., description="Mission title")
    passed: Optional[bool] = Field(default=None, description="Whether mission was passed")
    skipped: Optional[bool] = Field(default=None, description="Whether mission was skipped")
    attempts: Optional[int] = Field(default=1, description="Number of attempts taken")


class CandidateSignals(BaseModel):
    """Aggregated commitment and performance signals."""
    commitDays: int = Field(..., description="Total days committed")
    missionsCompleted: int = Field(..., description="Total completed missions")
    missionsFirstTry: int = Field(..., description="Missions passed on first attempt")


class CandidateProfile(BaseModel):
    """Full candidate profile schema matching candidates.json."""
    member: CandidateMember
    missions: List[CandidateMission] = Field(default_factory=list)
    signals: CandidateSignals


class CandidateCollection(BaseModel):
    """Top-level container for candidates.json dataset."""
    candidates: List[CandidateProfile] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. Curriculum Schemas (Strictly matching curriculum.json)
# ---------------------------------------------------------------------------
class CurriculumModule(BaseModel):
    """Curriculum module specification."""
    n: int = Field(..., description="Module number (1-8)")
    title: str = Field(..., description="Module title")
    days: List[int] = Field(..., description="Day range or list of days included in module")


class CurriculumDay(BaseModel):
    """Single curriculum day learning specification."""
    day: int = Field(..., description="Day number (1-31)")
    title: str = Field(..., description="Topic title for the day")
    type: str = Field(..., description="Day type, e.g. SETUP, BUILD, CORE, CAPSTONE")
    tools: List[str] = Field(default_factory=list, description="Technologies and tools covered")
    objectives: List[str] = Field(default_factory=list, description="Key learning objectives")


class CurriculumSchema(BaseModel):
    """Top-level container for curriculum.json dataset."""
    cohort: str = Field(..., description="Cohort metadata description")
    modules: List[CurriculumModule] = Field(default_factory=list)
    days: List[CurriculumDay] = Field(default_factory=list)


class CurriculumChunk(BaseModel):
    """Structured text chunk prepared for vector store embeddings."""
    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. day-7-chunk-1")
    day: int = Field(..., description="Curriculum day number")
    module_n: int = Field(..., description="Module number")
    module_title: str = Field(..., description="Module title")
    day_title: str = Field(..., description="Day title")
    day_type: str = Field(..., description="Day type")
    tools: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    text_content: str = Field(..., description="Full text representation for semantic indexing")


# ---------------------------------------------------------------------------
# 3. API Contract Schemas (Strictly matching technical-spec(1).md)
# ---------------------------------------------------------------------------
class BehaviorDimensionScore(BaseModel):
    """Observable evaluation score and qualitative assessment for a single communication dimension."""
    score: float = Field(..., ge=0.0, le=10.0, description="Dimension score between 0.0 and 10.0")
    assessment: str = Field(..., description="Evidence-grounded qualitative assessment")


class InterviewBehaviorAssessment(BaseModel):
    """
    Structured behavioral and communication evaluation across 8 observable dimensions.
    Evaluates complete conversation history without inferring psychological traits.
    """
    communication_clarity: BehaviorDimensionScore = Field(
        ..., description="Clarity, structure, and coherence of candidate explanations"
    )
    technical_communication: BehaviorDimensionScore = Field(
        ..., description="Accuracy and appropriateness of technical terminology usage"
    )
    confidence: BehaviorDimensionScore = Field(
        ..., description="Directness and appropriate acknowledgment of uncertainty"
    )
    conciseness: BehaviorDimensionScore = Field(
        ..., description="Brevity vs. verbosity vs. depth trade-off in answers"
    )
    professionalism: BehaviorDimensionScore = Field(
        ..., description="Professional, respectful, interview-appropriate language"
    )
    answer_structure: BehaviorDimensionScore = Field(
        ..., description="Structure (concept -> reasoning -> example -> trade-off -> conclusion)"
    )
    responsiveness: BehaviorDimensionScore = Field(
        ..., description="Direct addressing of questions asked without going off-topic"
    )
    overall_interview_presence: BehaviorDimensionScore = Field(
        ..., description="Holistic assessment of observable interview presence"
    )
    communication_styles: List[str] = Field(
        default_factory=list,
        description="Classified styles from: Clear & Structured, Concise & Direct, Detailed & Analytical, Conversational, Verbose, Fragmented, Hesitant, Inconsistent"
    )
    language_observations: List[str] = Field(
        default_factory=list,
        description="Evidence-based bulleted observations of observable language patterns"
    )
    overall_presence_summary: str = Field(
        default="",
        description="Comprehensive summary statement of candidate interview presence"
    )


class FeedbackData(BaseModel):
    """
    Structured feedback schema returned on interview completion.
    Strictly requires: summary, strengths, gaps, next.
    Optionally enriched with behavioral assessment and composite scoring.
    """
    summary: str = Field(..., description="Comprehensive executive summary of the interview")
    strengths: List[str] = Field(..., description="List of identified candidate strengths")
    gaps: List[str] = Field(..., description="List of identified knowledge gaps and misconceptions")
    next: List[str] = Field(..., description="Actionable recommended next learning steps")
    behavior: Optional[InterviewBehaviorAssessment] = Field(
        default=None,
        description="Structured behavioral & communication assessment across 8 dimensions"
    )
    technical_score: Optional[int] = Field(
        default=None,
        description="Technical competency score (0-100)"
    )
    communication_score: Optional[int] = Field(
        default=None,
        description="Communication and behavioral score (0-100), calculated as average(8 dimensions) * 10"
    )
    overall_score: Optional[int] = Field(
        default=None,
        description="Composite overall score: round(0.70 * technical_score + 0.30 * communication_score)"
    )


class InterviewRequest(BaseModel):
    """
    Request schema for POST /api/interview.
    Turn 1: { "sessionId": "...", "candidate": { ... } }
    Turn N: { "sessionId": "...", "message": "..." }
    """
    sessionId: str = Field(..., description="Unique interview session identifier")
    candidate: Optional[CandidateProfile] = Field(
        default=None, 
        description="Candidate profile JSON provided on Turn 1"
    )
    message: Optional[str] = Field(
        default=None, 
        description="Candidate answer/message provided on Turn N"
    )


class InterviewResponse(BaseModel):
    """
    Response schema for POST /api/interview.
    In-progress: { "reply": "...", "done": false }
    Completed:   { "reply": "...", "done": true, "feedback": { ... } }
    """
    reply: str = Field(..., description="Interviewer reply or next technical question")
    done: bool = Field(..., description="Whether the interview is complete")
    feedback: Optional[FeedbackData] = Field(
        default=None, 
        description="Structured feedback payload, provided only when done is true"
    )
    score: Optional[int] = Field(
        default=None,
        description="Evaluation score of the latest response (0-100)"
    )
    averageScore: Optional[int] = Field(
        default=None,
        description="Running average score across all turns (0-100)"
    )
    totalQuestions: Optional[int] = Field(
        default=None,
        description="Total questions asked so far"
    )
    coveredDays: Optional[List[int]] = Field(
        default=None,
        description="List of tested curriculum day numbers"
    )
    isFollowUp: Optional[bool] = Field(
        default=None,
        description="Whether the returned question is an adaptive deep-dive probe"
    )
    technicalScore: Optional[int] = Field(
        default=None,
        description="Final technical score (0-100)"
    )
    communicationScore: Optional[int] = Field(
        default=None,
        description="Final communication score (0-100)"
    )
    overallScore: Optional[int] = Field(
        default=None,
        description="Blended overall interview score (0-100)"
    )


# ---------------------------------------------------------------------------
# 4. Database Persistence Records
# ---------------------------------------------------------------------------
class SessionRecord(BaseModel):
    """Structured model representing an interview session stored in SQLite."""
    session_id: str
    candidate_id: str
    candidate_name: str
    job_role: str
    status: str
    difficulty_level: str
    total_questions: int
    covered_days: List[int] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TurnRecord(BaseModel):
    """Structured model representing an interview turn stored in SQLite."""
    id: Optional[int] = None
    session_id: str
    turn_index: int
    question_text: str
    curriculum_day: int
    difficulty: str
    is_follow_up: bool = False
    candidate_answer: Optional[str] = None
    evaluation: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# 5. Internal Schemas for Agents and State Planning
# ---------------------------------------------------------------------------
class QuestionPlan(BaseModel):
    """Curriculum question plan item."""
    step: int
    day: int
    module: str
    topic: str
    difficulty: str
    question_type: str
    objectives: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class EvaluationScore(BaseModel):
    """Candidate answer evaluation scores across core rubrics."""
    correctness: int = Field(default=0, ge=0, le=100)
    reasoning: int = Field(default=0, ge=0, le=100)
    depth: int = Field(default=0, ge=0, le=100)
    examples: int = Field(default=0, ge=0, le=100)
    communication: int = Field(default=0, ge=0, le=100)
    practical_understanding: int = Field(default=0, ge=0, le=100)
    confidence_consistency: int = Field(default=0, ge=0, le=100)
    overall_score: int = Field(default=0, ge=0, le=100)
    notes: str = ""
    misconceptions: List[str] = Field(default_factory=list)
    follow_up_needed: bool = False
