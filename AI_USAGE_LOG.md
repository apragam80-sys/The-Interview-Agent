# AI Usage and Decision Log

This log documents all AI model interactions, agent prompts, architectural decisions, and evaluation traces used in building and verifying the Adaptive AI Technical Interview Platform.

---

## 1. Project Overview & Constraints

- **Hackathon Objective**: Build an Adaptive AI Technical Interview Agent.
- **Contract Boundary**: Single public endpoint strictly exposed at `POST /api/interview`.
- **Core Requirements**:
  - Maintain conversation memory and session state using `sessionId`.
  - Ask at least 8 questions.
  - Cover at least 4 unique curriculum days from `curriculum.json`.
  - Generate intelligent adaptive follow-up probes for shallow/ambiguous answers.
  - Return structured certification feedback with `{ summary, strengths, gaps, next }`.
- **Target Architecture**: 8-agent LangGraph State Machine with SQLite persistence and ChromaDB RAG.

---

## 2. Agent Inventory & Model Configuration

| Agent ID | Name | Primary Model | Purpose |
|---|---|---|---|
| `agent-01` | Candidate Analyzer | Gemini 2.5 Pro | Extracts profile signals and computes baseline difficulty. |
| `agent-02` | Curriculum Retriever | ChromaDB + Embeddings | Vector search across 31 curriculum days and 8 modules. |
| `agent-03` | Interview Planner | Gemini 2.5 Pro | Generates structured 8+ question roadmap covering >= 4 days. |
| `agent-04` | Memory Manager | SQLite State Sync | Tracks turn count, covered days, and session state. |
| `agent-05` | Answer Evaluator | Gemini 2.5 Pro | Scores answers across 6 core rubrics and flags follow-up needs. |
| `agent-06` | Adaptive Follow-up | Gemini 2.5 Pro | Synthesizes targeted follow-up probes on edge cases. |
| `agent-07` | Question Generator | Gemini 2.5 Pro | Synthesizes technical questions grounded in curriculum. |
| `agent-08` | Feedback Generator | Gemini 2.5 Pro | Formats final structured report (`summary`, `strengths`, `gaps`, `next`). |

---

## 3. Prompt Log & Versioning

### 3.1 Candidate Analyzer Prompt Template
- **Version**: 1.0.0
- **Input**: Candidate member metadata, missions history, signals.
- **Output**: JSON containing `difficulty_level`, `target_days`, and `candidate_signals`.

### 3.2 Answer Evaluator Prompt Template
- **Version**: 1.0.0
- **Input**: `question_text`, `candidate_answer`, `curriculum_context`, `difficulty`.
- **Rubrics**: Correctness, Reasoning, Depth, Examples, Communication, Practical Understanding (0-100 each).

### 3.3 Question Generator Prompt Template
- **Version**: 1.0.0
- **Archetypes**: Conceptual, Debugging, Production, Architecture, Scenario.

### 3.4 Feedback Generator Prompt Template
- **Version**: 1.0.0
- **Output Format**: Strictly `{ summary: str, strengths: list[str], gaps: list[str], next: list[str] }`.

---

## 4. Verification & Audit Trail

| Date / Step | Action | Result | Status |
|---|---|---|---|
| Phase 1 | Project scaffolding & directory structure setup | Complete tree created | Verified |
| Phase 2 | SQLite schema & Pydantic models initialization | Tables & schemas verified | Verified |
| Phase 3 | LangGraph StateGraph assembly | 8 nodes & conditional routing | Verified |
| Phase 4 | API Contract unit tests (`test_api_contract.py`) | Single endpoint validated | Passed |
| Phase 5 | 20-Candidate benchmark run (`test_candidate_flows.py`) | 20/20 candidates evaluated | Passed |
| Phase 6 | Live Steerability test (`test_steerability.py`) | Dynamic node addition in <20m | Passed |
