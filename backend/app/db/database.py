"""
SQLite Database Layer for Session Persistence and Message History.
Provides persistent storage, transaction management, and CRUD helpers for interview
sessions, turn evaluations, and metrics tracking.
"""

import sqlite3
import json
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Generator
from app.config import DB_PATH, logger
from app.models.schemas import SessionRecord, TurnRecord


def get_db_connection() -> sqlite3.Connection:
    """
    Establish and return a SQLite database connection with row factory enabled
    and WAL journal mode for concurrent read performance.

    Returns:
        sqlite3.Connection: Database connection object.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager providing automatic transaction commit and error rollback.

    Yields:
        sqlite3.Connection: Active database connection.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize SQLite database schema for interview sessions and turns.
    Creates tables and performance indexes if they do not already exist.
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # Table 1: Interview Sessions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            session_id TEXT PRIMARY KEY,
            candidate_id TEXT,
            candidate_name TEXT,
            job_role TEXT,
            status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
            difficulty_level TEXT NOT NULL DEFAULT 'MEDIUM',
            total_questions INTEGER DEFAULT 0,
            covered_days_json TEXT NOT NULL DEFAULT '[]',
            state_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Table 2: Interview Turns
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            curriculum_day INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            is_follow_up BOOLEAN DEFAULT 0,
            candidate_answer TEXT,
            evaluation_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES interview_sessions(session_id) ON DELETE CASCADE
        );
        """)

        # Indexes for fast lookup
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_turns_session_id ON interview_turns(session_id);
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_candidate ON interview_sessions(candidate_id);
        """)

    logger.info("SQLite database tables and indexes verified/initialized.")


def save_session(
    session_id: str,
    candidate_id: str,
    candidate_name: str,
    job_role: str,
    status: str,
    difficulty_level: str,
    total_questions: int,
    covered_days: List[int],
    state_dict: Dict[str, Any]
) -> None:
    """
    Insert or update an interview session in SQLite (Upsert).

    Args:
        session_id (str): Unique session identifier.
        candidate_id (str): Candidate identifier (e.g. CAND-001).
        candidate_name (str): Candidate name.
        job_role (str): Candidate target role.
        status (str): Current status ('IN_PROGRESS' or 'COMPLETED').
        difficulty_level (str): Computed difficulty level.
        total_questions (int): Total questions asked so far.
        covered_days (List[int]): List of unique curriculum day integers covered.
        state_dict (Dict[str, Any]): Full serialized LangGraph state dictionary.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO interview_sessions (
            session_id, candidate_id, candidate_name, job_role,
            status, difficulty_level, total_questions, covered_days_json,
            state_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id) DO UPDATE SET
            status = excluded.status,
            difficulty_level = excluded.difficulty_level,
            total_questions = excluded.total_questions,
            covered_days_json = excluded.covered_days_json,
            state_json = excluded.state_json,
            updated_at = CURRENT_TIMESTAMP;
        """, (
            session_id,
            candidate_id,
            candidate_name,
            job_role,
            status,
            difficulty_level,
            total_questions,
            json.dumps(covered_days),
            json.dumps(state_dict)
        ))


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an existing interview session by session ID.

    Args:
        session_id (str): Unique session identifier.

    Returns:
        Optional[Dict[str, Any]]: Session record dictionary, or None if not found.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interview_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "session_id": row["session_id"],
            "candidate_id": row["candidate_id"],
            "candidate_name": row["candidate_name"],
            "job_role": row["job_role"],
            "status": row["status"],
            "difficulty_level": row["difficulty_level"],
            "total_questions": row["total_questions"],
            "covered_days": json.loads(row["covered_days_json"]),
            "state": json.loads(row["state_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }


def list_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """
    List all interview sessions ordered by last update.

    Args:
        limit (int): Max number of sessions to return.

    Returns:
        List[Dict[str, Any]]: List of session summaries.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM interview_sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        return [
            {
                "session_id": r["session_id"],
                "candidate_id": r["candidate_id"],
                "candidate_name": r["candidate_name"],
                "job_role": r["job_role"],
                "status": r["status"],
                "difficulty_level": r["difficulty_level"],
                "total_questions": r["total_questions"],
                "covered_days": json.loads(r["covered_days_json"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            }
            for r in rows
        ]


def delete_session(session_id: str) -> bool:
    """
    Delete a session and all its associated turns from SQLite.

    Args:
        session_id (str): Session ID to delete.

    Returns:
        bool: True if deleted, False if session did not exist.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM interview_turns WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM interview_sessions WHERE session_id = ?", (session_id,))
        return cursor.rowcount > 0


def record_turn(
    session_id: str,
    turn_index: int,
    question_text: str,
    curriculum_day: int,
    difficulty: str,
    is_follow_up: bool,
    candidate_answer: Optional[str],
    evaluation_dict: Optional[Dict[str, Any]]
) -> int:
    """
    Insert an individual interview turn record into SQLite.

    Args:
        session_id (str): Unique session identifier.
        turn_index (int): Turn index sequence.
        question_text (str): Question presented to candidate.
        curriculum_day (int): Day number of tested objective.
        difficulty (str): Difficulty level of question.
        is_follow_up (bool): True if adaptive follow-up probe.
        candidate_answer (Optional[str]): Answer provided by candidate.
        evaluation_dict (Optional[Dict[str, Any]]): Evaluator scores and notes.

    Returns:
        int: Generated turn record ID.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO interview_turns (
            session_id, turn_index, question_text, curriculum_day,
            difficulty, is_follow_up, candidate_answer, evaluation_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            session_id,
            turn_index,
            question_text,
            curriculum_day,
            difficulty,
            1 if is_follow_up else 0,
            candidate_answer or "",
            json.dumps(evaluation_dict) if evaluation_dict else "{}"
        ))
        return cursor.lastrowid


def get_session_turns(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all turn history records for a session in sequential order.

    Args:
        session_id (str): Unique session identifier.

    Returns:
        List[Dict[str, Any]]: Ordered list of turn records.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM interview_turns WHERE session_id = ? ORDER BY turn_index ASC", 
            (session_id,)
        )
        rows = cursor.fetchall()

        turns = []
        for r in rows:
            turns.append({
                "id": r["id"],
                "turn_index": r["turn_index"],
                "question_text": r["question_text"],
                "curriculum_day": r["curriculum_day"],
                "difficulty": r["difficulty"],
                "is_follow_up": bool(r["is_follow_up"]),
                "candidate_answer": r["candidate_answer"],
                "evaluation": json.loads(r["evaluation_json"]) if r["evaluation_json"] else {},
                "created_at": r["created_at"]
            })
        return turns


def get_turn_count(session_id: str) -> int:
    """Return total number of recorded turns for a session."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM interview_turns WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        return row["count"] if row else 0


def get_last_turn(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent turn record for a session."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM interview_turns WHERE session_id = ? ORDER BY turn_index DESC LIMIT 1",
            (session_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "turn_index": row["turn_index"],
            "question_text": row["question_text"],
            "curriculum_day": row["curriculum_day"],
            "difficulty": row["difficulty"],
            "is_follow_up": bool(row["is_follow_up"]),
            "candidate_answer": row["candidate_answer"],
            "evaluation": json.loads(row["evaluation_json"]) if row["evaluation_json"] else {},
            "created_at": row["created_at"]
        }


# Auto-initialize database on import
init_db()
