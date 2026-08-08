"""
Configuration and Environment Settings for Adaptive AI Interview Platform.
Includes paths, environment variables, LLM model settings, and logging configuration.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

# Load environment variables explicitly from root .env
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv()

# Data file paths
CURRICULUM_PATH = DATA_DIR / "curriculum.json"
CANDIDATES_PATH = DATA_DIR / "candidates.json"

# SQLite DB Path
DB_PATH = DATA_DIR / "interview_sessions.db"

# ChromaDB Persistence Directory
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"

# LLM API Settings (Gemini & Groq)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-pro")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))

# Minimum Interview Constraints
MIN_QUESTIONS = int(os.getenv("MIN_QUESTIONS", "8"))
MIN_CURRICULUM_DAYS = int(os.getenv("MIN_CURRICULUM_DAYS", "4"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("InterviewPlatform")
