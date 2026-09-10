import os
from typing import Optional
from langchain_groq import ChatGroq
from app.config import settings

_default_llm: Optional[ChatGroq] = None


def get_llm(model: Optional[str] = None, temperature: float = 0.2) -> ChatGroq:
    """
    Returns a configured reusable ChatGroq instance.
    Uses GROQ_API_KEY from environment/settings.
    """
    api_key = getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    model_name = (
        model
        or getattr(settings, "GROQ_MODEL", None)
        or os.getenv("GROQ_MODEL", "")
        or "openai/gpt-oss-20b"
    )

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Please provide it in your .env file or environment variables."
        )

    return ChatGroq(
        model=model_name,
        groq_api_key=api_key,
        temperature=temperature,
    )
