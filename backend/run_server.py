"""
Uvicorn Server Launcher for FastAPI Backend.
"""

import uvicorn
from app.config import logger

if __name__ == "__main__":
    logger.info("Launching FastAPI server on http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
