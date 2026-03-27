"""
Hybrid Multi-Model Router — the brain of the AI system.
Routes requests to Gemini, OpenAI, or Ollama based on connectivity, preference, and task.
"""
import socket
import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel

from backend.config import settings

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Intelligent model routing with:
    - Google Gemini as primary cloud provider
    - OpenAI as secondary cloud fallback
    - Ollama as offline fallback
    - Auto-detection of available models
    - Cost-aware execution tracking
    """

    def __init__(self):
        self._gemini_available: Optional[bool] = None
        self._openai_available: Optional[bool] = None
        self._ollama_available: Optional[bool] = None
        self._total_tokens_used: int = 0
        self._estimated_cost_usd: float = 0.0

    def check_internet(self) -> bool:
        """Check if internet is available by probing Google's API endpoint."""
        try:
            socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=3)
            return True
        except (socket.timeout, socket.error, OSError):
            # Fallback: try OpenAI endpoint
            try:
                socket.create_connection(("api.openai.com", 443), timeout=3)
                return True
            except (socket.timeout, socket.error, OSError):
                return False

    def check_gemini(self) -> bool:
        """Check if Gemini API is reachable and configured."""
        if not settings.GEMINI_API_KEY:
            return False
        try:
            socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=3)
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            host = settings.OLLAMA_BASE_URL.replace("http://", "").replace("https://", "")
            if ":" in host:
                hostname, port = host.split(":")
                port = int(port)
            else:
                hostname, port = host, 11434
            socket.create_connection((hostname, port), timeout=2)
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def get_llm(
        self,
        provider: Optional[str] = None,
        task_type: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> BaseChatModel:
        """
        Get the best available LLM based on provider preference and availability.

        Args:
            provider: "gemini", "openai", "ollama", or "auto" (None = use settings default)
            task_type: Task hint for model selection — "generation", "analysis", "chat"
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            A LangChain chat model instance
        """
        provider = provider or settings.DEFAULT_MODEL_PROVIDER

        if provider == "auto":
            return self._auto_route(task_type, temperature, max_tokens)
        elif provider == "gemini":
            return self._get_gemini(temperature, max_tokens)
        elif provider == "openai":
            return self._get_openai(temperature, max_tokens)
        elif provider == "ollama":
            return self._get_ollama(temperature, max_tokens)
        else:
            return self._auto_route(task_type, temperature, max_tokens)

    def _auto_route(
        self, task_type: str, temperature: float, max_tokens: int
    ) -> BaseChatModel:
        """Auto-route to the best available model. Priority: Gemini → OpenAI → Ollama."""
        has_internet = self.check_internet()
        has_ollama = self.check_ollama()
        has_gemini_key = bool(settings.GEMINI_API_KEY)
        has_openai_key = bool(settings.OPENAI_API_KEY)

        # Priority 1: Gemini (if available + key)
        if has_internet and has_gemini_key:
            try:
                llm = self._get_gemini(temperature, max_tokens)
                logger.info("Using Gemini (primary cloud provider)")
                # Add fallbacks
                fallbacks = []
                if has_openai_key:
                    fallbacks.append(self._get_openai(temperature, max_tokens))
                if has_ollama:
                    fallbacks.append(self._get_ollama(temperature, max_tokens))
                if fallbacks:
                    return llm.with_fallbacks(fallbacks)
                return llm
            except Exception as e:
                logger.warning(f"Gemini failed: {e}, trying fallbacks...")

        # Priority 2: OpenAI (if available + key)
        if has_internet and has_openai_key:
            try:
                llm = self._get_openai(temperature, max_tokens)
                logger.info("Using OpenAI (secondary cloud provider)")
                if has_ollama:
                    fallback = self._get_ollama(temperature, max_tokens)
                    return llm.with_fallbacks([fallback])
                return llm
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}, trying Ollama...")

        # Priority 3: Ollama (offline)
        if has_ollama:
            logger.info("Using Ollama (offline mode)")
            return self._get_ollama(temperature, max_tokens)

        # Last resort: try Gemini or OpenAI anyway
        if has_gemini_key:
            return self._get_gemini(temperature, max_tokens)
        if has_openai_key:
            return self._get_openai(temperature, max_tokens)

        raise RuntimeError(
            "No AI model available. Please either:\n"
            "1. Set GEMINI_API_KEY in .env for Google Gemini AI, or\n"
            "2. Set OPENAI_API_KEY in .env for OpenAI, or\n"
            "3. Install and run Ollama (https://ollama.ai) for local AI"
        )

    def _get_gemini(self, temperature: float, max_tokens: int) -> BaseChatModel:
        """Get Google Gemini ChatModel."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    def _get_openai(self, temperature: float, max_tokens: int) -> BaseChatModel:
        """Get OpenAI ChatModel."""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _get_ollama(self, temperature: float, max_tokens: int) -> BaseChatModel:
        """Get Ollama ChatModel."""
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
            num_predict=max_tokens,
        )

    def get_status(self) -> dict:
        """Get current AI system status."""
        return {
            "internet_available": self.check_internet(),
            "gemini_available": self.check_gemini(),
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "gemini_model": settings.GEMINI_MODEL,
            "ollama_available": self.check_ollama(),
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "default_provider": settings.DEFAULT_MODEL_PROVIDER,
            "openai_model": settings.OPENAI_MODEL,
            "ollama_model": settings.OLLAMA_MODEL,
            "tokens_used": self._total_tokens_used,
            "estimated_cost_usd": round(self._estimated_cost_usd, 4),
        }

    def track_usage(self, tokens: int, model: str = "gemini-2.0-flash"):
        """Track token usage and estimated cost."""
        self._total_tokens_used += tokens
        # Rough pricing per 1K tokens
        cost_per_1k = {
            "gemini-2.0-flash": 0.0001,
            "gemini-2.0-flash-lite": 0.00005,
            "gemini-2.5-pro": 0.00125,
            "gemini-1.5-pro": 0.00125,
            "gemini-1.5-flash": 0.0001,
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.06,
            "gpt-4-turbo": 0.03,
            "gpt-4o": 0.015,
            "gpt-4o-mini": 0.00015,
        }
        rate = cost_per_1k.get(model, 0.0001)
        self._estimated_cost_usd += (tokens / 1000) * rate


# Singleton instance
model_router = ModelRouter()
