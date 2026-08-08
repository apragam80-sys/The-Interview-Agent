"""
LLM Client Factory and Interface Wrapper.
Provides initialization helpers for LangChain ChatModel instances (Gemini, Groq).
"""

from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from app.config import GEMINI_API_KEY, GROQ_API_KEY, LLM_MODEL, TEMPERATURE, logger


def get_llm(model_name: Optional[str] = None, temperature: Optional[float] = None) -> BaseChatModel:
    """
    Instantiate and return a configured LangChain ChatModel instance (Gemini or Groq).

    Args:
        model_name (Optional[str]): Target model identifier (e.g. 'gemini-2.5-pro', 'llama-3.3-70b-versatile').
        temperature (Optional[float]): Sampling temperature.

    Returns:
        BaseChatModel: Configured LangChain chat model instance.
    """
    model = model_name or LLM_MODEL
    temp = temperature if temperature is not None else TEMPERATURE

    # 1. Groq Provider (e.g. llama-3.3-70b-versatile, llama-3.1-70b-versatile, mixtral-8x7b-32768)
    if any(k in model.lower() for k in ["groq", "llama", "mixtral", "gemma"]) or (GROQ_API_KEY and not GEMINI_API_KEY):
        try:
            from langchain_groq import ChatGroq
            groq_model = model if any(k in model.lower() for k in ["llama", "mixtral", "gemma"]) else "llama-3.3-70b-versatile"
            return ChatGroq(
                model_name=groq_model,
                groq_api_key=GROQ_API_KEY or "dummy_key",
                temperature=temp
            )
        except Exception as e:
            logger.warning(f"Could not initialize Groq LLM: {e}. Trying Gemini fallback.")

    # 2. Google Gemini Provider (e.g. gemini-2.5-pro, gemini-1.5-pro, gemini-1.5-flash)
    if ("gemini" in model.lower() or GEMINI_API_KEY) and GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            gemini_model = model if "gemini" in model.lower() else "gemini-2.5-pro"
            return ChatGoogleGenerativeAI(
                model=gemini_model,
                google_api_key=GEMINI_API_KEY or "dummy_key",
                temperature=temp
            )
        except Exception as e:
            logger.warning(f"Could not initialize Gemini LLM: {e}.")

    # 3. Fallback to Groq if Groq key exists
    if GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name="llama-3.3-70b-versatile",
                groq_api_key=GROQ_API_KEY or "dummy_key",
                temperature=temp
            )
        except Exception as e:
            logger.warning(f"Could not initialize fallback Groq LLM: {e}.")

    # Default fallback to Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        google_api_key=GEMINI_API_KEY or "dummy_key",
        temperature=temp
    )
