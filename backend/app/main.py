"""
FastAPI Backend Application for Adaptive AI Technical Interview Platform.
Exposes ONLY the single required public endpoint: POST /api/interview.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import InterviewRequest, InterviewResponse, FeedbackData
from app.db.database import init_db, get_session, save_session
from app.graph.workflow import get_compiled_graph
from app.config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info("Starting Adaptive AI Interview Platform FastAPI Server")
    init_db()
    yield
    logger.info("Shutting down FastAPI Server")


# Initialize FastAPI application
app = FastAPI(
    title="Adaptive AI Technical Interview Platform",
    description="Multi-Agent LangGraph Technical Interview Platform exposing ONLY POST /api/interview",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Frontend Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing API information and documentation link."""
    return {
        "service": "Adaptive AI Technical Interview Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "interview_endpoint": "POST /api/interview",
        "frontend_dashboard": "http://localhost:5173"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "adaptive-interview-backend"}


@app.post(
    "/api/interview",
    response_model=InterviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Interview Turn",
    description="The single public API endpoint for starting or progressing an adaptive technical interview."
)
async def interview_endpoint(payload: InterviewRequest) -> InterviewResponse:
    """
    Single required endpoint: POST /api/interview.

    Turn 1 (Start):
        Request: { "sessionId": "...", "candidate": { ... } }
        Response: { "reply": "...", "done": false }

    Turn N (Conversation):
        Request: { "sessionId": "...", "message": "..." }
        Response (In Progress): { "reply": "...", "done": false }
        Response (Completed):   { "reply": "...", "done": true, "feedback": { ... } }
    """
    session_id = payload.sessionId
    logger.info(f"Received POST /api/interview for session: {session_id}")

    try:
        graph = get_compiled_graph()
        
        # Turn 1: Initialization Turn
        if payload.candidate:
            cand_dict = payload.candidate.model_dump()
            member = cand_dict.get("member", {})
            cand_id = member.get("id", "UNKNOWN")
            cand_name = member.get("name", "Candidate")
            job_role = member.get("jobRole", "Software Engineer")

            initial_state = {
                "session_id": session_id,
                "candidate_profile": cand_dict,
                "conversation_history": [],
                "evaluations": [],
                "covered_days": [],
                "total_questions_asked": 0,
                "is_complete": False,
            }

            output_state = graph.invoke(initial_state)

            diff_level = output_state.get("difficulty_level", "MID")
            total_q = output_state.get("total_questions_asked", 1)
            covered_d = output_state.get("covered_days", [])
            is_done = output_state.get("is_complete", False)
            reply = output_state.get("latest_reply", "Welcome to your technical interview.")
            feedback = output_state.get("final_feedback")

            # Persist initial session state in SQLite
            save_session(
                session_id=session_id,
                candidate_id=cand_id,
                candidate_name=cand_name,
                job_role=job_role,
                status="COMPLETED" if is_done else "IN_PROGRESS",
                difficulty_level=diff_level,
                total_questions=total_q,
                covered_days=covered_d,
                state_dict=output_state
            )

            return InterviewResponse(
                reply=reply,
                done=is_done,
                feedback=FeedbackData.model_validate(feedback) if feedback else None,
                score=output_state.get("latest_score"),
                averageScore=output_state.get("average_score"),
                totalQuestions=total_q,
                coveredDays=covered_d,
                isFollowUp=output_state.get("is_follow_up", False)
            )

        # Turn N: Conversation Turn
        elif payload.message is not None:
            existing_session = get_session(session_id)
            if not existing_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session '{session_id}' not found. You must initialize the interview with a candidate profile first."
                )

            # If session is already completed, return existing completion state
            if existing_session.get("status") == "COMPLETED" and existing_session.get("state", {}).get("final_feedback"):
                st = existing_session["state"]
                val_fb = FeedbackData.model_validate(st["final_feedback"]) if st.get("final_feedback") else None
                return InterviewResponse(
                    reply=st.get("latest_reply", "Interview is already completed."),
                    done=True,
                    feedback=val_fb,
                    score=st.get("latest_score"),
                    averageScore=st.get("average_score"),
                    totalQuestions=st.get("total_questions_asked", existing_session.get("total_questions", 8)),
                    coveredDays=st.get("covered_days", existing_session.get("covered_days", [])),
                    isFollowUp=False,
                    technicalScore=val_fb.technical_score if val_fb else None,
                    communicationScore=val_fb.communication_score if val_fb else None,
                    overallScore=val_fb.overall_score if val_fb else None
                )

            # Load prior state and inject latest message
            prior_state = existing_session.get("state", {})
            # Clear candidate_profile so router takes conversation path
            prior_state["candidate_profile"] = None
            prior_state["incoming_message"] = payload.message

            output_state = graph.invoke(prior_state)

            cand_id = existing_session.get("candidate_id", "UNKNOWN")
            cand_name = existing_session.get("candidate_name", "Candidate")
            job_role = existing_session.get("job_role", "Software Engineer")
            diff_level = output_state.get("difficulty_level", existing_session.get("difficulty_level", "MID"))
            total_q = output_state.get("total_questions_asked", existing_session.get("total_questions", 1))
            covered_d = output_state.get("covered_days", existing_session.get("covered_days", []))
            is_done = output_state.get("is_complete", False)
            reply = output_state.get("latest_reply", "Thank you. Let's proceed to the next topic.")
            feedback = output_state.get("final_feedback")

            # Persist updated session state in SQLite
            save_session(
                session_id=session_id,
                candidate_id=cand_id,
                candidate_name=cand_name,
                job_role=job_role,
                status="COMPLETED" if is_done else "IN_PROGRESS",
                difficulty_level=diff_level,
                total_questions=total_q,
                covered_days=covered_d,
                state_dict=output_state
            )

            validated_feedback = FeedbackData.model_validate(feedback) if feedback else None
            return InterviewResponse(
                reply=reply,
                done=is_done,
                feedback=validated_feedback,
                score=output_state.get("latest_score"),
                averageScore=output_state.get("average_score"),
                totalQuestions=total_q,
                coveredDays=covered_d,
                isFollowUp=output_state.get("is_follow_up", False),
                technicalScore=validated_feedback.technical_score if validated_feedback else None,
                communicationScore=validated_feedback.communication_score if validated_feedback else None,
                overallScore=validated_feedback.overall_score if validated_feedback else None
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request must contain either 'candidate' (Turn 1) or 'message' (Turn N)."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing interview turn for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview execution error: {str(e)}"
        )
