# 📋 Project Prompt History & Implementation Plan

This document contains the complete record of user requirements, iterative prompts, architectural decisions, and the technical implementation plan for the **Adaptive AI Technical Interview Platform**.

---

## 📑 Table of Contents
1. [Chronological User Prompts](#-chronological-user-prompts)
   - [Prompt 1: Question Cap, Scoring Display & Abusive Content Handling](#prompt-1-question-cap-scoring-display--abusive-content-handling)
   - [Prompt 2: Negative Scoring on Profanity & Enforcing Turn Limits](#prompt-2-negative-scoring-on-profanity--enforcing-turn-limits)
   - [Prompt 3: Comprehensive Behavior & Communication Evaluation Layer](#prompt-3-comprehensive-behavior--communication-evaluation-layer)
   - [Prompt 4: Scoring Formula Refinement & Terminology Metric Clarification](#prompt-4-scoring-formula-refinement--terminology-metric-clarification)
   - [Prompt 5 & 6: Running & Verification Instructions](#prompt-5--6-running--verification-instructions)
   - [Prompt 7: Executive Summary Coherence & Behavioral Separation](#prompt-7-executive-summary-coherence--behavioral-separation)
   - [Prompt 8: Penalty Attribution to Behavior Layer](#prompt-8-penalty-attribution-to-behavior-layer)
   - [Prompt 9: GitHub Repository Initialization & README Creation](#prompt-9-github-repository-initialization--readme-creation)
   - [Prompt 10: Railway Deployment & Multi-Stage Dockerfile](#prompt-10-railway-deployment--multi-stage-dockerfile)
   - [Prompt 11: Prompt History & Implementation Plan Generation](#prompt-11-prompt-history--implementation-plan-generation)
2. [Complete Technical Implementation Plan](#-complete-technical-implementation-plan)
   - [Architectural Overview](#architectural-overview)
   - [Dual-Layer Evaluation Engine](#dual-layer-evaluation-engine)
   - [Data Models & API Schemas](#data-models--api-schemas)
   - [Backend State Machine & Agents](#backend-state-machine--agents)
   - [Frontend Dashboard & UI Components](#frontend-dashboard--ui-components)
   - [Verification & Automated Test Suite](#verification--automated-test-suite)
   - [Railway & Production Deployment Strategy](#railway--production-deployment-strategy)

---

## 📜 Chronological User Prompts

### Prompt 1: Question Cap, Scoring Display & Abusive Content Handling
> **User:**
> *"as you can see in screenshot question limit is crossing more than 8. and score is not showing . and if a abusive word is given than no respond only same question is asked again. fix this"*

- **Focus**: Fixed loop where sessions exceeded the 8-question maximum, resolved score visualization in progress tracker, and handled abusive input gracefully without locking the interview graph.

---

### Prompt 2: Negative Scoring on Profanity & Enforcing Turn Limits
> **User:**
> *"see score is not giving. and again more than 8 question is asked by it. fix it. and fix this also that if the person give abusive word then his score goes to negative."*

- **Focus**: Hard question cap at 8 turns across all candidate scenarios, negative conduct penalty on abusive words, and real-time score propagation in API response payload.

---

### Prompt 3: Comprehensive Behavior & Communication Evaluation Layer
> **User:**
> *"We need to improve the FINAL INTERVIEW EVALUATION REPORT.*
> 
> *IMPORTANT:*
> *Do NOT redesign the existing architecture.*
> *Do NOT break the existing API contract.*
> *Do NOT remove the current feedback fields: `summary`, `strengths`, `gaps`, `next`.*
> *Keep all existing technical evaluation functionality.*
> 
> *The problem we need to solve is that the current final feedback evaluates technical knowledge but does NOT evaluate the candidate's interview behavior and communication style.*
> 
> *Implement a new "Interview Behavior & Communication" evaluation layer.*
> 
> *==================================================*
> *1. WHAT TO ANALYZE*
> *==================================================*
> *Analyze the candidate's COMPLETE conversation history, not only the final answer.*
> *Evaluate these dimensions:*
> *A. Communication Clarity*
> *B. Technical Communication*
> *C. Confidence & Delivery Style*
> *D. Conciseness vs Verbosity*
> *E. Professionalism & Tone*
> *F. Answer Structure*
> *G. Responsiveness to Questions*
> *H. Overall Interview Presence*
> 
> *==================================================*
> *2. SCORING MODEL*
> *==================================================*
> *technical_score: 0 - 100 (existing)*
> *communication_score: 0 - 100 (new)*
> *overall_score: 0 - 100 (weighted: 70% technical + 30% communication)*
> 
> *Each behavioral dimension scored 0.0 - 10.0 with 1-2 sentence evidence-grounded assessment.*
> 
> *==================================================*
> *3. COMMUNICATION STYLE CLASSIFICATION*
> *==================================================*
> *Classify candidate into 1-2 styles ("Clear & Structured", "Concise & Direct", "Detailed & Analytical", "Conversational", "Verbose", "Fragmented", "Hesitant", "Inconsistent").*
> 
> *==================================================*
> *4. SPECIFIC LANGUAGE OBSERVATIONS*
> *==================================================*
> *Provide concrete observations grounded in conversation transcript.*
> 
> *==================================================*
> *5. OUTPUT FORMAT*
> *==================================================*
> *Keep existing feedback structure and ADD behavior evaluation under a new field.*
> 
> *==================================================*
> *6. CRITICAL RULES*
> *==================================================*
> *- Ground every observation in the actual interview transcript.*
> *- Do NOT generate generic or boilerplate feedback.*
> *- If the candidate wrote very little, score accordingly and state evidence was limited.*
> *- Tone must be constructive, professional, and objective.*
> *- Do NOT diagnose psychological traits. Only evaluate observable interview communication behavior.*
> *- Ensure frontend displays this new section cleanly in final report."*

---

### Prompt 4: Scoring Formula Refinement & Terminology Metric Clarification
> **User:**
> *"Fix the communication score definition:
> Don't leave this ambiguous. Use the average of the 8 behavioral dimensions. That makes the score reproducible and avoids one LLM-generated 'overall presence' score dominating everything.
> 
> Use:
> communication_score = round(average(clarity, technical_communication, confidence, conciseness, professionalism, answer_structure, responsiveness, overall_presence) * 10)
> 
> Then:
> overall_score = round(0.70 * technical_score + 0.30 * communication_score)
> 
> 2. Don't make 'technical terminology density' a scoring goal.
> Density alone doesn't mean good communication. A candidate can use fewer technical terms and explain the concept extremely well.
> 
> Change it to:
> technical terminology accuracy and appropriateness"*

---

### Prompt 5 & 6: Running & Verification Instructions
> **User:**
> *"how to run it?"*
> *"tell me step by step how to test it and run"*

- **Focus**: Delivered complete end-to-end execution guide for local Python/FastAPI environment, Vite React frontend, and automated testing suite.

---

### Prompt 7: Executive Summary Coherence & Behavioral Separation
> **User:**
> *"I found one important inconsistency: Look at your Executive Summary: 'The candidate showed strong practical knowledge...' and your Strengths: 'Clear communication and structured approach to system architectural trade-offs'. But your Behavior section says: Communication Clarity: 4/10, Answer Structure: 3.5/10, Professionalism: 1.5/10, Overall Presence: 3.7/10. That can look contradictory to a judge.*
> 
> *Change the executive summary to something like:
> 'Sarah Johnson demonstrated strong technical understanding in several evaluated AI curriculum areas, particularly vector search and backend APIs. However, the interview revealed weaknesses in communication structure, responsiveness, and professional language, which significantly affected the overall interview performance.'*
> 
> *Make the distinction between technical knowledge and behavior explicit."*

---

### Prompt 8: Penalty Attribution to Behavior Layer
> **User:**
> *"The penalty should be clearly tied to the behavior score, not randomly to the technical score.
> Your screenshot says: Penalty: -25/100. That could make a judge wonder: 'Is profanity reducing the candidate's technical knowledge score?' It shouldn't.
> 
> Instead, make it:
> ⚠️ Professionalism penalty: -2.5 points (or ⚠️ Behavior penalty: -25 points)
> 
> And internally:
> Technical Performance -> unchanged
> Communication / Behavior -> penalty applied
> Overall Interview Score -> 70% Technical + 30% Communication"*

---

### Prompt 9: GitHub Repository Initialization & README Creation
> **User:**
> *"https://github.com/apragam80-sys/The-Interview-Agent . push the full project to github and also make readme.md file to make repo beautifull"*

- **Focus**: Initialized Git repository on `main`, built visual markdown documentation with Mermaid architecture diagram, API contract reference, and pushed complete codebase to GitHub.

---

### Prompt 10: Railway Deployment & Multi-Stage Dockerfile
> **User:**
> *"i have to deploy it on railway and its not supporting pip make an docker file so i can deploy it on railway"*

- **Focus**: Created production multi-stage `Dockerfile` (Node 18 frontend builder + Python 3.11 backend server), `railway.json` configuration, dynamic port binding, SPA static route mounting in FastAPI, and updated API service client.

---

### Prompt 11: Prompt History & Implementation Plan Generation
> **User:**
> *"generate a prompt.md file, in which all my prompt and the implementation plan written"*

---

## 🛠️ Complete Technical Implementation Plan

### Architectural Overview

```mermaid
flowchart TD
    subgraph Client [Frontend UI (React + Tailwind)]
        UI[Candidate Selection & Interview Chat]
        DASH[Dual-Layer Feedback Dashboard]
    end

    subgraph API [FastAPI Gateway]
        EP["POST /api/interview"]
    end

    subgraph Orchestrator [LangGraph State Machine (8 Nodes)]
        SR[Session Router Node]
        CA[Candidate Analyzer Node]
        CR[Curriculum Retriever Node]
        IP[Interview Planner Node]
        MM[Memory Manager Node]
        AE[Answer Evaluator Node]
        AF[Adaptive Follow-up / Progression Router]
        QG[Question Generator Node]
        FG[Feedback Generator & Behavior Evaluator Node]
    end

    subgraph Storage [Data & Persistence Layer]
        SQL[(SQLite: interview_sessions.db)]
        VEC[(ChromaDB: curriculum_collection)]
        JSON[(candidates.json & curriculum.json)]
    end

    UI -->|Turn 1 (Init) / Turn N (Message)| EP
    EP --> SR
    SR -->|Init| CA --> CR --> IP --> QG
    SR -->|Turn N| MM --> AE --> AF
    AF -->|Next Topic / Follow-up| QG
    AF -->|Session Complete (Done=True)| FG
    FG --> DASH
    SQL <--> SR
    SQL <--> FG
    VEC <--> CR
    JSON <--> CA
    JSON <--> CR
```

---

### Dual-Layer Evaluation Engine

#### 1. Pure Technical Score (0–100)
- Computed solely from candidate answers on technical questions.
- Unaffected by profanity or conduct penalties to maintain pure technical measurement.
- Normalized across curriculum modules covered (Data Engineering, Neural Architectures, RAG, Alignment, Deployment).

#### 2. Communication & Behavior Score (0–100)
- Analyzes complete transcript history across 8 observable dimensions:
  1. **Communication Clarity (0–10)**: Structural coherence, idea transitions.
  2. **Technical Communication (0–10)**: Terminology accuracy, mechanism explanations vs buzzwords.
  3. **Confidence & Delivery Style (0–10)**: Assertiveness vs excessive hedging.
  4. **Conciseness vs Verbosity (0–10)**: Directness, signal-to-noise ratio.
  5. **Professionalism & Tone (0–10)**: Constructiveness, respectfulness, conduct penalties.
  6. **Answer Structure (0–10)**: Concept $\rightarrow$ reasoning $\rightarrow$ example $\rightarrow$ trade-offs.
  7. **Responsiveness to Questions (0–10)**: Answering the exact prompt asked without pivoting.
  8. **Overall Interview Presence (0–10)**: Holistic engineering communication readiness.

$$\text{Communication Score} = \text{round}\left(\frac{\text{Clarity} + \text{TechComm} + \text{Confidence} + \text{Conciseness} + \text{Professionalism} + \text{Structure} + \text{Responsiveness} + \text{Presence}}{8} \times 10\right)$$

#### 3. Composite Overall Score (0–100)
$$\text{Overall Score} = \text{round}\left(0.70 \times \text{Technical Score} + 0.30 \times \text{Communication Score}\right)$$

---

### Data Models & API Schemas

```python
class BehaviorDimensionScore(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    assessment: str

class InterviewBehaviorAssessment(BaseModel):
    communication_clarity: BehaviorDimensionScore
    technical_communication: BehaviorDimensionScore
    confidence: BehaviorDimensionScore
    conciseness: BehaviorDimensionScore
    professionalism: BehaviorDimensionScore
    answer_structure: BehaviorDimensionScore
    responsiveness: BehaviorDimensionScore
    overall_interview_presence: BehaviorDimensionScore
    communication_styles: List[str]
    language_observations: List[str]
    overall_presence_summary: str

class FeedbackData(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]
    behavior: Optional[InterviewBehaviorAssessment] = None
    technical_score: Optional[int] = Field(None, ge=0, le=100)
    communication_score: Optional[int] = Field(None, ge=0, le=100)
    overall_score: Optional[int] = Field(None, ge=0, le=100)

class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[FeedbackData] = None
    score: Optional[int] = None
    averageScore: Optional[int] = None
    totalQuestions: Optional[int] = None
    coveredDays: Optional[List[int]] = None
    isFollowUp: Optional[bool] = None
    technicalScore: Optional[int] = None
    communicationScore: Optional[int] = None
    overallScore: Optional[int] = None
```

---

### Backend State Machine & Agents

1. **`SessionRouter` (`backend/app/agents/interview_state_manager.py`)**:
   - Manages SQLite session lookup and restores state.
   - Routes Turn 1 into initialization pipeline and Turn N into evaluation pipeline.
2. **`CandidateAnalyzer` (`backend/app/agents/candidate_analyzer.py`)**:
   - Ingests candidate profile, job role, experience level, and claims.
3. **`CurriculumRetriever` (`backend/app/agents/curriculum_retriever.py`)**:
   - Queries ChromaDB embeddings to retrieve 31 days of AI engineering curriculum.
4. **`InterviewPlanner` (`backend/app/agents/interview_planner.py`)**:
   - Generates customized interview roadmap targeting 4+ curriculum days.
5. **`MemoryManager` (`backend/app/agents/memory_manager.py`)**:
   - Maintains rolling conversation buffer and updates coverage status.
6. **`AnswerEvaluator` (`backend/app/agents/answer_evaluator.py`)**:
   - Evaluates technical correctness (0-100), detects conduct violations, and applies penalties exclusively to behavior state.
7. **`AdaptiveFollowup` (`backend/app/agents/adaptive_followup.py`)**:
   - Decides whether to probe deeper into misconceptions or pivot to new curriculum topics. Enforces the strict 8-question cap.
8. **`FeedbackGenerator` & `BehaviorEvaluator` (`backend/app/agents/feedback_generator.py` & `backend/app/services/behavior_evaluator.py`)**:
   - Generates dual-layer evaluation: pure technical metrics + 8 behavioral dimensions + styles + observations + 70/30 composite score.

---

### Frontend Dashboard & UI Components

- **`CandidateSelector.jsx`**: Selects from 20 diverse candidate profiles across Junior, Mid, Senior, and Staff engineering tiers.
- **`ChatInterface.jsx`**: Interactive chat interface with real-time conduct alerts (`⚠️ Professionalism penalty: -25 points`), adaptive follow-up pills, and auto-scrolling conversation log.
- **`ProgressTracker.jsx`**: Live tracking of current question number (out of 8), covered curriculum modules, latest technical score, and cumulative average.
- **`FeedbackDashboard.jsx`**:
  - **Hero Score Summary**: 3 prominent score cards (Overall Composite 70/30, Pure Technical, Communication & Behavior).
  - **Executive Summary & Strengths**: Distinct distinction between technical knowledge and communication presence.
  - **Gaps & Next Steps**: Detailed technical remediation roadmap.
  - **Behavior & Communication Breakdown**:
    - Circular gauge for Overall Presence score.
    - 8 Dimension score bars with evidence assessments.
    - Style tags ("Clear & Structured", "Detailed & Analytical", etc.).
    - Specific language observations.

---

### Verification & Automated Test Suite

| Test Suite | Purpose | Test Cases |
| :--- | :--- | :--- |
| `test_api_contract.py` | Validates compliance with `POST /api/interview` contract | 3 |
| `test_data_layer.py` | Tests SQLite persistence and ChromaDB semantic search | 5 |
| `test_adaptive_behavior.py` | Tests follow-up generation and difficulty steering | 4 |
| `test_behavior_evaluation.py` | Tests 8 behavioral dimensions, styles, and edge cases | 9 |
| `test_candidate_coverage.py` | Tests full interview flows across all 20 candidate profiles | 8 |
| **Total Automated Tests** | **Comprehensive Regression Suite** | **29 Tests (100% Pass)** |

---

### Railway & Production Deployment Strategy

- **Multi-Stage `Dockerfile`**:
  - Compiles frontend inside `node:18-alpine`.
  - Serves API & SPA through unified Python 3.11 Uvicorn server on `${PORT:-8000}`.
- **`railway.json`**:
  - Preconfigured with Dockerfile builder, `/health` health check endpoint, and auto-restart policy.
- **Dynamic API Client**:
  - Frontend automatically detects production environment and calls relative `/api/interview` on the same domain without CORS overhead.
