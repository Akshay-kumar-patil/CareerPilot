"""
Hybrid Multi-Model Router — the brain of the AI system.
Routes requests to Gemini, OpenAI, or Groq (llama-3.3-70b-versatile) based on
connectivity, preference, and task.
"""
import socket
import logging
from typing import Optional, Tuple
from langchain_core.language_models import BaseChatModel
from backend.config import settings

logger = logging.getLogger(__name__)

# Gemini quota/rate-limit error codes and messages to detect
_QUOTA_SIGNALS = ("429", "RESOURCE_EXHAUSTED", "quota", "rate limit", "rateLimitExceeded", "api key expired", "api_key_invalid")


def is_quota_error(error: Exception) -> bool:
    """Return True if the exception is a Gemini quota/rate-limit error."""
    msg = str(error).lower()
    return any(sig.lower() in msg for sig in _QUOTA_SIGNALS)


class ModelRouter:
    def __init__(self):
        self._total_tokens_used: int = 0
        self._estimated_cost_usd: float = 0.0
        # Track if Gemini quota is exhausted this session so we skip it immediately
        self._gemini_quota_exhausted: bool = False

    def check_internet(self) -> bool:
        try:
            socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=3)
            return True
        except (socket.timeout, socket.error, OSError):
            try:
                socket.create_connection(("api.groq.com", 443), timeout=3)
                return True
            except (socket.timeout, socket.error, OSError):
                return False

    def check_gemini(self) -> bool:
        if not settings.GEMINI_API_KEY or self._gemini_quota_exhausted:
            return False
        try:
            socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=3)
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def check_groq(self) -> bool:
        """Check if Groq API is reachable and configured."""
        if not settings.GROQ_API_KEY:
            return False
        try:
            socket.create_connection(("api.groq.com", 443), timeout=3)
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def mark_gemini_quota_exhausted(self):
        """Call this when a 429/RESOURCE_EXHAUSTED is received from Gemini."""
        logger.warning("Gemini quota marked as exhausted — routing to Groq for remainder of session.")
        self._gemini_quota_exhausted = True

    def reset_gemini_quota(self):
        """Call this to re-enable Gemini (e.g. after quota resets)."""
        self._gemini_quota_exhausted = False
        logger.info("Gemini quota flag reset.")

    def get_llm(
        self,
        provider: Optional[str] = None,
        task_type: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> BaseChatModel:
        """
        Get the best available LLM.

        If provider is 'gemini' but quota is exhausted, automatically falls back
        to Groq. No LangChain .with_fallbacks() wrapping — we handle it explicitly
        so chains.py can detect quota errors cleanly.
        """
        provider = provider or settings.DEFAULT_MODEL_PROVIDER

        # If Gemini was requested but quota is exhausted, redirect to Groq
        if provider == "gemini" and self._gemini_quota_exhausted:
            logger.info("Gemini quota exhausted — redirecting to Groq")
            return self._get_groq(temperature, max_tokens)

        if provider == "auto":
            return self._auto_route(task_type, temperature, max_tokens)
        elif provider == "gemini":
            return self._get_gemini(temperature, max_tokens)
        elif provider == "openai":
            return self._get_openai(temperature, max_tokens)
        elif provider == "groq":
            return self._get_groq(temperature, max_tokens)
        else:
            return self._auto_route(task_type, temperature, max_tokens)

    def get_llm_with_fallback(
        self,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Tuple[BaseChatModel, str]:
        """
        Get LLM and return (llm, provider_name_used).
        If Gemini quota is exhausted, returns Groq directly.
        Used by chains that need to know which provider was actually used.
        """
        provider = provider or settings.DEFAULT_MODEL_PROVIDER

        if provider == "gemini" and self._gemini_quota_exhausted:
            logger.info("Gemini quota exhausted — using Groq directly")
            return self._get_groq(temperature, max_tokens), "groq"

        if provider == "gemini" and settings.GEMINI_API_KEY:
            return self._get_gemini(temperature, max_tokens), "gemini"
        elif provider == "openai" and settings.OPENAI_API_KEY:
            return self._get_openai(temperature, max_tokens), "openai"
        elif provider == "groq" or self.check_groq():
            return self._get_groq(temperature, max_tokens), "groq"

        # Last resort
        if settings.GEMINI_API_KEY:
            return self._get_gemini(temperature, max_tokens), "gemini"
        raise RuntimeError("No AI model available.")

    def _auto_route(self, task_type: str, temperature: float, max_tokens: int) -> BaseChatModel:
        has_internet = self.check_internet()
        has_groq_key = bool(settings.GROQ_API_KEY)
        has_gemini_key = bool(settings.GEMINI_API_KEY) and not self._gemini_quota_exhausted
        has_openai_key = bool(settings.OPENAI_API_KEY)

        if has_internet and has_gemini_key:
            logger.info("Auto-routing to Gemini")
            return self._get_gemini(temperature, max_tokens)

        if has_internet and has_openai_key:
            logger.info("Auto-routing to OpenAI")
            return self._get_openai(temperature, max_tokens)

        if has_internet and has_groq_key:
            logger.info("Auto-routing to Groq (llama-3.3-70b-versatile)")
            return self._get_groq(temperature, max_tokens)

        if settings.GEMINI_API_KEY:
            return self._get_gemini(temperature, max_tokens)
        if settings.OPENAI_API_KEY:
            return self._get_openai(temperature, max_tokens)
        if settings.GROQ_API_KEY:
            return self._get_groq(temperature, max_tokens)

        raise RuntimeError(
            "No AI model available. Please either:\n"
            "1. Set GEMINI_API_KEY in .env for Google Gemini AI, or\n"
            "2. Set GROQ_API_KEY in .env for Groq (llama-3.3-70b-versatile) — free & ultra-fast, or\n"
            "3. Set OPENAI_API_KEY in .env for OpenAI"
        )

    def _get_gemini(self, temperature: float, max_tokens: int) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    def _get_openai(self, temperature: float, max_tokens: int) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _get_groq(self, temperature: float, max_tokens: int) -> BaseChatModel:
        """Groq inference — ultra-fast, free tier, uses llama-3.3-70b-versatile."""
        from langchain_groq import ChatGroq
        # Groq max_tokens cap is 32768 for llama-3.3-70b-versatile
        safe_max_tokens = min(max_tokens, 8192)
        return ChatGroq(
            model=settings.GROQ_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=temperature,
            max_tokens=safe_max_tokens,
        )

    def get_status(self) -> dict:
        return {
            "internet_available": self.check_internet(),
            "gemini_available": self.check_gemini(),
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "gemini_quota_exhausted": self._gemini_quota_exhausted,
            "gemini_model": settings.GEMINI_MODEL,
            "groq_available": self.check_groq(),
            "groq_configured": bool(settings.GROQ_API_KEY),
            "groq_model": settings.GROQ_MODEL,
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "default_provider": settings.DEFAULT_MODEL_PROVIDER,
            "openai_model": settings.OPENAI_MODEL,
            "tokens_used": self._total_tokens_used,
            "estimated_cost_usd": round(self._estimated_cost_usd, 4),
        }

    def track_usage(self, tokens: int, model: str = "gemini-2.5-flash"):
        self._total_tokens_used += tokens
        cost_per_1k = {
            "gemini-2.0-flash": 0.0001, "gemini-2.0-flash-lite": 0.00005,
            "gemini-2.5-pro": 0.00125, "gemini-2.5-flash": 0.0001,
            "gemini-1.5-pro": 0.00125, "gemini-1.5-flash": 0.0001,
            "gpt-3.5-turbo": 0.002, "gpt-4": 0.06,
            "gpt-4-turbo": 0.03, "gpt-4o": 0.015, "gpt-4o-mini": 0.00015,
            # Groq is free tier — zero cost
            "llama-3.3-70b-versatile": 0.0,
        }
        rate = cost_per_1k.get(model, 0.0001)
        self._estimated_cost_usd += (tokens / 1000) * rate


# Singleton
model_router = ModelRouter()
